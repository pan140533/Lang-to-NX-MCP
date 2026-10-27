"""MCP 服务核心。

职责：
  自然语言 / 显式步骤  →  Agent 规划  →  C# Journal  →  run_journal.exe  →  .prt

这一层不关心任何 UI；调用方是 MCP 客户端（Claude Desktop / Cursor / 任何 MCP Host）。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from backend import config
from backend.agent.executor import AgentPipeline, Executor
from backend.agent.intent import IntentRecognition
from backend.agent.memory import ContextMemory
from backend.agent.planner import TaskPlanner
from backend.journal import generator as journal_generator
from backend.journal.generator import JournalGenerator, generate_output_name
from backend.name_mapper import save_mapping

MODELS_DIR: Path = journal_generator.OUTPUT_DIR
JOURNAL_DIR: Path = Path(journal_generator.__file__).resolve().parent
TOOLS_JSON: Path = JOURNAL_DIR / "tools.json"
MODELER_CS: Path = JOURNAL_DIR / "nx_modeler.cs"

EXEC_TIMEOUT = config.NX_TIMEOUT_SECONDS

DEFAULT_LICENSE_FILE = r"C:\ProgramData\Siemens\siemens_SSQ.dat"

_pipeline: Optional[AgentPipeline] = None
_stub_cache: Optional[Set[str]] = None
_tool_specs_cache: Optional[Dict[str, Any]] = None


# ──────────────────────────────────────────────────────────────────────
# 执行：C# → NX
# ──────────────────────────────────────────────────────────────────────

def _nx_env() -> Dict[str, str]:
    """构造 run_journal 子进程环境。

    MCP 客户端（Claude Desktop / Cursor 等）拉起本服务时，子进程通常只拿到精简环境，
    NX 会因缺少 UGII_BASE_DIR / 许可证配置而报 "failed to initialize UFUN"。
    这里从 NX_ROOT 和 .env 补齐，保证服务自身可独立运行。
    """
    env = os.environ.copy()

    # NX 的 SaveAs 依赖临时目录；MCP 客户端只透传 TEMP、不传 TMP，
    # 缺了会报 "Invalid temporary directory"。这里补齐。
    tmp_dir = env.get("TEMP") or env.get("TMP") or tempfile.gettempdir()
    env.setdefault("TEMP", tmp_dir)
    env.setdefault("TMP", tmp_dir)

    if config.NX_ROOT:
        env.setdefault("UGII_BASE_DIR", config.NX_ROOT)
        nxbin = os.path.join(config.NX_ROOT, "NXBIN")
        path_parts = env.get("PATH", "").split(os.pathsep)
        if nxbin not in path_parts:
            env["PATH"] = nxbin + os.pathsep + env.get("PATH", "")

    if config.SPLM_LICENSE_SERVER:
        env["SPLM_LICENSE_SERVER"] = config.SPLM_LICENSE_SERVER
    elif not env.get("SPLM_LICENSE_SERVER") and os.path.exists(DEFAULT_LICENSE_FILE):
        env["SPLM_LICENSE_SERVER"] = DEFAULT_LICENSE_FILE

    if config.UGII_LANG:
        env.setdefault("UGII_LANG", config.UGII_LANG)

    return env


def _unique_output_name(base: str) -> str:
    """NX 的 SaveAs 遇到同名文件会直接报 'File already exists'，这里保证不重名。"""
    candidate = base
    index = 1
    while (MODELS_DIR / f"{candidate}.prt").exists():
        candidate = f"{base}_{index}"
        index += 1
    return candidate


def run_journal(code: str, output_name: str) -> Dict[str, Any]:
    """保存 C# journal 并交给 run_journal.exe 执行，返回结构化结果。"""
    gen = JournalGenerator(part_name=output_name)
    journal_path = gen.save_journal(code)
    part_path = MODELS_DIR / f"{output_name}.prt"
    exe = config.NX_EXE

    if not exe or not os.path.exists(exe):
        return {
            "ok": False,
            "error": (
                f"找不到 run_journal.exe：{exe or '(未配置)'}。"
                "请检查项目根目录 .env 里的 NX_ROOT 是否指向你的 NX 安装目录"
                "（该目录下应有 NXBIN\\run_journal.exe）。程序不会自动搜索磁盘。"
            ),
            "journal": str(journal_path),
            "part_file": str(part_path),
        }

    try:
        proc = subprocess.run(
            [exe, os.path.abspath(journal_path)],
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT,
            encoding="gbk",
            errors="ignore",
            env=_nx_env(),
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": f"NX 执行超时（>{EXEC_TIMEOUT}s）。可用环境变量 NX_TIMEOUT_SECONDS 调大。",
            "journal": str(journal_path),
            "part_file": str(part_path),
        }
    except OSError as exc:
        return {
            "ok": False,
            "error": f"启动 run_journal.exe 失败：{exc}",
            "journal": str(journal_path),
            "part_file": str(part_path),
        }

    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "journal": str(journal_path),
        "part_file": str(part_path),
        "part_exists": part_path.exists(),
        "part_size": part_path.stat().st_size if part_path.exists() else 0,
        "stdout": (proc.stdout or "")[-2000:],
        "stderr": (proc.stderr or "")[-2000:],
    }


# ──────────────────────────────────────────────────────────────────────
# Agent 流水线（进程内单例，跨工具调用保留上下文）
# ──────────────────────────────────────────────────────────────────────

def get_pipeline() -> AgentPipeline:
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    memory = ContextMemory()
    planner = TaskPlanner(memory=memory)
    executor = Executor(memory, planner, lambda calls: "", lambda code: (False, {}))
    pipeline = AgentPipeline(IntentRecognition(), memory, planner, executor)

    def _generate(tool_calls: List[dict]) -> str:
        name = pipeline.current_output_name or "model"
        return JournalGenerator(part_name=name).generate(tool_calls)

    def _execute(code: str):
        name = pipeline.current_output_name or "model"
        res = run_journal(code, name)
        if not res["ok"]:
            return False, {
                "error": res.get("error") or (res.get("stderr") or "").strip()[-500:] or "NX 执行失败"
            }
        return True, {
            "files": [res["part_file"]],
            "features": [],
            "journal": res["journal"],
        }

    executor._generate = _generate
    executor._execute = _execute
    _pipeline = pipeline
    return pipeline


def create_model(description: str, name: Optional[str] = None) -> Dict[str, Any]:
    """自然语言 → 规划 → C# → NX → .prt。"""
    description = (description or "").strip()
    if not description:
        raise ValueError("description 不能为空")

    pipeline = get_pipeline()
    output_name = _unique_output_name(name or generate_output_name(description))
    pipeline.current_output_name = output_name

    try:
        save_mapping(output_name, description[:50], description)
    except Exception:
        pass  # 名称映射只是辅助信息，失败不影响建模

    result = pipeline.process(description)

    plan = pipeline.last_plan
    steps = [{"tool": s.tool, "params": s.params} for s in plan.steps] if plan else []

    result["output_name"] = output_name
    result["steps"] = steps
    if result.get("status") == "success" and not result.get("part_file"):
        result["part_file"] = str(MODELS_DIR / f"{output_name}.prt")
    return result


# ──────────────────────────────────────────────────────────────────────
# 显式步骤执行
# ──────────────────────────────────────────────────────────────────────

def _normalize_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(steps, list) or not steps:
        raise ValueError("steps 必须是非空数组")

    normalized = []
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"steps[{i}] 必须是对象")
        tool = step.get("tool")
        if not isinstance(tool, str) or not tool:
            raise ValueError(f"steps[{i}].tool 缺失")
        params = step.get("params") or {}
        if not isinstance(params, dict):
            raise ValueError(f"steps[{i}].params 必须是对象")
        normalized.append({"tool": tool, "params": params})

    if not any(s["tool"] == "new_document" for s in normalized):
        normalized.insert(0, {"tool": "new_document", "params": {}})
    return normalized


def execute_plan(steps: List[Dict[str, Any]], name: Optional[str] = None) -> Dict[str, Any]:
    """直接执行一组建模步骤（跳过 Agent 规划）。"""
    normalized = _normalize_steps(steps)
    known = set(known_tools())
    unknown = [s["tool"] for s in normalized if s["tool"] not in known]

    if unknown:
        return {
            "status": "rejected",
            "message": f"未知工具：{', '.join(unknown)}",
            "hint": "调用 nx_list_tools 查看全部可用工具名",
        }

    output_name = _unique_output_name(name or generate_output_name("plan"))
    code = JournalGenerator(part_name=output_name).generate(normalized)
    res = run_journal(code, output_name)

    if not res["ok"]:
        return {
            "status": "error",
            "message": res.get("error") or "NX 执行失败",
            "output_name": output_name,
            "steps": normalized,
            "journal": res.get("journal"),
            "stderr": res.get("stderr", ""),
        }

    return {
        "status": "success",
        "message": f"已生成模型（{len(normalized)} 步）",
        "output_name": output_name,
        "part_file": res["part_file"],
        "part_exists": res["part_exists"],
        "part_size": res["part_size"],
        "journal": res["journal"],
        "steps": normalized,
    }


# ──────────────────────────────────────────────────────────────────────
# 工具清单 / 环境信息
# ──────────────────────────────────────────────────────────────────────

def known_tools() -> List[str]:
    """generator 里真实存在 _gen_ 方法的工具名。"""
    return sorted(m[5:] for m in dir(JournalGenerator) if m.startswith("_gen_"))


def _camel_to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def stub_tools() -> Set[str]:
    """nx_modeler.cs 里只有 Console.WriteLine("[TODO] ...") 的方法名。"""
    global _stub_cache
    if _stub_cache is not None:
        return _stub_cache

    stubs: Set[str] = set()
    try:
        text = MODELER_CS.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        _stub_cache = stubs
        return stubs

    for m in re.finditer(r"public\s+void\s+(Tool_\w+)\s*\([^)]*\)\s*\{", text):
        start = m.end() - 1  # 指向 '{'
        depth = 0
        end = start
        while end < len(text):
            ch = text[end]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
            end += 1
        if "[TODO]" in text[start:end]:
            stubs.add(_camel_to_snake(m.group(1)[5:]))

    _stub_cache = stubs
    return stubs


def list_tools() -> Dict[str, Any]:
    global _tool_specs_cache
    if _tool_specs_cache is None:
        _tool_specs_cache = json.loads(TOOLS_JSON.read_text(encoding="utf-8"))

    stubs = stub_tools()
    tools = []
    for spec in _tool_specs_cache.get("tools", []):
        name = spec.get("name", "")
        tools.append({
            "name": name,
            "category": spec.get("category", ""),
            "description": spec.get("description", ""),
            "params": spec.get("params", {}),
            "implemented": name not in stubs,
        })

    available = [t["name"] for t in tools if t["implemented"]]
    pending = [t["name"] for t in tools if not t["implemented"]]
    return {
        "count": len(tools),
        "available_count": len(available),
        "pending_count": len(pending),
        "available": available,
        "pending": pending,
        "tools": tools,
    }


def config_info() -> Dict[str, Any]:
    exe = config.NX_EXE
    exists = bool(exe) and os.path.exists(exe)
    return {
        "server": "lang-to-nx-mcp",
        "nx_root": config.NX_ROOT,
        "run_journal": exe,
        "run_journal_exists": exists,
        "models_dir": str(MODELS_DIR),
        "timeout_seconds": EXEC_TIMEOUT,
        "tool_count": len(list_tools()["tools"]),
        "ready": exists,
        "hint": (
            "已就绪" if exists
            else "未就绪：请在项目根目录 .env 中把 NX_ROOT 设为你的 NX 安装目录"
                 "（该目录下应有 NXBIN\\run_journal.exe）。程序不会自动搜索磁盘。"
        ),
    }
