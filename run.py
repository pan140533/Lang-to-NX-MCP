"""Lang-to-NX-MCP — MCP 服务器入口（stdio 传输）。

用法：
    python run.py                 # 启动 MCP 服务器（由 MCP 客户端拉起的常规方式）
    python run.py --check         # 检查 NX 路径配置是否就绪
    python run.py --list-tools    # 列出全部建模工具（已实现 / 未实现）
    python run.py --help
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

USAGE = """Lang-to-NX-MCP — 自然语言驱动 Siemens NX 建模的 MCP 服务器

用法:
  python run.py               启动 MCP 服务器（stdio），由 MCP 客户端调用
  python run.py --check       检查 NX 路径 / 输出目录配置
  python run.py --list-tools  列出建模工具
  python run.py --help        显示本帮助

运行前必须手动配置 .env 中的 NX_ROOT（程序不会自动搜索磁盘）。
"""


def _check() -> int:
    from backend.mcp.service import config_info

    info = config_info()
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0 if info["ready"] else 1


def _list_tools() -> int:
    from backend.mcp.service import list_tools

    data = list_tools()
    print(f"建模工具 {data['count']} 个：已实现 {data['available_count']}，"
          f"未实现 {data['pending_count']}\n")
    for tool in data["tools"]:
        flag = "✓" if tool["implemented"] else "·"
        print(f"  {flag} {tool['name']:<22} {tool['description']}")
    if data["pending"]:
        print(f"\n未实现（仅占位，不产生几何）：{', '.join(data['pending'])}")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if any(a in ("-h", "--help") for a in argv):
        print(USAGE)
        return 0
    if "--check" in argv:
        return _check()
    if "--list-tools" in argv:
        return _list_tools()

    from backend.mcp.server import main as serve

    serve()
    return 0


if __name__ == "__main__":
    sys.exit(main())
