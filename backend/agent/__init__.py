"""
Agent 模块 — AI 分析任务管理层

职责：
  让 AI 理解「自己在做什么」「准备做什么」「用户意图是什么」「下一步该考虑什么」

模块结构：
  intent.py     — 意图识别：用户想干什么？
  decomposer.py — 结构分解：像人一样分析模型组成（重复/对称/旋转体）
  memory.py     — 上下文记忆：当前零件状态、历史对话、关注焦点
  planner.py    — 任务规划：先分解结构，再生成最优步骤
  executor.py   — 执行调度：按计划逐步执行，处理错误和反馈

数据流：
  用户输入 → IntentRecognition → StructuralDecomposer → [MemoryContext] → TaskPlanner → Executor → NX
"""

from .intent import IntentRecognition, Intent, IntentType, EntityInfo
from .decomposer import StructuralDecomposer, DecompositionResult, DecomposedPart, DecompositionStrategy
from .memory import ContextMemory, MemoryEntry, ModelState, ModelPhase, Focus
from .planner import TaskPlanner, TaskPlan, TaskStep, StepType
from .executor import Executor, ExecutionResult, ExecutionStatus, AgentPipeline

__all__ = [
    # intent
    "IntentRecognition", "Intent", "IntentType", "EntityInfo",
    # decomposer
    "StructuralDecomposer", "DecompositionResult", "DecomposedPart", "DecompositionStrategy",
    # memory
    "ContextMemory", "MemoryEntry", "ModelState", "ModelPhase", "Focus",
    # planner
    "TaskPlanner", "TaskPlan", "TaskStep", "StepType",
    # executor
    "Executor", "ExecutionResult", "ExecutionStatus", "AgentPipeline",
]