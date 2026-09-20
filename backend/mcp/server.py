"""
MCP Server — 通过 stdio 传输层与 AI Agent 通信

每个工具 handler 不直接调 NXOpen API，而是：
  生成 C# Journal → run_journal.exe（外部进程）→ 返回结果

这确保了：
  - NX 不需要持续打开（用完即退）
  - 不会在 NX 进程内跑重型 Python
  - 适合批量建模场景

关于 mcp 版本（重要）：
  1.x 用的是装饰器 —— @server.list_tools() / @server.call_tool()；
  2.x 把这两个装饰器删掉了，改成创建 Server 时传回调：
      Server(name, on_list_tools=..., on_call_tool=...)
  回调直接返回 types.ListToolsResult / types.CallToolResult。
  本文件按 2.x 写（requirements.txt 里 mcp>=1.0.0 实际会装到 2.x）。
  stdio_server() 与 server.run(...) 的用法在 2.x 没变。
"""
from __future__ import annotations

import asyncio
import importlib
import json
import logging
import pkgutil
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

from backend.mcp.registry import ToolRegistry
from backend.mcp.response import ToolError, ToolResult

logger = logging.getLogger("lang-to-nx-mcp")


def _discover_tools() -> None:
    """自动发现所有工具模块（在 tools/ 目录下）"""
    import backend.mcp.tools as tools_pkg

    for _importer, modname, _ispkg in pkgutil.iter_modules(tools_pkg.__path__):
        if modname == "registry" or modname.startswith("_"):
            continue
        full_name = f"{tools_pkg.__name__}.{modname}"
        try:
            importlib.import_module(full_name)
            logger.info("发现工具模块: %s", full_name)
        except Exception as e:
            # 日志走 stderr；stdout 是 JSON-RPC 通道，绝不能污染
            logger.error("导入工具模块失败 %s: %s", full_name, e)


def _build_tools() -> list[Tool]:
    """把注册表里的工具定义转成 mcp.types.Tool 列表"""
    return [
        Tool(
            name=t["name"],
            description=t["description"],
            input_schema=t["inputSchema"],
        )
        for t in ToolRegistry.list_tools()
    ]


async def _call_tool_text(name: str, arguments: dict[str, Any]) -> tuple[str, bool]:
    """派发工具调用。

    Returns:
        (文本, 是否错误)。文本是 JSON 字符串，客户端按 JSON 解析即可。
    """
    handler = ToolRegistry.get_handler(name)
    if handler is None:
        error = ToolError(
            error_code="TOOL_NOT_FOUND",
            message=f"未知工具: {name}",
            suggestion=f"可用工具: {', '.join(ToolRegistry.get_tool_names())}",
        )
        return error.to_text(), True

    try:
        result = await handler(**arguments)
    except Exception as exc:
        error = ToolError(
            error_code="EXECUTION_ERROR",
            message=str(exc),
            suggestion="检查 NX 安装路径和配置文件",
        )
        return error.to_text(), True

    if isinstance(result, str):
        return result, False
    if isinstance(result, ToolResult):
        return result.to_text(), False
    if isinstance(result, ToolError):
        return result.to_text(), True
    if isinstance(result, dict):
        return json.dumps(result, indent=2, ensure_ascii=False), False
    return str(result), False


def create_server() -> Server:
    """创建 MCP Server（mcp 2.x：回调用构造参数注册）"""
    _discover_tools()

    async def on_list_tools(_context: Any, _params: Any) -> ListToolsResult:
        return ListToolsResult(tools=_build_tools())

    async def on_call_tool(_context: Any, params: CallToolRequestParams) -> CallToolResult:
        text, is_error = await _call_tool_text(
            params.name, dict(params.arguments or {})
        )
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            is_error=is_error,
        )

    return Server(
        "lang-to-nx-mcp",
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
    )


async def async_main() -> None:
    """启动 MCP Server（stdio 传输）"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    server = create_server()
    logger.info("Lang-to-NX MCP Server 启动 (stdio 传输)")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """入口点"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
