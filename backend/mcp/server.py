"""Lang-to-NX-MCP —— MCP 服务器（stdio 传输）。

对 MCP 客户端暴露的全部能力：
  nx_create            自然语言 → NX 模型（完整 Agent 流水线）
  nx_execute_plan      显式建模步骤 → NX 模型
  nx_create_block / nx_create_cylinder / nx_create_cone / nx_create_sphere
  nx_list_tools        列出全部建模工具及其参数
  nx_get_config        检查 NX 路径配置是否就绪

注意：stdio 模式下 stdout 是 MCP 协议通道，业务代码里任何 print()
都必须改道 stderr，否则会污染协议、客户端直接断连。
"""
from __future__ import annotations

import contextlib
import functools
import sys
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from backend.mcp import service

INSTRUCTIONS = """Lang-to-NX-MCP：用自然语言驱动 Siemens NX 建模。

推荐流程：
1. 先调用 nx_get_config 确认 ready=true（即 NX 路径已配置）。
2. 不确定工具名/参数时调用 nx_list_tools（implemented=false 的是尚未实现的工具，不要用）。
3. 用 nx_create 传一句自然语言描述（如「做一个直径 60、高 20 的圆柱」），
   或对步骤有精确要求时用 nx_execute_plan 传 steps 数组。

执行方式：每条指令都会生成 C# Journal，交给 NX 的 run_journal.exe 以外部进程执行，
完成后在 output/models/ 下产出 .prt 文件。NX 启动较慢，单次调用通常需要 30~120 秒。
"""

mcp = FastMCP("lang-to-nx-mcp", instructions=INSTRUCTIONS)


def _quiet(fn):
    """把业务代码的 stdout 输出改到 stderr，避免污染 MCP 协议通道。"""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with contextlib.redirect_stdout(sys.stderr):
            return fn(*args, **kwargs)

    return wrapper


def _safe(fn):
    """统一把异常转成结构化结果，避免 MCP 客户端只看到裸异常。"""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as exc:
            return {"status": "error", "message": str(exc)}
        except Exception as exc:  # noqa: BLE001 - 顶层兜底
            return {"status": "error", "message": f"{type(exc).__name__}: {exc}"}

    return wrapper


@mcp.tool()
@_quiet
@_safe
def nx_create(description: str, name: Optional[str] = None) -> Dict[str, Any]:
    """用一句自然语言创建 NX 模型（推荐入口）。

    内部会走完整 Agent 流水线：意图识别 → 结构分解 → 步骤规划 → 生成 C# → 执行 NX。

    Args:
        description: 零件描述，中文或英文均可。例：
            "做一个直径 60、高 20 的圆柱"
            "做一个三叶风扇，中心带轴孔"
            "做一个 20 齿的齿轮，模数 1.5，厚度 15"
        name: 可选输出名（ASCII，会作为 .prt 文件名）。不传则按时间自动生成。

    Returns:
        status=success 时包含 part_file（.prt 路径）、steps（实际执行的步骤）、
        message、strategy；失败时包含 message 与可执行的修正建议。
        单次调用通常耗时 30~120 秒（NX 启动占大头）。
    """
    return service.create_model(description, name)


@mcp.tool()
@_quiet
@_safe
def nx_execute_plan(steps: List[Dict[str, Any]], name: Optional[str] = None) -> Dict[str, Any]:
    """执行一组建模步骤（跳过 Agent 规划，适合需要精确控制的场景）。

    steps 里每一步的格式：{"tool": "工具名", "params": {...}}
    工具名与参数请先用 nx_list_tools 查询。未提供 new_document 时会自动补在最前面。

    典型的最短流程：
        [{"tool": "new_document", "params": {}},
         {"tool": "create_sketch_on_plane", "params": {}},
         {"tool": "draw_closed_circle", "params": {"x": 0, "y": 0, "radius": 30}},
         {"tool": "close_sketch", "params": {}},
         {"tool": "extrude", "params": {"length": 20}}]

    Args:
        steps: 建模步骤数组。
        name: 可选输出名（ASCII，.prt 文件名）。

    Returns:
        status、message、output_name、part_file、part_exists、steps、journal。
    """
    return service.execute_plan(steps, name)


@mcp.tool()
@_quiet
@_safe
def nx_create_block(
    length: float,
    width: float,
    height: float,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """直接创建一个长方体（单位 mm）。x/y/z 是起始角点，长方体沿 +X/+Y/+Z 生长。"""
    steps = [
        {"tool": "new_document", "params": {}},
        {"tool": "block", "params": {"x": x, "y": y, "z": z,
                                     "length": length, "width": width, "height": height}},
    ]
    return service.execute_plan(steps, name)


@mcp.tool()
@_quiet
@_safe
def nx_create_cylinder(
    radius: float,
    height: float,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """直接创建一个圆柱（单位 mm）。圆心在 (x, y)，从 z 向上拉伸 height。"""
    steps = [
        {"tool": "new_document", "params": {}},
        {"tool": "cylinder", "params": {"x": x, "y": y, "z": z,
                                        "radius": radius, "height": height}},
    ]
    return service.execute_plan(steps, name)


@mcp.tool()
@_quiet
@_safe
def nx_create_cone(radius: float, height: float, name: Optional[str] = None) -> Dict[str, Any]:
    """直接创建一个圆锥（单位 mm）。"""
    steps = [
        {"tool": "new_document", "params": {}},
        {"tool": "cone", "params": {"radius": radius, "height": height}},
    ]
    return service.execute_plan(steps, name)


@mcp.tool()
@_quiet
@_safe
def nx_create_sphere(radius: float, name: Optional[str] = None) -> Dict[str, Any]:
    """直接创建一个球体（单位 mm）。"""
    steps = [
        {"tool": "new_document", "params": {}},
        {"tool": "sphere", "params": {"radius": radius}},
    ]
    return service.execute_plan(steps, name)


@mcp.tool()
@_quiet
@_safe
def nx_list_tools() -> Dict[str, Any]:
    """列出全部建模工具：名称、分类、参数、以及是否已实现（implemented）。

    标为 implemented=false 的工具目前只有占位实现（打印一行，不产生几何），
    规划步骤时请避开。
    """
    return service.list_tools()


@mcp.tool()
@_quiet
@_safe
def nx_get_config() -> Dict[str, Any]:
    """检查运行环境：NX_ROOT、run_journal.exe 是否存在、模型输出目录、超时时间。

    返回 ready=false 说明 NX 路径没配好，此时任何建模调用都会失败。
    """
    return service.config_info()


def main() -> None:
    """启动 MCP 服务器（stdio）。"""
    print("Lang-to-NX-MCP 启动（stdio）", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
