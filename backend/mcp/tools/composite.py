"""
组合工具：复制副本 → 改参数 → 装配

nx_assemble_and_update 的流程：
  0. 把 part_path 复制一份到 output/models/（母版从此不再被碰）
  1. 在副本上更新表达式并保存
  2. 把副本作为组件装配到 assembly_path 的指定位置和姿态

为什么默认先复制：
  改表达式必须原地保存才能被装配读取，如果直接对原部件操作，等于把标准件母版
  改掉了手里。复制副本后所有写操作都落在 output/ 里，母版永远是干净的。

为什么拆成两次 NX 调用而不是写一个 Journal：
  改表达式要求"部件已保存"，而装配时 NX 又要重新加载该部件。分两步走，每一步
  都是一个干净的 NX 会话，语义清楚，也不会出现"改参失败但已经装配进去"的半成品。
"""
from __future__ import annotations

import os
import shutil
import time

from backend.config import config
from backend.mcp.executor import generate_output_path
from backend.mcp.registry import mcp_tool
from backend.mcp.response import ToolError, ToolResult
from backend.mcp.tools.assembly import nx_add_component
from backend.mcp.tools.expressions import nx_update_expressions, parse_expressions
from backend.mcp.tools.flatten import nx_assemble_to_model


def _is_inside(path: str, root: str) -> bool:
    """path 是否位于 root 之内（两者都已 abspath）。跨盘符时返回 False。"""
    try:
        return os.path.commonpath([os.path.abspath(path), os.path.abspath(root)]) == os.path.abspath(root)
    except ValueError:
        return False


def _cleanup_descendant_parts(candidates: list[str], keep_paths: list[str],
                              allowed_root: str) -> tuple[list[str], list[str]]:
    """删除拍平之后已经没人引用的派生 .prt。

    只删同时满足这些条件的文件，宁可漏删也绝不误删：
      - 是本次调用派生出来的（工作副本 / 为解析组件而复制的兄弟部件）
      - 位于允许的根目录（output/）之内 —— 输出目录之外的任何文件一律不碰
      - 不是最终交付物，也不是母版
      - 确实是存在的 .prt 文件

    为什么需要它：拍平把几何全部吸收进成品之后，工作副本和那些为了解析子组件
    而复制过来的兄弟 .prt 就成了孤儿；留着它们，output/ 里会有一堆看起来像
    交付物的中间文件。

    Returns:
        (已删除, 因越界而保留)
    """
    removed: list[str] = []
    skipped: list[str] = []
    keep = {os.path.abspath(p) for p in keep_paths if p}

    for path in candidates:
        if not path:
            continue
        ap = os.path.abspath(path)
        if ap in keep or not ap.lower().endswith(".prt") or not os.path.isfile(ap):
            continue
        if not _is_inside(ap, allowed_root):
            # 安全闸：只清理输出目录自己的东西
            skipped.append(ap)
            continue
        try:
            os.remove(ap)
            removed.append(ap)
        except OSError:
            skipped.append(ap)

    return removed, skipped


def _resolve_copy_target(source_part: str, copy_to: str) -> str:
    """算出副本的落盘路径。

    copy_to 留空  → output/models/<时间戳>_<原名>_copy_<随机>.prt
    copy_to 是目录 → 该目录下 <原名>_<时间戳>.prt
    copy_to 是文件 → 直接用这个路径
    """
    stem = os.path.splitext(os.path.basename(source_part))[0]

    if not copy_to:
        _, generated = generate_output_path(extension=".prt", tag=f"{stem}_copy")
        return generated

    target = os.path.abspath(copy_to)
    # 没有扩展名的路径基本可以断定是目录（调用方想"复制到某个位置"），
    # 这样目标目录还不存在时也不会被误当成文件名。
    looks_like_dir = (
        copy_to.endswith(("/", "\\"))
        or os.path.isdir(target)
        or os.path.splitext(target)[1] == ""
    )
    if looks_like_dir:
        return os.path.join(target, f"{stem}_{time.strftime('%Y_%m_%d_%H_%M_%S')}.prt")
    return target


# 同目录部件超过这个数量时，不再整目录复制，改为只挑源部件里确实引用到的
_SIBLING_COPY_CAP = 50


def _sibling_parts_to_copy(source_part: str) -> tuple[list[str], str]:
    """找出必须跟副本放在一起的"兄弟部件"文件名。

    为什么需要：被装配的部件本身可能是个装配体，它的子组件（螺钉、压板…）
    NX 是按"引用方所在目录"去解析的。只把 .prt 本身复制走、把同目录的兄弟部件
    落下，装配出来的组件树看着是全的，但子组件几何加载不出来（refset 变成 Empty）。
    把兄弟部件一起复制，副本才是自洽的。

    返回 (文件名列表, 模式)，模式用于日志说明：
      "none"       没有兄弟部件
      "all"        整目录复制（部件数量不大，最稳）
      "referenced" 目录里部件太多，只挑源部件二进制里出现过的
      "unreadable" 读不了源部件，放弃复制
    """
    src_dir = os.path.dirname(source_part)
    source_name = os.path.basename(source_part).lower()
    try:
        siblings = sorted(
            name for name in os.listdir(src_dir)
            if name.lower().endswith(".prt") and name.lower() != source_name
        )
    except OSError:
        return [], "unreadable"

    if not siblings:
        return [], "none"
    if len(siblings) <= _SIBLING_COPY_CAP:
        return siblings, "all"

    try:
        with open(source_part, "rb") as fh:
            blob = fh.read()
    except OSError:
        return [], "unreadable"

    referenced = [
        name for name in siblings
        if name.encode("ascii", "ignore") in blob
        or os.path.splitext(name)[0].encode("ascii", "ignore") in blob
    ]
    return referenced, "referenced"


@mcp_tool(
    name="nx_assemble_and_update",
    description=(
        "把带参 PRT 复制一份副本到 output/，在副本上更新表达式参数，再把副本装配到"
        "装配体（可新建）的指定位置和姿态。原部件不会被修改。"
        "先改参并保存，再装配；改参失败则不会装配。"
    ),
    params={
        "part_path": {
            "type": "string",
            "description": "带参 .prt 的绝对路径（只读，不会被修改）",
        },
        "expressions_json": {
            "type": "string",
            "description": (
                'JSON 数组，如 \'[{"name":"d1","value":100.0},{"name":"d2","value":50.0}]\'；'
                "留空则只装配、不改参数"
            ),
            "required": False,
        },
        "assembly_path": {
            "type": "string",
            "description": "目标装配体 .prt 路径；留空则自动生成到 output/models/",
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
            "description": "组件名，默认取原部件文件名（不含副本后缀）",
            "required": False,
        },
        "reference_set": {
            "type": "string",
            "description": "参考集名，默认 MODEL（不存在时自动回退）",
            "default": "MODEL",
            "required": False,
        },
        "create_new": {
            "type": "boolean",
            "description": "True 新建空装配体；False 打开已有装配体；不传则按文件是否存在自动判断",
            "required": False,
        },
        "copy_before_update": {
            "type": "boolean",
            "description": "是否先复制副本（默认 True，母版不被修改）。设为 False 会直接改原部件。",
            "default": True,
            "required": False,
        },
        "copy_to": {
            "type": "string",
            "description": "副本落盘位置：目录则放进去，文件路径则直接用；留空自动生成到 output/models/",
            "required": False,
        },
        "flatten_assembly": {
            "type": "boolean",
            "description": (
                "是否彻底拍平（默认 True）。开启时分两步：改参后先把副本拍平成单一部件"
                "（子部件几何合并进根部件），装配完成后再把装配体本身拍平，"
                "最终交付物是一个「装着全部几何、零组件」的 .prt，不再残留任何装配关系。"
                "设 False 则保留原始装配树。"
            ),
            "default": True,
            "required": False,
        },
        "cleanup_descendants": {
            "type": "boolean",
            "description": (
                "彻底拍平之后，是否删除已经没人引用的派生子孙 .prt（工作副本 + 为解析子组件"
                "而复制的兄弟部件）。默认 True。只删本次生成、位于 output/ 之内、"
                "且不再被成品引用的文件；母版与最终交付物永不删除。"
            ),
            "default": True,
            "required": False,
        },
    },
)
async def nx_assemble_and_update(
    part_path: str,
    expressions_json: str = "",
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
    create_new: bool | None = None,
    copy_before_update: bool = True,
    copy_to: str = "",
    flatten_assembly: bool = True,
    cleanup_descendants: bool = True,
) -> ToolResult:
    """复制副本 → 改参 → 拍平 → 装配。

    默认会把 part_path 复制一份到 output/models/，之后所有写操作都在副本上进行，
    part_path 指向的原始部件不会被修改。要直接改原部件，显式传 copy_before_update=False。
    """
    # ── 0a. 校验原部件 ──
    source_part = os.path.abspath(part_path)
    if not os.path.isfile(source_part):
        return ToolError(
            "PART_NOT_FOUND",
            f"部件不存在: {source_part}",
            "确认路径无误，并注意 NX 11 批处理对非 ASCII 路径支持有限",
        )

    # ── 0b. 复制副本（默认行为） ──
    siblings_copied: list[str] = []
    sibling_mode = "none"
    if copy_before_update:
        working_part = _resolve_copy_target(source_part, copy_to)
        if os.path.abspath(working_part) == source_part:
            return ToolError(
                "COPY_TARGET_IS_SOURCE",
                f"副本路径与原部件相同，会覆盖母版: {source_part}",
                "把 copy_to 指到 output/ 下的另一个路径",
            )
        config.ensure_dirs()
        work_dir = os.path.dirname(working_part)
        try:
            os.makedirs(work_dir, exist_ok=True)
            shutil.copy2(source_part, working_part)
        except OSError as exc:
            return ToolError(
                "COPY_FAILED",
                f"复制副本失败: {exc}",
                f"检查目标目录是否可写: {work_dir}",
            )

        # 兄弟部件一起复制，否则副本里的子组件解析不到（几何缺失）
        if work_dir != os.path.dirname(source_part):
            names, sibling_mode = _sibling_parts_to_copy(source_part)
            src_dir = os.path.dirname(source_part)
            for name in names:
                try:
                    shutil.copy2(os.path.join(src_dir, name), os.path.join(work_dir, name))
                    siblings_copied.append(name)
                except OSError:
                    pass
    else:
        working_part = source_part

    # 组件名默认取"原部件"文件名，避免带上副本的时间戳后缀
    if component_name == "COMPONENT":
        component_name = os.path.splitext(os.path.basename(source_part))[0]

    expression_result: dict | None = None

    # ── 1. 在副本上改参数（失败就不装配） ──
    if expressions_json and expressions_json.strip():
        try:
            parse_expressions(expressions_json)
        except Exception as exc:
            return ToolError(
                "BAD_EXPRESSIONS",
                f"表达式参数无法解析: {exc}",
                '正确格式: \'[{"name":"d1","value":100.0}]\'',
            )

        update = await nx_update_expressions(
            part_path=working_part,
            expressions_json=expressions_json,
        )
        if isinstance(update, ToolError):
            if copy_before_update:
                # 副本已生成但没改成功，说清楚，免得用户去找不着
                return ToolError(
                    update.error_code,
                    f"{update.message}（副本已生成但未改动: {working_part}）",
                    update.suggestion,
                )
            return update
        expression_result = update.data

    # ── 2. 拍平副本：把子部件几何合并进根部件（放在改参之后、装配之前） ──
    # 被装配的部件本身可能是个装配体，它的子组件（螺钉、压板…）是按"引用方所在目录"
    # 解析的；现在我们操作的是副本，不补上原目录的话那些子组件会加载不出来（几何缺失）。
    search_dirs = os.path.dirname(source_part)
    if copy_before_update and os.path.dirname(working_part) != search_dirs:
        search_dirs = f"{search_dirs};{os.path.dirname(working_part)}"

    flatten_result: dict | None = None
    if flatten_assembly:
        flat = await nx_assemble_to_model(
            part_path=working_part,
            search_dirs=search_dirs,
        )
        if isinstance(flat, ToolError):
            # 副本可能已经被改参了，要说清楚，避免用户以为什么都没发生
            notes = []
            if expression_result is not None:
                notes.append("表达式已改并保存")
            if copy_before_update:
                notes.append(f"副本已生成: {working_part}")
            suffix = f"（{'; '.join(notes)}）" if notes else ""
            return ToolError(flat.error_code, f"{flat.message}{suffix}", flat.suggestion)
        flatten_result = flat.data

    # ── 3. 装配副本 ──
    result = await nx_add_component(
        part_path=working_part,
        assembly_path=assembly_path,
        position_x=position_x,
        position_y=position_y,
        position_z=position_z,
        rotation_z_deg=rotation_z_deg,
        orient_xx=orient_xx, orient_xy=orient_xy, orient_xz=orient_xz,
        orient_yx=orient_yx, orient_yy=orient_yy, orient_yz=orient_yz,
        orient_zx=orient_zx, orient_zy=orient_zy, orient_zz=orient_zz,
        component_name=component_name,
        reference_set=reference_set,
        create_new=create_new,
        search_dirs=search_dirs,
    )
    if isinstance(result, ToolError):
        # 参数已经改到副本上了，要说清楚，避免用户以为什么都没发生
        if expression_result is not None:
            return ToolError(
                result.error_code,
                f"{result.message}（注意：副本 {os.path.basename(working_part)} 的表达式已改并保存）",
                result.suggestion,
            )
        return result

    # ── 4. 拍平装配体：把刚装进去的组件也合并进装配体根部件 ──
    # 上一步拍平只让"组件自己"变成单文件；装配体 → 组件这条装配关系还在。
    # 这里再把装配体本身拍平，交付物才是"一个 prt 装下所有几何、零组件"。
    assembly_flat: dict | None = None
    if flatten_assembly:
        final_part = result.data.get("assembly_path", "") or assembly_path
        if final_part and os.path.exists(final_part):
            flat2 = await nx_assemble_to_model(
                part_path=final_part,
                search_dirs=search_dirs,
            )
            if isinstance(flat2, ToolError):
                return ToolError(
                    flat2.error_code,
                    f"{flat2.message}（注意：装配体 {final_part} 已生成，"
                    "但仍保持「父装配体 + 组件」的结构，尚未合并为单一部件）",
                    flat2.suggestion,
                )
            assembly_flat = flat2.data

    # ── 5. 清理派生的子孙 .prt ──
    # 成品已经是零组件的单一部件，几何全部吸收进去了；工作副本和那些为了解析
    # 子组件而复制过来的兄弟 .prt 从此没有任何引用，留着只是脏。
    # 只在"确实拍平到零组件"时才清理——万一拍平没做成，那些文件还是被依赖的。
    cleanup: dict | None = None
    final_part = result.data.get("assembly_path", "") or assembly_path
    if (cleanup_descendants and assembly_flat is not None
            and assembly_flat.get("components_after") == 0):
        candidates: list[str] = []
        if copy_before_update:
            # copy_before_update=False 时 working_part 就是母版，绝不能删
            candidates.append(working_part)
        work_dir = os.path.dirname(working_part)
        candidates += [os.path.join(work_dir, name) for name in siblings_copied]

        removed, skipped = _cleanup_descendant_parts(
            candidates,
            keep_paths=[final_part, source_part],
            allowed_root=config.output_dir,
        )
        cleanup = {
            "removed": removed,
            "skipped_outside_output": skipped,
            "kept_working_part": not copy_before_update,
        }

    changes = (expression_result or {}).get("changes", [])
    data = dict(result.data)
    data["source_part_path"] = source_part
    data["working_part_path"] = working_part
    data["copy_created"] = bool(copy_before_update)
    data["sibling_parts_copied"] = siblings_copied
    data["sibling_copy_mode"] = sibling_mode
    data["expressions"] = expression_result
    data["flatten"] = flatten_result
    data["flatten_assembly"] = assembly_flat
    data["cleanup"] = cleanup

    if expression_result is None:
        action = "装配成功（未改参数）"
    else:
        action = f"改参并装配成功: {len(changes)} 个参数"

    if flatten_result is not None:
        if flatten_result.get("already_flat"):
            action += "，副本本就是平件无需拍平"
        else:
            action += (
                f"，副本已拍平（合并 {len(flatten_result.get('imported', []))} 个子部件、"
                f"移除 {len(flatten_result.get('removed', []))} 个组件）"
            )

    if assembly_flat is not None:
        if assembly_flat.get("already_flat"):
            action += "，装配体本就是平件"
        else:
            action += (
                f"，装配体已拍平为单一部件（合并 {len(assembly_flat.get('imported', []))} 个组件、"
                f"实体 {assembly_flat.get('bodies_before')} → {assembly_flat.get('bodies_after')}）"
            )

    if cleanup is not None:
        n_removed = len(cleanup["removed"])
        if n_removed:
            action += f"，已清理 {n_removed} 个拍平后不再引用的子孙 .prt"

    if copy_before_update:
        message = (
            f"{action}；母版未改动。成品 {data['assembly_path']}"
        )
        if cleanup is not None and cleanup["removed"]:
            message += f"（中间副本已删除: {os.path.basename(working_part)} 等）"
    else:
        message = f"{action}（直接改动了原部件）→ {data['assembly_path']}"

    return ToolResult.success(data=data, message=message)
