"""JSON 工具调用执行引擎 — NX 版本

将 AI 输出的 JSON 工具调用序列翻译为 NXOpen Python 函数调用。

与 CATIA 版本的架构区别：
  - CATIA: JSON → Python COM 封装层 → CATIA（COM 需要额外封装）
  - NX:    JSON → NXOpen 函数调用 → NX（原生 Python API，更直接可靠）

实际使用时，也可以绕过 JSON 层，让 AI 直接生成 NXOpen Python 代码。

用法：
    session = NXSession()
    executor = ToolExecutor(session)
    result = executor.execute([
        {"tool": "new_document", "params": {}},
        {"tool": "create_sketch_on_plane", "params": {"plane_id": "XY", "sketch_name": "s1"},
         "ref": "sketch_main"},
        {"tool": "draw_closed_circle", "params": {"sketch": "sketch_main", "x": 0, "y": 0, "radius": 15}},
        {"tool": "extrude", "params": {"sketch": "sketch_main", "length": 30}, "ref": "pad_1"},
        {"tool": "save_model", "params": {"path": "C:/model.prt"}},
    ])
"""
from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import Any, Optional

from .nx_session import NXSession
from . import sketch as sketch_tools
from . import features as feature_tools
from . import io as io_tools
from . import planes as plane_tools
from . import selection as sel_tools
from log_system import log_operation, log_error, log_fix

# 工具名 → Python 函数映射
_TOOL_REGISTRY = {
    "new_document":           io_tools.new_document,
    "save_model":            io_tools.save_model,
    "save_as_step":          io_tools.save_as_step,
    "create_sketch_on_plane": sketch_tools.create_sketch_on_plane,
    "open_sketch":           sketch_tools.open_sketch,
    "close_sketch":          sketch_tools.close_sketch,
    "draw_closed_circle":    sketch_tools.draw_closed_circle,
    "draw_rectangle":        sketch_tools.draw_rectangle,
    "draw_line":             sketch_tools.draw_line,
    "extrude":               feature_tools.extrude,
    "extrude_cut":           feature_tools.extrude_cut,
    "revolve":               feature_tools.revolve,
    "offset_plane":          plane_tools.offset_plane,
    "chamfer":               feature_tools.chamfer,
    "fillet":                feature_tools.fillet,
    "rib":                   feature_tools.rib,
    "stiffener":             feature_tools.stiffener,
}

# 加载 tools.json 获取参数 schema
_TOOLS_SCHEMA_PATH = Path(__file__).parent / "tools.json"
_TOOL_SCHEMAS: dict = {}
if _TOOLS_SCHEMA_PATH.exists():
    try:
        for t in json.loads(_TOOLS_SCHEMA_PATH.read_text(encoding="utf-8")).get("tools", []):
            _TOOL_SCHEMAS[t["name"]] = t
    except Exception:
        pass


class ToolExecutor:
    """JSON 工具调用执行器（NX 版本）"""

    def __init__(self, session: NXSession, task_id: str = ""):
        self.session = session
        self.task_id = task_id
        self.refs: dict[str, Any] = {}      # 引用名 → NXOpen 对象
        self.history: list[dict] = []        # 执行历史

    def execute(self, steps: list[dict]) -> dict:
        """执行一组工具调用

        Args:
            steps: JSON 工具调用序列

        Returns:
            {"status": "ok"|"error", "steps": [...], "error": "..."}
        """
        self.history = []
        for i, step in enumerate(steps):
            result = self._execute_one(i + 1, step)
            self.history.append(result)
            if result["status"] == "error":
                return {
                    "status": "error",
                    "steps": self.history,
                    "error": f"步骤 {i+1} ({step.get('tool')}) 失败: {result.get('error')}",
                    "failed_step": i + 1,
                }
        return {"status": "ok", "steps": self.history}

    def _execute_one(self, step_num: int, step: dict) -> dict:
        """执行单步工具调用"""
        tool_name = step.get("tool", "")
        params = dict(step.get("params", {}))
        ref_name = step.get("ref", "")

        t_start = time.time()
        result = {
            "step": step_num,
            "tool": tool_name,
            "params": params,
            "status": "error",
            "error": "",
        }

        # 1. 检查工具是否存在
        func = _TOOL_REGISTRY.get(tool_name)
        if func is None:
            err = f"未知工具: {tool_name}"
            result["error"] = err
            log_error(self.task_id, "executor", err, {"step": step_num, "tool": tool_name})
            return result

        # 2. 解析 ref 类型的参数（字符串 → NXOpen 对象）
        try:
            resolved = self._resolve_refs(tool_name, params)
        except Exception as e:
            err = f"参数解析失败: {e}"
            result["error"] = err
            log_error(self.task_id, "executor", err, {"step": step_num, "params": params})
            return result

        # 3. 执行函数
        try:
            return_value = func(self.session, **resolved)
        except Exception as e:
            err = str(e)
            tb = traceback.format_exc()
            result["error"] = err
            result["traceback"] = tb
            log_error(self.task_id, f"executor.{tool_name}", err, {"step": step_num, "params": resolved})
            log_operation(self.task_id, tool_name, resolved, "failed", error=err,
                          duration_ms=(time.time() - t_start) * 1000)
            return result

        # 4. 处理 edge_index 参数（chamfer/fillet）
        if tool_name in ("chamfer", "fillet") and "edge_index" in params:
            self._handle_edge_feature(tool_name, step, return_value)

        # 5. 存储引用
        if ref_name and return_value is not None:
            self.refs[ref_name] = return_value

        duration = (time.time() - t_start) * 1000
        log_operation(self.task_id, tool_name, resolved, "success", duration_ms=duration)

        result["status"] = "ok"
        result["duration_ms"] = round(duration, 1)
        return result

    def _resolve_refs(self, tool_name: str, params: dict) -> dict:
        """将 params 中的 ref 字符串替换为 NXOpen 对象"""
        schema = _TOOL_SCHEMAS.get(tool_name, {})
        param_schemas = schema.get("params", {})

        resolved = {}
        for key, value in params.items():
            param_schema = param_schemas.get(key, {})
            if param_schema.get("type") == "ref" and isinstance(value, str):
                if value not in self.refs:
                    raise ValueError(f"引用 '{value}' 未定义（前面步骤没有输出这个引用）")
                resolved[key] = self.refs[value]
            else:
                resolved[key] = value

        # 移除 executor 内部用的参数（不传给函数）
        resolved.pop("feature_ref", None)
        resolved.pop("edge_index", None)
        return resolved

    def _handle_edge_feature(self, tool_name: str, step: dict, return_value):
        """chamfer/fillet 的后续处理"""
        pass

    def get_history(self) -> list[dict]:
        return self.history
