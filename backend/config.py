"""
配置管理

从 .env 或环境变量加载，提供所有 NX 相关路径。
支持两种 NX 执行方式：
  1. run_journal.exe（外部进程，批量场景）
  2. NXOpen Python API（进程内交互场景，可选）
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _load_env_file(path: Path) -> None:
    """把 .env 里的键值对注入 os.environ（已存在的环境变量优先，不覆盖）。

    为什么需要它：之前只有 run.py 会在启动时调用 python-dotenv 加载 .env，
    任何直接 `import backend.config` 的入口（FastAPI、脚本、测试）都会静默退回
    默认的 `C:\\Program Files\\Siemens\\NX`，导致 run_journal.exe 找不到。
    这里做一个不依赖第三方库的最小解析器，python-dotenv 缺失时也能工作。
    """
    try:
        content = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return

    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv_file = _load_env_file  # 兼容别名
_load_env_file(Path(__file__).resolve().parent.parent / ".env")


@dataclass
class Config:
    # ── NX Installation ──
    nx_root: str = field(default_factory=lambda: _env("NX_ROOT", r"C:\Program Files\Siemens\NX"))
    nx_version: str = field(default_factory=lambda: _env("NX_VERSION", "2412"))

    # ── NX Execution ──
    run_journal_exe: str = field(init=False)
    nx_exe: str = field(default_factory=lambda: _env("NX_EXE", ""))  # fallback

    def __post_init__(self):
        default_exe = os.path.join(self.nx_root, "NXBIN", "run_journal.exe")
        self.run_journal_exe = _env("RUN_JOURNAL_EXE", default_exe)

    @property
    def run_journal_path(self) -> str:
        return self.run_journal_exe

    # ── Output ──
    output_dir: str = field(default_factory=lambda: _env("OUTPUT_DIR", os.path.join(Path(__file__).parent.parent, "output")))

    # ── LLM (optional, for agent pipeline) ──
    llm_api_key: str = field(default_factory=lambda: _env("LLM_API_KEY", ""))
    llm_base_url: str = field(default_factory=lambda: _env("LLM_BASE_URL", "https://api.deepseek.com"))
    llm_model: str = field(default_factory=lambda: _env("LLM_MODEL", "deepseek-chat"))
    llm_temperature: float = float(_env("LLM_TEMPERATURE", "0.7"))

    # ── Server ──
    host: str = field(default_factory=lambda: _env("HOST", "127.0.0.1"))
    port: int = int(_env("PORT", "8000"))

    # ── C# Journal generation ──
    journal_template_path: str = field(default_factory=lambda: _env("JOURNAL_TEMPLATE_PATH", ""))

    def ensure_dirs(self):
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "models"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "scripts"), exist_ok=True)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not os.path.exists(self.run_journal_exe):
            errors.append(f"run_journal.exe 未找到: {self.run_journal_exe}")
        return errors


# ── Global singleton ──
config = Config()
