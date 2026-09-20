"""
装配工具

把一个已有的 .prt 按「位置 + 姿态」装配进一个装配体，并真正执行。

执行链路与其它工具一致：
    JSON 参数 → generate_assembly_journal() → .cs → run_journal.exe → .prt

注意：装配体可以"新建"（create_new=True，用 PartCollection.NewDisplay 建一个空
装配体），也可以"打开已有的"。未显式指定时，按目标文件是否已存在自动判断。
"""
from __future__ import annotations

import math
import os
import time

from backend.config import config
from backend.journal.generator import generate_assembly_journal
from backend.mcp.executor import execute_journal, failure_detail
from backend.mcp.registry import mcp_tool
from backend.mcp.response import ToolError, ToolResult


def rotation_z_matrix(degrees: float) -> list[float]:
    """绕 Z 轴旋转 degrees 度的 3x3 姿态矩阵，按 NX 的列序展开。

    返回 [Xx, Xy, Xz, Yx, Yy, Yz, Zx, Zy, Zz]，
    其中每三个数是一个轴向量（第 1 列 = 组件 X 轴，依此类推）。
    """
    rad = math.radians(degrees)
    c, s = math.cos(rad), math.sin(rad)
    # 数值清理：把 6.1e-17 这类浮点噪声压成 0，避免脏值进入 Journal
    def clean(v: float) -> float:
        return 0.0 if abs(v) < 1e-12 else v

    return [
        clean(c), clean(s), 0.0,    # 组件 X 轴
        clean(-s), clean(c), 0.0,   # 组件 Y 轴
        0.0, 0.0, 1.0,              # 组件 Z 轴
    ]


@mcp_tool(
    name="nx_add_component",
    description=(
        "将指定的 .prt 装配到一个装配体（可新建）中，支持指定插入位置和姿态。"
        "姿态用 3x3 旋转矩阵或 rotation_z_deg 简写指定。返回新 .prt 路径。"
    ),
    params={
        "part_path": {
            "type": "string",
            "description": "要装配的 .prt 绝对路径",
        },
        "assembly_path": {
            "type": "string",
            "description": "目标装配体 .prt 绝对路径；留空则自动生成到 output/models/",
            "required": False,
        },
        "position_x": {"type": "number", "description": "插入点 X（mm）", "default": 0.0, "required": False},
        "position_y": {"type": "number", "description": "插入点 Y（mm）", "default": 0.0, "required": False},
        "position_z": {"type": "number", "description": "插入点 Z（mm）", "default": 0.0, "required": False},
        "rotation_z_deg": {
            "type": "number",
            "description": "绕 Z 轴旋转角度（度）。提供后覆盖 orient_* 矩阵。",
            "required": False,
        },
        "orient_xx": {"type": "number", "description": "姿态矩阵 X 轴 X 分量", "default": 1.0, "required": False},
        "orient_xy": {"type": "number", "description": "姿态矩阵 X 轴 Y 分量", "default": 0.0, "required": False},
        "orient_xz": {"type": "number", "description": "姿态矩阵 X 轴 Z 分量", "default": 0.0, "required": False},
        "orient_yx": {"type": "number", "description": "姿态矩阵 Y 轴 X 分量", "default": 0.0, "required": False},
        "orient_yy": {"type": "number", "description": "姿态矩阵 Y 轴 Y 分量", "default": 1.0, "required": False},
        "orient_yz": {"type": "number", "description": "姿态矩阵 Y 轴 Z 分量", "default": 0.0, "required": False},
        "orient_zx": {"type": "number", "description": "姿态矩阵 Z 轴 X 分量", "default": 0.0, "required": False},
        "orient_zy": {"type": "number", "description": "姿态矩阵 Z 轴 Y 分量", "default": 0.0, "required": False},
        "orient_zz": {"type": "number", "description": "姿态矩阵 Z 轴 Z 分量", "default": 1.0, "required": False},
        "component_name": {
            "type": "string",
            "description": "组件名，默认 COMPONENT",
            "default": "COMPONENT",
            "required": False,
        },
        "reference_set": {
            "type": "string",
            "description": "参考集名，默认 MODEL（不存在时自动回退 Entire Part / 整个部件）",
            "default": "MODEL",
            "required": False,
        },
        "layer": {
            "type": "integer",
            "description": "图层：-1 沿用原部件图层（默认），0 当前工作图层，1-256 指定图层",
            "default": -1,
            "required": False,
        },
        "create_new": {
            "type": "boolean",
            "description": "True 新建空装配体；False 打开已有装配体；不传则按文件是否存在自动判断",
            "required": False,
        },
        "search_dirs": {
            "type": "string",
            "description": (
                "额外的部件搜索目录，多个用 ';' 分隔。被装配部件本身若是装配体，"
                "其子组件按引用方所在目录解析；对副本操作时可在这里补上原目录。"
            ),
            "required": False,
        },
    },
)
async def nx_add_component(
    part_path: str,
    assembly_path: str = "",
    position_x: float = 0.0,
    position_y: float = 0.0,
    position_z: float = 0.0,
    rotation_z_deg: float | None = None,
    orient_xx: float = 1.0, orient_xy: float = 0.0, orient_xz: float = 0.0,
    orient_yx: float = 0.0, orient_yy: float = 1.0, orient_yz: float = 0.0,
    orient_zx: float = 0.0, orient_zy: float = 0.0, orient_zz: float = 1.0,
    component_name: str = "COMPONENT",
    reference_set: str = "MODEL",
    layer: int = -1,
    create_new: bool | None = None,
    search_dirs: str = "",
) -> ToolResult:
    """把 part_path 装配到 assembly_path 指定的装配体中。

    位置为组件原点在世界坐标系中的位置；姿态为 3x3 旋转矩阵（NX 列序：每 3 个数一个轴向量）。
    rotation_z_deg 是"绕 Z 轴转多少度"的简写，给了它就忽略 orient_*。
    """
    # ── 1. 参数校验 ──
    part_path = os.path.abspath(part_path)
    if not os.path.isfile(part_path):
        return ToolError(
            "PART_NOT_FOUND",
            f"待装配的 .prt 不存在: {part_path}",
            "确认路径无误，并注意 NX 11 批处理对非 ASCII 路径支持有限",
        )

    if rotation_z_deg is not None:
        orientation = rotation_z_matrix(rotation_z_deg)
    else:
        orientation = [
            orient_xx, orient_xy, orient_xz,
            orient_yx, orient_yy, orient_yz,
            orient_zx, orient_zy, orient_zz,
        ]

    if not assembly_path:
        assembly_path = os.path.join(
            config.output_dir, "models",
            f"{time.strftime('%Y_%m_%d_%H_%M_%S')}_assembly.prt",
        )
    assembly_path = os.path.abspath(assembly_path)
    os.makedirs(os.path.dirname(assembly_path), exist_ok=True)

    # 未显式指定时：目标不存在 → 新建；存在 → 打开后追加
    if create_new is None:
        create_new = not os.path.exists(assembly_path)

    # 组件名默认取部件文件名（不含扩展名）
    if component_name == "COMPONENT":
        component_name = os.path.splitext(os.path.basename(part_path))[0]

    # ── 2. 生成 Journal ──
    report_path = os.path.splitext(assembly_path)[0] + "_report.txt"
    if os.path.exists(report_path):
        try:
            os.remove(report_path)
        except OSError:
            pass

    refsets = [reference_set] if reference_set else []
    for fallback in ("MODEL", "Entire Part", ""):
        if fallback not in refsets:
            refsets.append(fallback)

    params = {
        "assembly_path": assembly_path,
        "part_path": part_path,
        "position": [position_x, position_y, position_z],
        "orientation": orientation,
        "component_name": component_name,
        "reference_sets": refsets,
        "layer": layer,
        "create_new": create_new,
        "search_dirs": [d.strip() for d in search_dirs.split(";") if d.strip()],
        "report_path": report_path,
    }

    try:
        code = generate_assembly_journal(params)
    except Exception as exc:
        return ToolError("GENERATION_FAILED", f"装配 Journal 生成失败: {exc}")

    # ── 3. 执行 ──
    tag = os.path.splitext(os.path.basename(assembly_path))[0]
    result = execute_journal(code, tag=tag)

    report_lines: list[str] = []
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8", errors="ignore") as fh:
                report_lines = [ln.rstrip("\n") for ln in fh if ln.strip()]
        except OSError:
            pass

    unloaded = [ln[len("UNLOADED "):].strip() for ln in report_lines if ln.startswith("UNLOADED ")]

    data = {
        "assembly_path": assembly_path,
        "part_path": part_path,
        "component_name": component_name,
        "position": [position_x, position_y, position_z],
        "orientation": orientation,
        "create_new": create_new,
        "search_dirs": params["search_dirs"],
        "unloaded_sub_parts": unloaded,
        "journal_path": result.get("journal_path", ""),
        "report_path": report_path,
        "report": report_lines,
    }

    failed_in_report = any("FAILED" in ln for ln in report_lines)
    if not result["success"] or failed_in_report:
        detail = next((ln for ln in report_lines if "ERROR" in ln), "")
        return ToolError(
            "ASSEMBLY_FAILED",
            f"NX 装配执行失败: {detail or failure_detail(result)}",
            f"检查 Journal 日志: {result.get('journal_path', '')} 与 {report_path}",
        )

    if not os.path.exists(assembly_path):
        return ToolError(
            "ASSEMBLY_NOT_SAVED",
            f"Journal 返回成功但装配体文件不存在: {assembly_path}",
            f"查看日志: {report_path}",
        )

    message = (
        f"装配成功: {part_path} → {assembly_path}"
        f"（位置 ({position_x}, {position_y}, {position_z})）"
    )
    if unloaded:
        # 组件挂上了但子部件几何没加载出来，必须让用户知道
        # （只用 GBK 能编码的字符，避免中文控制台打印时抛 UnicodeEncodeError）
        message += f"；注意：有 {len(unloaded)} 个子部件未加载: {'; '.join(unloaded)}"

    return ToolResult.success(data=data, message=message)
