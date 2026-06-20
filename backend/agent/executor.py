"""
执行调度模块

职责：
  1. 接收 TaskPlan，逐步执行
  2. 协调 Intent → Memory → Planner → Generator → NX 的完整流程
  3. 处理错误和重试
  4. 提供执行反馈

执行流程：
  Intent → Memory.update() → Planner.plan() → Executor.run() → Generator → NX
                                                      ↓
                                                 Memory.record()
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from enum import Enum


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # 部分成功


@dataclass
class ExecutionResult:
    """执行结果"""
    status: ExecutionStatus
    message: str
    steps_completed: int = 0
    steps_total: int = 0
    errors: List[str] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)
    features_created: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0

    def to_response(self) -> dict:
        return {
            "status": self.status.value,
            "message": self.message,
            "steps_completed": self.steps_completed,
            "steps_total": self.steps_total,
            "errors": self.errors,
            "output_files": self.output_files,
            "features": self.features_created,
            "duration_seconds": self.duration_seconds,
        }


class Executor:
    """
    执行调度器

    用法：
      executor = Executor(memory, generate_func, execute_func)
      result = executor.run(intent)
    """

    def __init__(self,
                 memory,      # ContextMemory
                 planner,     # TaskPlanner
                 generator_func: Callable,  # JournalGenerator.generate
                 executor_func: Callable,   # 实际执行 C# journal 的函数
                 ):
        self.memory = memory
        self.planner = planner
        self._generate = generator_func
        self._execute = executor_func

    def run(self, intent) -> ExecutionResult:
        """
        完整的执行流程：
        1. 记录用户意图
        2. 更新内存状态
        3. 生成规划
        4. 执行规划
        5. 记录结果
        """
        start_time = datetime.now()
        result = ExecutionResult(
            status=ExecutionStatus.PENDING,
            message="",
            steps_total=0,
        )

        try:
            # 1. 记录用户输入
            self.memory.record_user_message(intent.description)

            # 2. 生成规划
            plan = self.planner.plan(intent)
            self.last_plan = plan  # 供外部访问

            if not plan.steps:
                result.status = ExecutionStatus.FAILED
                result.message = "无法生成执行计划"
                result.errors = plan.warnings
                return result

            result.steps_total = len(plan.steps)

            # 3. 验证规划
            validation_errors = self.planner.validate_plan(plan)
            if validation_errors:
                result.errors.extend(validation_errors)
                # 不阻塞，继续执行（有些工具是 TODO 状态）

            # 4. 执行步骤
            result.status = ExecutionStatus.RUNNING
            tool_calls = plan.to_tool_calls()

            # 生成 C# 代码
            code = self._generate(tool_calls)

            # 执行
            success, output = self._execute(code)

            if success:
                result.status = ExecutionStatus.SUCCESS
                result.message = f"成功执行 {len(plan.steps)} 个步骤"
                result.steps_completed = len(plan.steps)
                result.output_files = output.get("files", [])
                result.features_created = output.get("features", [])

                # 更新内存
                for step in plan.steps:
                    self.memory.record(
                        description=step.step_name,
                        action=step.tool,
                        params=step.params,
                        result="success",
                    )
                self.memory.update_model_state(result.features_created)

            else:
                result.status = ExecutionStatus.FAILED
                result.message = output.get("error", "执行失败")
                result.errors.append(result.message)

                # 记录失败
                self.memory.record(
                    description=plan.steps[0].step_name if plan.steps else "未知",
                    action="error",
                    result="failed",
                )

        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.message = str(e)
            result.errors.append(str(e))

        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        return result

    def run_tool_calls(self, tool_calls: List[dict]) -> ExecutionResult:
        """直接执行工具调用列表（跳过规划）"""
        start_time = datetime.now()
        result = ExecutionResult(
            status=ExecutionStatus.RUNNING,
            message="",
            steps_total=len(tool_calls),
        )

        try:
            code = self._generate(tool_calls)
            success, output = self._execute(code)

            if success:
                result.status = ExecutionStatus.SUCCESS
                result.message = f"成功执行 {len(tool_calls)} 个工具调用"
                result.steps_completed = len(tool_calls)
                result.output_files = output.get("files", [])
                result.features_created = output.get("features", [])
            else:
                result.status = ExecutionStatus.FAILED
                result.message = output.get("error", "执行失败")
                result.errors.append(result.message)

        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.message = str(e)
            result.errors.append(str(e))

        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        return result

    def get_progress(self) -> Dict[str, Any]:
        """获取当前执行进度"""
        return {
            "model_state": self.memory.get_model_state().to_context_dict(),
            "focus": {
                "feature_id": self.memory.get_focus().feature_id,
                "feature_name": self.memory.get_focus().feature_name,
            },
            "suggestions": self.memory.get_next_action_suggestions(),
            "recent_history": [
                {"action": e.action, "description": e.description, "result": e.result}
                for e in self.memory.get_history(3)
            ],
        }


class AgentPipeline:
    """
    完整 Agent 流水线

    把 Intent → Memory → Planner → Executor 串起来，
    让 AI 知道自己「在做什么 → 准备做什么 → 下一步该考虑什么」

    用法：
      pipeline = AgentPipeline(intent_recognizer, memory, planner, executor)
      result = pipeline.process(user_input)
    """

    def __init__(self,
                 intent_recognizer,   # IntentRecognition
                 memory,              # ContextMemory
                 planner,             # TaskPlanner
                 executor,            # Executor
                 ):
        self.intent_recognizer = intent_recognizer
        self.memory = memory
        self.planner = planner
        self.executor = executor
        self.last_plan = None  # 保存最近一次规划结果，供外部访问
        self.current_output_name = ""  # 当前输出名称，每次处理请求前由 api.py 设置

    def process(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户输入，返回完整结果

        流程：
          1. 意图识别 → 知道用户想干什么
          2. 获取上下文 → 知道当前模型状态
          3. 生成规划 → 知道要做什么步骤
          4. 执行 → 调用 NX 建模
          5. 返回结果 + 下一步建议
        """
        # 1. 意图识别
        model_context = self.memory.get_model_state().to_context_dict()
        intent = self.intent_recognizer.recognize(user_input, model_context)

        # 2. 如果是闲聊，直接返回
        if intent.type.value == "chat":
            return {
                "status": "success",
                "intent": intent.type.value,
                "message": "你好！我是 NX 建模助手。你可以让我创建模型、修改特征、查询信息。",
                "suggestions": self.memory.get_next_action_suggestions(),
            }

        # 3. 如果需要追问，先判断意图类型
        # CREATE 意图即使缺少尺寸也不追问，decomposer 会提供默认值
        # MODIFY 意图缺少明确对象时追问
        if intent.needs_clarification:
            if intent.type.value == "create":
                # CREATE 意图不阻塞，用默认尺寸继续
                intent.needs_clarification = False
            else:
                return {
                    "status": "need_clarification",
                    "intent": intent.type.value,
                    "message": intent.clarification_question,
                    "suggestions": self.memory.get_next_action_suggestions(),
                }

        # 4. 执行规划
        result = self.executor.run(intent)
        self.last_plan = self.executor.last_plan  # 传递规划结果

        # 5. 组装响应
        response = result.to_response()
        response["intent"] = intent.type.value
        response["strategy"] = intent.modeling_strategy
        response["next_action_hint"] = intent.next_action_hint
        response["suggestions"] = self.memory.get_next_action_suggestions()
        response["model_summary"] = self.memory.get_model_state().summary()

        return response

    def get_status(self) -> Dict[str, Any]:
        """获取当前 Agent 状态"""
        return self.executor.get_progress()