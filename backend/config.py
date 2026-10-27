"""
配置文件 — Lang-to-NX-MCP

默认使用 DeepSeek，用户可在 .env 中自定义。
NX 执行通过 run_journal.exe + C#，不需要 Python NXOpen 环境。
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM 配置（默认 DeepSeek）──
LLM_CONFIG = {
    "base_url": os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
    "api_key": os.getenv("LLM_API_KEY", ""),
    "model": os.getenv("LLM_MODEL", "deepseek-chat"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
}

# ── 输出目录 ──
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
SESSION_DIR = os.getenv("SESSION_DIR", "sessions")

# ── NX 执行配置（C# + run_journal.exe）──
NX_ROOT = os.getenv("NX_ROOT", "")
NX_EXE = os.path.join(NX_ROOT, "NXBIN", "run_journal.exe")
MODELER_DIR = os.path.join(os.path.dirname(__file__), "tools")

# ── 会话超时 ──
SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
