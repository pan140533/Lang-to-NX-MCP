"""
表达式工具

更新一个已有 .prt 里的表达式值（带参部件改参）。

执行链路与其它工具一致：
    JSON 参数 → generate_expression_journal() → .cs → run_journal.exe → .prt

语义是「全有或全无」：只要有一个表达式没改成功（名字不存在，或被锁定），
Journal 就不保存，避免部件被改成"半套参数"的状态。
"""
from __future__ import annotations

import json
import os
import re

from backend.config import config
from backend.journal.generator import generate_expression_journal
from backend.mcp.executor import execute_journal, failure_detail
from backend.mcp.registry import mcp_tool
from backend.mcp.response import ToolError, ToolResult


def parse_expressions(expressions_json) -> list[dict]:
    """把输入解析成 [{"name": ..., "value": ...}]。

    兼容三种写法：
      - JSON 数组字符串 '[{"name":"d1","value":100},{"name":"d2","value":50}]'
      - JSON 对象字符串 '{"d1":100,"d2":50}'
      - 已经是 list / dict 的 Python 对象
    """
    data = expressions_json
    if isinstance(data, str):
        if not data.strip():
            raise ValueError("expressions_json 不能为空")
        data = json.loads(data)

    if isinstance(data, dict):
        items = [{"name": str(k), "value": v} for k, v in data.items()]
    elif isinstance(data, list):
        items = []
        for i, entry in enumerate(data, start=1):
            if not isinstance(entry, dict):
                raise ValueError(f"第 {i} 项不是对象: {entry!r}")
            if "name" not in entry:
                raise ValueError(f"第 {i} 项缺少 name 字段: {entry!r}")
            if "value" not in entry:
                raise ValueError(f"第 {i} 项缺少 value 字段: {entry!r}")
            items.append({"name": str(entry["name"]), "value": entry["value"]})
    else:
        raise ValueError(f"无法解析表达式列表: {type(data).__name__}")

    if not items:
        raise ValueError("表达式列表为空")
    return items


_EXPR_OK_RE = re.compile(r"^EXPR_OK (\S+) \[(.*)\] -> \[(.*)\]$")


def parse_report(lines: list[str]) -> dict:
    """从 Journal 日志里还原改动明细。"""
    changes = []
    missing = []
    errors = []
    update_errors = []
    update_failures = []
    for line in lines:
        m = _EXPR_OK_RE.match(line)
        if m:
            changes.append({"name": m.group(1), "old": m.group(2), "new": m.group(3)})
        elif line.startswith("EXPR_MISSING "):
            missing.append(line[len("EXPR_MISSING "):].strip())
        elif line.startswith("EXPR_ERR "):
            errors.append(line[len("EXPR_ERR "):].strip())
        elif line.startswith("UPDATE_ERR "):
            update_errors.append(line[len("UPDATE_ERR "):].strip())
        elif line.startswith("UPDATE_FAIL "):
            update_failures.append(line[len("UPDATE_FAIL "):].strip())
    return {
        "changes": changes,
        "missing": missing,
        "errors": errors,
        "update_errors": update_errors,
        "update_failures": update_failures,
    }


@mcp_tool(
    name="nx_update_expressions",
    description=(
        "更新指定 PRT 文件中的表达式值，支持批量更新多个表达式。"
        "默认原地保存（会覆盖原文件）；传 output_path 则另存为新文件、不改原部件。"
        "value 可以是数字，也可以是公式字符串（如 \"d1*2\"）。"
        "只要有一个表达式没改成功就整体不保存。"
    ),
    params={
        "part_path": {
            "type": "string",
            "description": "要修改的 .prt 绝对路径",
        },
        "expressions_json": {
            "type": "string",
            "description": (
                'JSON 数组，如 \'[{"name":"d1","value":100.0},{"name":"d2","value":50.0}]\'；'
                '也接受 \'{"d1":100,"d2":50}\' 这种对象写法。'
            ),
        },
        "output_path": {
            "type": "string",
            "description": "可选。给了就另存为该路径（原部件不动）；留空则原地保存。",
            "required": False,
        },
    },
)
async def nx_update_expressions(
    part_path: str,
    expressions_json: str,
    output_path: str = "",
) -> ToolResult:
    """更新 part_path 中指定表达式的值。

    value 建议用浮点数；代码会用 InvariantCulture 转成字符串，避免区域设置差异。
    返回每个表达式改动前后的值。
    """
    # ── 1. 参数校验 ──
    part_path = os.path.abspath(part_path)
    if not os.path.isfile(part_path):
        return ToolError(
            "PART_NOT_FOUND",
            f"部件不存在: {part_path}",
            "确认路径无误，并注意 NX 11 批处理对非 ASCII 路径支持有限",
        )

    try:
        expressions = parse_expressions(expressions_json)
    except (ValueError, json.JSONDecodeError) as exc:
        return ToolError(
            "BAD_EXPRESSIONS",
            f"表达式参数无法解析: {exc}",
            '正确格式: \'[{"name":"d1","value":100.0}]\'',
        )

    if output_path:
        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # ── 2. 生成 Journal ──
    # 报告名以部件名为主，不再叠一层时间戳：副本名本身已经带时间戳了，
    # 再叠就会变成 2026_..._expr_2026_..._报告.txt 这种又长又难认的名字。
    # execute_journal 自己会给 .cs 加时间戳，tag 这里不需要。
    config.ensure_dirs()
    stem = os.path.splitext(os.path.basename(part_path))[0][:60]
    tag = f"expr_{stem}"
    report_path = os.path.join(config.output_dir, "models", f"{stem}_expr_report.txt")
    if os.path.exists(report_path):
        try:
            os.remove(report_path)
        except OSError:
            pass

    try:
        code = generate_expression_journal({
            "part_path": part_path,
            "expressions": expressions,
            "output_path": output_path,
            "report_path": report_path,
        })
    except Exception as exc:
        return ToolError("GENERATION_FAILED", f"表达式 Journal 生成失败: {exc}")

    # ── 3. 执行 ──
    result = execute_journal(code, tag=tag)

    report_lines: list[str] = []
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8", errors="ignore") as fh:
                report_lines = [ln.rstrip("\n") for ln in fh if ln.strip()]
        except OSError:
            pass

    detail = parse_report(report_lines)
    target = output_path or part_path

    data = {
        "part_path": part_path,
        "output_path": output_path,
        "saved_to": target,
        "requested": expressions,
        "changes": detail["changes"],
        "missing": detail["missing"],
        "errors": detail["errors"],
        "update_errors": detail["update_errors"],
        "update_failures": detail["update_failures"],
        "journal_path": result.get("journal_path", ""),
        "report_path": report_path,
        "report": report_lines,
    }

    failed_in_report = any("FAILED" in ln for ln in report_lines)
    if not result["success"] or failed_in_report:
        if detail["missing"]:
            problem = f"表达式不存在: {', '.join(detail['missing'])}"
        elif detail["errors"]:
            problem = f"表达式修改被拒绝: {'; '.join(detail['errors'])}"
        elif detail["update_errors"]:
            # 值改下去了，但模型重建失败 —— 把这组参数对该部件不成立
            problem = (
                f"模型重建失败，已回滚且未保存（这组参数对该部件不成立）: "
                f"{'; '.join(detail['update_errors'])}"
            )
            if detail["update_failures"]:
                problem += f" | 失败对象: {'; '.join(detail['update_failures'])}"
        else:
            problem = failure_detail(result)
        return ToolError(
            "EXPRESSION_UPDATE_FAILED",
            f"表达式更新失败（未保存）: {problem or '未知原因'}",
            f"查看 Journal 日志: {result.get('journal_path', '')} 与 {report_path}",
        )

    if not os.path.exists(target):
        return ToolError(
            "EXPRESSION_NOT_SAVED",
            f"Journal 返回成功但文件不存在: {target}",
            f"查看日志: {report_path}",
        )

    return ToolResult.success(
        data=data,
        message=(
            f"表达式更新成功: {len(detail['changes'])} 个 → {target}"
            f"（{', '.join(c['name'] for c in detail['changes'])}）"
        ),
    )
