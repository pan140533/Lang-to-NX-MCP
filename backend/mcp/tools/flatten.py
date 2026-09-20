"""
拍平工具

把一个装配体 .prt 变成「单一部件」：所有子部件的几何被搬进根部件、装配树清空，
结果仍然只有一个 .prt。

执行链路与其它工具一致：
    JSON 参数 → generate_flatten_journal() → .cs → run_journal.exe → .prt

为什么需要它：装配交付物往往还要被下游（出图、仿真、CAM、再次装配）消费，
多层 .prt 组成的装配树会带来「子件找不到 / 几何缺失」的麻烦。拍平之后是一个
自洽的单文件，几何全部就地实化，不再依赖任何兄弟部件。

实现要点见 backend/journal/generator.py 的拍平模板注释。
"""
from __future__ import annotations

import os
import re

from backend.config import config
from backend.journal.generator import generate_flatten_journal
from backend.mcp.executor import execute_journal, failure_detail
from backend.mcp.registry import mcp_tool
from backend.mcp.response import ToolError, ToolResult

_IMPORTED_RE = re.compile(r"^IMPORTED (?P<path>.*?)(?: at (?P<pos>.*))?$")


def parse_flatten_report(lines: list[str]) -> dict:
    """从 Journal 日志里还原拍平明细。"""
    imported: list[dict] = []
    removed: list[str] = []
    unresolved: list[str] = []
    nested: list[str] = []
    numbers: dict[str, int] = {}
    saved_to = ""

    for line in lines:
        m = _IMPORTED_RE.match(line)
        if m:
            imported.append({"part": m.group("path"), "position": m.group("pos") or ""})
        elif line.startswith("REMOVED "):
            removed.append(line[len("REMOVED "):].strip())
        elif line.startswith("UNRESOLVED "):
            unresolved.append(line[len("UNRESOLVED "):].split(" (")[0].strip())
        elif line.startswith("NESTED_SUBASSEMBLY "):
            nested.append(line[len("NESTED_SUBASSEMBLY "):].strip())
        elif line.startswith("SAVED_AS "):
            saved_to = line[len("SAVED_AS "):].split(" unsaved_parts=")[0].strip()
        elif line.startswith("SAVED "):
            saved_to = line[len("SAVED "):].split(" unsaved_parts=")[0].strip()
        else:
            for key in ("BODIES_BEFORE", "BODIES_AFTER",
                        "TOP_COMPONENTS", "TOP_COMPONENTS_AFTER"):
                if line.startswith(key + " "):
                    try:
                        numbers[key] = int(line[len(key) + 1:].strip())
                    except ValueError:
                        pass

    return {
        "imported": imported,
        "removed": removed,
        "unresolved": unresolved,
        "nested_subassemblies": nested,
        "saved_to": saved_to,
        "already_flat": any(ln.startswith("NO_COMPONENTS") for ln in lines),
        **{k.lower(): v for k, v in numbers.items()},
    }


@mcp_tool(
    name="nx_assemble_to_model",
    description=(
        "把装配体拍平成单一部件：把每个子部件的几何按其在装配中的位姿导入根部件，"
        "然后移除全部组件。输出仍是一个 .prt，但不再有装配树、不再依赖其它 .prt。"
        "默认原地保存（覆盖原文件）；传 output_path 则另存为新文件。"
        "本来就是平件（无组件）时是安全的空操作。"
        "限制：组件的部件如果自己也是装配体，NX 的「导入部件」无法合并它"
        "——需要自底向上逐个拍平（nx_assemble_and_update 会自动按这个顺序做）。"
        "任何一步不成立都整体不保存，绝不会留下缺失几何的半成品。"
    ),
    params={
        "part_path": {
            "type": "string",
            "description": "要拍平的装配体 .prt 绝对路径",
        },
        "output_path": {
            "type": "string",
            "description": "可选。给了就另存为该路径（原部件不被覆盖）；留空则原地保存。",
            "required": False,
        },
        "search_dirs": {
            "type": "string",
            "description": "额外的部件搜索目录，多个用 ';' 分隔（副本场景下补上原子件所在目录）。",
            "required": False,
        },
    },
)
async def nx_assemble_to_model(
    part_path: str,
    output_path: str = "",
    search_dirs: str = "",
) -> ToolResult:
    """把 part_path 指向的装配体拍平成一个不再含组件的部件。"""
    # ── 1. 参数校验 ──
    part_path = os.path.abspath(part_path)
    if not os.path.isfile(part_path):
        return ToolError(
            "PART_NOT_FOUND",
            f"部件不存在: {part_path}",
            "确认路径无误，并注意 NX 11 批处理对非 ASCII 路径支持有限",
        )

    if output_path:
        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # ── 2. 生成 Journal ──
    config.ensure_dirs()
    stem = os.path.splitext(os.path.basename(part_path))[0][:60]
    tag = f"flatten_{stem}"
    report_path = os.path.join(config.output_dir, "models", f"{stem}_flatten_report.txt")
    if os.path.exists(report_path):
        try:
            os.remove(report_path)
        except OSError:
            pass

    try:
        code = generate_flatten_journal({
            "part_path": part_path,
            "output_path": output_path,
            "search_dirs": [d.strip() for d in search_dirs.split(";") if d.strip()],
            "report_path": report_path,
        })
    except Exception as exc:
        return ToolError("GENERATION_FAILED", f"拍平 Journal 生成失败: {exc}")

    # ── 3. 执行 ──
    result = execute_journal(code, tag=tag)

    report_lines: list[str] = []
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8", errors="ignore") as fh:
                report_lines = [ln.rstrip("\n") for ln in fh if ln.strip()]
        except OSError:
            pass

    detail = parse_flatten_report(report_lines)
    target = output_path or part_path

    data = {
        "part_path": part_path,
        "output_path": output_path,
        "saved_to": target,
        "already_flat": detail["already_flat"],
        "bodies_before": detail.get("bodies_before"),
        "bodies_after": detail.get("bodies_after"),
        "components_before": detail.get("top_components"),
        "components_after": detail.get("top_components_after"),
        "imported": detail["imported"],
        "removed": detail["removed"],
        "unresolved": detail["unresolved"],
        "nested_subassemblies": detail["nested_subassemblies"],
        "journal_path": result.get("journal_path", ""),
        "report_path": report_path,
        "report": report_lines,
    }

    failed_in_report = any(ln == "FAILED" for ln in report_lines)
    if not result["success"] or failed_in_report:
        if detail["unresolved"]:
            problem = (
                f"{len(detail['unresolved'])} 个组件的部件没加载出来，无法导入几何"
                f"（已放弃，未删除任何组件、未保存）: {'; '.join(detail['unresolved'])}"
                "。把这些部件所在目录用 search_dirs 传进来"
            )
        elif detail["nested_subassemblies"] and any(
                ln.startswith("IMPORT_ERR ") for ln in report_lines):
            problem = (
                "组件 " + "; ".join(detail["nested_subassemblies"]) + " 自己也是装配体。"
                "NX 的「导入部件」无法把一个已加载、且自身含组件的部件合并进来"
                "（报 Update undo happened）。请先对每个子装配体单独调用 "
                "nx_assemble_to_model 拍平，再拍平本部件；"
                "或直接用 nx_assemble_and_update —— 它会自底向上按正确顺序分步拍平"
            )
        else:
            problem = next((ln for ln in report_lines if ln.startswith("IMPORT_ERR ")
                            or ln.startswith("SAVE_ERR ")
                            or ln.startswith("REMOVE_ERR ")), "") or failure_detail(result)
        return ToolError(
            "FLATTEN_FAILED",
            f"装配拍平失败（未保存）: {problem}",
            f"查看 Journal 日志: {result.get('journal_path', '')} 与 {report_path}",
        )

    if not os.path.exists(target):
        return ToolError(
            "FLATTEN_NOT_SAVED",
            f"Journal 返回成功但文件不存在: {target}",
            f"查看日志: {report_path}",
        )

    if detail["already_flat"]:
        message = f"部件本来就没有组件，无需拍平: {target}"
    else:
        message = (
            f"拍平成功: 合并 {len(detail['imported'])} 个子部件、移除 "
            f"{len(detail['removed'])} 个组件，实体 {detail.get('bodies_before')} → "
            f"{detail.get('bodies_after')} → {target}"
        )

    return ToolResult.success(data=data, message=message)
