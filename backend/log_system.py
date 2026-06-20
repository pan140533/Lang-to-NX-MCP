"""操作日志系统

每次建模操作都记录日志，同时输出两份：
  1. JSON Lines（.jsonl）— 供程序读取、AI 分析
  2. 纯文本（.log）— 人可直接阅读的详细记录

目录结构：
    logs/
        YYYY-MM-DD/
            operations.jsonl    # 操作流水（机器可读）
            tasks.jsonl         # 任务级日志（机器可读）
            detailed.log        # 人可读的详细日志
            scripts/            # 生成的脚本原文
"""

import json
import os
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).parent.parent.resolve()
LOG_ROOT = BASE_DIR / "logs"


def _today_dir() -> Path:
    """按日期分目录: logs/2026-06-11/"""
    d = LOG_ROOT / datetime.now().strftime("%Y-%m-%d")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _append_jsonl(path: Path, record: dict) -> None:
    """追加一行 JSON 到日志文件"""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _append_text(text: str) -> None:
    """追加一行文本到详细日志文件"""
    try:
        path = _today_dir() / "detailed.log"
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception:
        pass


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _ts_ms() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.") + f"{datetime.now().microsecond // 1000:03d}"


def _record(task_id: str, log_type: str, data: dict) -> dict:
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "task_id": task_id,
        "type": log_type,
        "data": data,
    }


# ═══════════════════════════════════════════════════════════════
#  人可读的详细日志
# ═══════════════════════════════════════════════════════════════

def log_detailed(
    task_id: str,
    module: str,
    operation: str,
    status: str = "",
    message: str = "",
    params: dict = None,
    error: str = "",
    trace: str = "",
    fix_attempt: str = "",
    fix_result: str = "",
):
    """写入一条人可读的详细日志。"""
    lines = []
    lines.append(f"[{_ts()}] [任务 {task_id[:8]}] [{module}] [{operation}]")
    if message:
        lines.append(f"  描述: {message}")
    if params:
        params_str = json.dumps(params, ensure_ascii=False)
        if len(params_str) > 200:
            params_str = params_str[:200] + "..."
        lines.append(f"  参数: {params_str}")
    if error:
        lines.append(f"  ❌ 异常: {error}")
        if trace:
            trace_lines = trace.strip().split("\n")
            short_trace = "\n".join(trace_lines[-5:])
            lines.append(f"  堆栈:\n{short_trace}")
    if fix_attempt:
        lines.append(f"  🔧 修复: {fix_attempt}")
    if fix_result:
        icon = "✅" if "完成" in fix_result or "成功" in fix_result else "❌"
        lines.append(f"  {icon} 修复结果: {fix_result}")

    _append_text("\n".join(lines))
    _append_text("")


# ═══════════════════════════════════════════════════════════════
#  原 JSON Lines 日志
# ═══════════════════════════════════════════════════════════════

def log_task_start(task_id: str, prompt: str) -> None:
    record = _record(task_id, "task_start", {"prompt": prompt, "time": time.time()})
    _append_jsonl(_today_dir() / "tasks.jsonl", record)
    log_detailed(task_id, "system", "建模任务", "start",
                 message=f"用户输入: {prompt}")


def log_task_end(task_id: str, status: str, message: str = "",
                 model_path: str = "", duration_s: float = 0) -> None:
    record = _record(task_id, "task_end", {
        "status": status, "message": message,
        "model_path": model_path, "duration_s": round(duration_s, 2),
    })
    _append_jsonl(_today_dir() / "tasks.jsonl", record)
    s = "成功" if status == "completed" else "失败"
    model_info = f"，模型: {model_path}" if model_path else ""
    log_detailed(task_id, "system", "建模任务", status,
                 message=f"任务{s}{model_info} (耗时 {duration_s:.1f}s)")


def log_operation(task_id: str, operation: str, params: dict,
                  result: str, error: str = "", duration_ms: float = 0) -> None:
    record = _record(task_id, "operation", {
        "operation": operation, "params": params,
        "result": result, "error": error, "duration_ms": round(duration_ms, 1),
    })
    _append_jsonl(_today_dir() / "operations.jsonl", record)
    log_detailed(task_id, "executor", operation, result,
                 params=params, error=error)


def log_error(task_id: str, source: str, message: str, details: Any = None) -> None:
    record = _record(task_id, "error", {
        "source": source, "message": message,
        "details": str(details) if details else None,
    })
    _append_jsonl(_today_dir() / "operations.jsonl", record)
    log_detailed(task_id, source, "异常", "error",
                 message=message, error=str(details) if details else "")


def log_fix(task_id: str, module: str, operation: str,
            error: str, fix_attempt: str, fix_result: str,
            trace: str = "") -> None:
    log_detailed(task_id, module, operation, "fix_attempt",
                 error=error, trace=trace,
                 fix_attempt=fix_attempt, fix_result=fix_result)


def save_script(task_id: str, script_content: str) -> Path:
    script_dir = _today_dir() / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    path = script_dir / f"{task_id}.json"
    try:
        path.write_text(script_content, encoding="utf-8")
    except Exception:
        pass
    return path


def read_today_operations() -> list[dict]:
    ops_path = _today_dir() / "operations.jsonl"
    if not ops_path.exists():
        return []
    records = []
    try:
        with open(ops_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    except Exception:
        pass
    return records


def read_today_tasks() -> list[dict]:
    tasks_path = _today_dir() / "tasks.jsonl"
    if not tasks_path.exists():
        return []
    records = []
    try:
        with open(tasks_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    except Exception:
        pass
    return records


def read_today_detailed() -> str:
    log_path = _today_dir() / "detailed.log"
    if not log_path.exists():
        return ""
    try:
        return log_path.read_text(encoding="utf-8")
    except Exception:
        return ""
