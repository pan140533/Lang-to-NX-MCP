#!/usr/bin/env python
"""
Lang-to-NX MCP — 启动入口

用法:
  python run.py                  # 启动 MCP Server (stdio)
  python run.py --api            # 启动 FastAPI Server (HTTP)
  python run.py --list-tools     # 列出所有注册的工具
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# 确保 backend 在 Python path 中
sys.path.insert(0, str(Path(__file__).parent))


def run_mcp():
    """启动 MCP Server（stdio 传输，供 AI Agent 连接）"""
    from backend.mcp.server import async_main
    import asyncio
    asyncio.run(async_main())


def run_api():
    """启动 FastAPI Server（HTTP 传输，供前端连接）"""
    import uvicorn
    from backend.config import config
    print(f"启动 FastAPI Server: http://{config.host}:{config.port}")
    uvicorn.run("backend.api:app", host=config.host, port=config.port, reload=True)


def list_tools():
    """列出所有已注册的 MCP 工具"""
    from backend.mcp.registry import ToolRegistry
    from backend.mcp.server import _discover_tools

    _discover_tools()
    tools = ToolRegistry.list_tools()
    print(f"\n已注册 {len(tools)} 个 MCP 工具:\n")
    for t in sorted(tools, key=lambda x: x["name"]):
        print(f"  {t['name']}")
        print(f"    描述: {t['description'][:80]}")
        params = t.get("inputSchema", {}).get("properties", {})
        if params:
            print(f"    参数: {', '.join(params.keys())}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Lang-to-NX MCP")
    parser.add_argument("--api", action="store_true", help="启动 FastAPI Server（HTTP）")
    parser.add_argument("--list-tools", action="store_true", help="列出所有工具")
    args = parser.parse_args()

    # 加载 .env
    # backend.config 在 import 时就自行加载 .env（不依赖第三方库），
    # 这里保留 python-dotenv 只是为了兼容旧行为；未安装时不再中断启动。
    env_path = Path(__file__).parent / ".env"
    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None
    if env_path.exists():
        if load_dotenv is not None:
            load_dotenv(env_path)
        # 必须走 stderr：不带参数运行时 stdout 就是 MCP 的 JSON-RPC 通道，
        # 往里 print 一行非 JSON 内容会让客户端解析失败。
        print(f"已加载配置: {env_path}", file=sys.stderr)

    if args.api:
        run_api()
    elif args.list_tools:
        list_tools()
    else:
        # 验证配置
        from backend.config import config
        errors = config.validate()
        if errors:
            # 同样走 stderr —— 这个分支接下来就要启动 MCP，stdout 不能被占用
            # 不要用 ⚠ 这类 GBK 编码不了的符号：中文控制台上会抛 UnicodeEncodeError，
            # 偏偏这时候用户最需要看到错误信息
            print("配置检查发现以下问题:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            print("请检查 .env 文件或环境变量\n", file=sys.stderr)

        run_mcp()


if __name__ == "__main__":
    main()
