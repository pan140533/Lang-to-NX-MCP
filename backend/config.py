"""
配置文件 — Lang-to-NX-MCP

默认使用 DeepSeek，用户可在 .env 中自定义。
NX 执行通过 run_journal.exe + C#，不需要 Python NXOpen 环境。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 固定从项目根目录读取 .env，保证被 MCP 客户端从任意工作目录拉起时都能读到。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

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

# MCP 客户端启动本服务时通常只传精简环境，NX 需要的变量可能缺失。
# 这里显式读取，执行时再补到子进程环境里。
SPLM_LICENSE_SERVER = os.getenv("SPLM_LICENSE_SERVER", "")
UGII_LANG = os.getenv("UGII_LANG", "")
NX_TIMEOUT_SECONDS = int(os.getenv("NX_TIMEOUT_SECONDS", "300"))

# ── 会话超时 ──
SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
