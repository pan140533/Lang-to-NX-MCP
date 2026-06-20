"""
任务规划模块

将用户意图 + 上下文 → 可执行的建模步骤序列。

规划流程：
  1. 意图识别 → 知道用户想干什么
  2. 结构分解 → 像人一样分析模型的组成（重复/对称/旋转体）
  3. 步骤生成 → 根据分解结果生成最优建模步骤
  4. 验证 → 检查步骤是否在可用工具范围内

核心原则：
  遇到可以镜像、旋转、阵列完成的重复性任务，
  绝不要一个一个小部件去画。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from .intent import Intent, IntentType, EntityInfo
from .memory import ContextMemory, ModelPhase
from .decomposer import (
    StructuralDecomposer, DecompositionResult, DecomposedPart,
    DecompositionStrategy,
)


class StepType(Enum):
    """步骤类型"""
    SETUP = "setup"         # 初始化：new_document
    SKETCH = "sketch"       # 草图：create_sketch, draw_xxx
    FEATURE = "feature"     # 特征：extrude, revolve, extrude_cut
    PATTERN = "pattern"     # 阵列：pattern_linear, pattern_circular
    MIRROR = "mirror"       # 镜像：mirror_feature
    MODIFY = "modify"       # 修改：chamfer, fillet, hole
    SAVE = "save"           # 保存：save_model


@dataclass
class TaskStep:
    """一个规划步骤"""
    step_id: int
    step_name: str                     # 描述性名称
    step_type: StepType
    tool: str                          # 工具名
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)  # 依赖的步骤 ID
    note: str = ""                     # 给 AI 自己的备注

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "tool": self.tool,
            "params": self.params,
        }


@dataclass
class TaskPlan:
    """完整的任务规划"""
    intent_type: IntentType
    description: str
    human_thought: str = ""            # 人类思维过程
    decomposition: Optional[DecompositionResult] = None  # 结构分解结果
    steps: List[TaskStep] = field(default_factory=list)
    strategy: str = ""                 # 使用的策略
    estimated_tools: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_tool_calls(self) -> List[dict]:
        """转为 generator.py 可用的 JSON 步骤列表"""
        return [
            {"tool": s.tool, "params": s.params, "ref": s.step_name}
            for s in self.steps
        ]

    def summary(self) -> str:
        lines = []
        if self.human_thought:
            lines.append(self.human_thought)
            lines.append("")
        lines.append(f"建模计划：{self.description}")
        lines.append(f"策略：{self.strategy}，共 {len(self.steps)} 步")
        for i, s in enumerate(self.steps):
            lines.append(f"  {i+1}. [{s.step_type.value}] {s.step_name} → {s.tool}({s.params})")
        if self.warnings:
            lines.append(f"警告：{'; '.join(self.warnings)}")
        return "\n".join(lines)


class TaskPlanner:
    """
    任务规划器 — 先分解结构，再生成步骤

    用法：
      planner = TaskPlanner(memory, available_tools)
      plan = planner.plan(intent)
    """

    # 基础建模模板（简单形状回退用）
    TEMPLATES = {
        "圆柱": [
            ("创建草图", StepType.SKETCH, "create_sketch_on_plane", {}),
            ("画圆截面", StepType.SKETCH, "draw_closed_circle",
             {"x": 0, "y": 0, "radius": 25}),
            ("关闭草图", StepType.SKETCH, "close_sketch", {}),
            ("拉伸成圆柱", StepType.FEATURE, "extrude", {"length": 100}),
        ],
        "方块": [
            ("创建草图", StepType.SKETCH, "create_sketch_on_plane", {}),
            ("画矩形截面", StepType.SKETCH, "draw_rectangle",
             {"x": 0, "y": 0, "width": 100, "height": 100}),
            ("关闭草图", StepType.SKETCH, "close_sketch", {}),
            ("拉伸成方块", StepType.FEATURE, "extrude", {"length": 100}),
        ],
        "球": [
            ("创建球体", StepType.FEATURE, "sphere", {"radius": 50}),
        ],
        "圆锥": [
            ("创建圆锥", StepType.FEATURE, "cone", {"radius": 50, "height": 100}),
        ],
    }

    def __init__(self, memory: Optional[ContextMemory] = None,
                 available_tools: Optional[List[str]] = None):
        self.memory = memory or ContextMemory()
        self.available_tools = available_tools or []
        self.decomposer = StructuralDecomposer()

    def plan(self, intent: Intent) -> TaskPlan:
        """
        根据意图生成任务规划

        流程：
          1. 结构分解 → 分析模型组成
          2. 根据分解策略生成步骤
          3. 验证
        """
        plan = TaskPlan(
            intent_type=intent.type,
            description=intent.description,
            strategy=intent.modeling_strategy,
        )

        if intent.type == IntentType.CREATE:
            self._plan_create(intent, plan)
        elif intent.type == IntentType.MODIFY:
            self._plan_modify(intent, plan)
        elif intent.type == IntentType.QUERY:
            self._plan_query(intent, plan)
        elif intent.type == IntentType.DELETE:
            self._plan_delete(intent, plan)
        elif intent.type == IntentType.CHAT:
            plan.strategy = "chat_reply"
        else:
            plan.warnings.append(f"未知意图类型: {intent.type}")

        return plan

    def _plan_create(self, intent: Intent, plan: TaskPlan) -> None:
        """规划 CREATE 意图 — 核心方法"""

        # ── 第一步：结构分解 ──
        decomposition = self.decomposer.decompose(intent.description)
        plan.decomposition = decomposition
        plan.human_thought = decomposition.human_thought
        plan.strategy = decomposition.strategy.value

        # ── 第二步：根据分解策略生成步骤 ──
        if decomposition.strategy == DecompositionStrategy.CIRCULAR_PATTERN:
            self._build_circular_pattern_plan(decomposition, plan)
        elif decomposition.strategy == DecompositionStrategy.LINEAR_PATTERN:
            self._build_linear_pattern_plan(decomposition, plan)
        elif decomposition.strategy == DecompositionStrategy.MIRROR:
            self._build_mirror_plan(decomposition, plan)
        elif decomposition.strategy == DecompositionStrategy.REVOLVE:
            self._build_revolve_plan(decomposition, intent, plan)
        elif decomposition.strategy == DecompositionStrategy.BASE_THEN_CUT:
            self._build_base_detail_plan(decomposition, plan)
        elif decomposition.strategy == DecompositionStrategy.BASE_THEN_ADD:
            self._build_base_detail_plan(decomposition, plan)
        elif decomposition.strategy == DecompositionStrategy.STACKED:
            self._build_stacked_plan(decomposition, plan)
        elif decomposition.strategy == DecompositionStrategy.SINGLE:
            self._build_single_plan(decomposition, intent, plan)
        else:
            plan.warnings.append(f"未处理的分解策略: {decomposition.strategy}")

        plan.estimated_tools = [s.tool for s in plan.steps]

    # ═══════════════════════════════════════════════════════════════
    # 策略构建方法
    # ═══════════════════════════════════════════════════════════════

    def _build_circular_pattern_plan(self, decomp: DecompositionResult,
                                     plan: TaskPlan) -> None:
        """
        圆形阵列计划

        示例：三叶风扇
          步骤1: new_document
          步骤2: 创建中心圆柱
          步骤3: 创建一片叶子
          步骤4: 圆形阵列 → 3片叶子
          步骤5: 保存
        """
        step_id = 0

        # 1. 初始化
        plan.steps.append(TaskStep(
            step_id=step_id, step_name="初始化文档",
            step_type=StepType.SETUP, tool="new_document", params={},
        ))
        step_id += 1

        # 2. 建基体
        base = next((p for p in decomp.parts if not p.is_repeating), None)
        if base:
            base_steps = self._build_part_steps(base, step_id, "基体")
            plan.steps.extend(base_steps)
            step_id += len(base_steps)

        # 3. 建一个重复部件
        repeating = next((p for p in decomp.parts if p.is_repeating), None)
        if repeating and base:
            part_steps = self._build_part_steps(repeating, step_id, "重复部件")
            plan.steps.extend(part_steps)
            part_last_id = step_id + len(part_steps) - 1
            step_id += len(part_steps)

            # 4. 圆形阵列
            rp = repeating.repeat_params
            plan.steps.append(TaskStep(
                step_id=step_id,
                step_name=f"圆形阵列 → {repeating.repeat_count} 个{repeating.name}",
                step_type=StepType.PATTERN,
                tool="pattern_circular",
                params={
                    "feature_ref": f"feature_{part_last_id}",
                    "count": rp.get("count", repeating.repeat_count),
                    "angle": rp.get("total_angle", 360) / rp.get("count", repeating.repeat_count),
                },
                depends_on=[part_last_id],
                note=f"把一个 {repeating.name} 绕着中心均匀复制 {repeating.repeat_count} 份",
            ))
            step_id += 1

        # 5. 保存
        plan.steps.append(TaskStep(
            step_id=step_id, step_name="保存模型",
            step_type=StepType.SAVE, tool="save_model", params={},
            depends_on=[step_id - 1],
        ))

    def _build_linear_pattern_plan(self, decomp: DecompositionResult,
                                   plan: TaskPlan) -> None:
        """
        线性阵列计划

        示例：阶梯
          步骤1: new_document
          步骤2: 建基体
          步骤3: 建一个重复单元
          步骤4: 线性阵列
          步骤5: 保存
        """
        step_id = 0

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="初始化文档",
            step_type=StepType.SETUP, tool="new_document", params={},
        ))
        step_id += 1

        base = next((p for p in decomp.parts if not p.is_repeating), None)
        if base:
            base_steps = self._build_part_steps(base, step_id, "基体")
            plan.steps.extend(base_steps)
            step_id += len(base_steps)

        repeating = next((p for p in decomp.parts if p.is_repeating), None)
        if repeating and base:
            part_steps = self._build_part_steps(repeating, step_id, "重复单元")
            plan.steps.extend(part_steps)
            part_last_id = step_id + len(part_steps) - 1
            step_id += len(part_steps)

            rp = repeating.repeat_params
            plan.steps.append(TaskStep(
                step_id=step_id,
                step_name=f"线性阵列 → {repeating.repeat_count} 个{repeating.name}",
                step_type=StepType.PATTERN,
                tool="pattern_linear",
                params={
                    "feature_ref": f"feature_{part_last_id}",
                    "count_x": rp.get("count", repeating.repeat_count),
                    "spacing_x": rp.get("spacing", 20),
                    "count_y": 1,
                    "spacing_y": 0,
                },
                depends_on=[part_last_id],
                note=f"把 {repeating.name} 沿直线复制 {repeating.repeat_count} 份",
            ))
            step_id += 1

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="保存模型",
            step_type=StepType.SAVE, tool="save_model", params={},
            depends_on=[step_id - 1],
        ))

    def _build_mirror_plan(self, decomp: DecompositionResult,
                           plan: TaskPlan) -> None:
        """
        镜像计划

        示例：左右对称的翅膀
          步骤1: new_document
          步骤2: 建中心体
          步骤3: 建一侧
          步骤4: 镜像到另一侧
          步骤5: 保存
        """
        step_id = 0

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="初始化文档",
            step_type=StepType.SETUP, tool="new_document", params={},
        ))
        step_id += 1

        base = next((p for p in decomp.parts if not p.is_repeating), None)
        if base:
            base_steps = self._build_part_steps(base, step_id, "中心体")
            plan.steps.extend(base_steps)
            step_id += len(base_steps)

        half = next((p for p in decomp.parts if p.is_repeating), None)
        if half and base:
            part_steps = self._build_part_steps(half, step_id, "一侧")
            plan.steps.extend(part_steps)
            part_last_id = step_id + len(part_steps) - 1
            step_id += len(part_steps)

            plan.steps.append(TaskStep(
                step_id=step_id,
                step_name=f"镜像 → 另一侧{half.name}",
                step_type=StepType.MIRROR,
                tool="mirror_feature",
                params={
                    "feature_ref": f"feature_{part_last_id}",
                    "mirror_plane": half.repeat_params.get("plane", "yz"),
                },
                depends_on=[part_last_id],
                note="把一侧镜像到另一侧，完成对称结构",
            ))
            step_id += 1

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="保存模型",
            step_type=StepType.SAVE, tool="save_model", params={},
            depends_on=[step_id - 1],
        ))

    def _build_revolve_plan(self, decomp: DecompositionResult,
                            intent: Intent, plan: TaskPlan) -> None:
        """
        旋转体计划

        示例：花瓶
          步骤1: new_document
          步骤2: 创建草图
          步骤3: 画截面轮廓
          步骤4: revolve 360°
          步骤5: 保存
        """
        step_id = 0

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="初始化文档",
            step_type=StepType.SETUP, tool="new_document", params={},
        ))
        step_id += 1

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="创建草图",
            step_type=StepType.SKETCH, tool="create_sketch_on_plane",
            params={}, depends_on=[step_id - 1],
        ))
        step_id += 1

        # 画截面轮廓（根据形状决定用矩形还是自定义）
        if decomp.parts and decomp.parts[0].shape == "cylinder":
            plan.steps.append(TaskStep(
                step_id=step_id, step_name="画截面轮廓（圆柱）",
                step_type=StepType.SKETCH,
                tool="draw_rectangle",
                params={"x": 0, "y": 0, "width": 30, "height": 100},
                depends_on=[step_id - 1],
            ))
        else:
            # 如果是复杂旋转体（花瓶等），需要 LLM 帮忙画截面
            plan.steps.append(TaskStep(
                step_id=step_id, step_name="画截面轮廓",
                step_type=StepType.SKETCH,
                tool="draw_rectangle",
                params={"x": 0, "y": 0, "width": 30, "height": 80},
                depends_on=[step_id - 1],
                note="复杂旋转体需要更精确的截面轮廓，此处用矩形近似",
            ))
        step_id += 1

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="关闭草图",
            step_type=StepType.SKETCH, tool="close_sketch",
            params={}, depends_on=[step_id - 1],
        ))
        step_id += 1

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="旋转成型 360°",
            step_type=StepType.FEATURE, tool="revolve",
            params={"angle": 360},
            depends_on=[step_id - 1],
            note="绕 Z 轴旋转，一步生成光滑旋转体",
        ))
        step_id += 1

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="保存模型",
            step_type=StepType.SAVE, tool="save_model", params={},
            depends_on=[step_id - 1],
        ))

    def _build_base_detail_plan(self, decomp: DecompositionResult,
                                plan: TaskPlan) -> None:
        """
        基体+细节计划

        示例：方块上打4个孔
          步骤1: new_document
          步骤2: 建主体
          步骤3: 建一个孔
          步骤4: 圆形阵列孔
          步骤5: 保存
        """
        step_id = 0

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="初始化文档",
            step_type=StepType.SETUP, tool="new_document", params={},
        ))
        step_id += 1

        for part in decomp.parts:
            if part.boolean_op == "create":
                part_steps = self._build_part_steps(part, step_id, "主体")
                plan.steps.extend(part_steps)
                step_id += len(part_steps)
            elif part.boolean_op == "subtract":
                # 切除类细节：打孔/挖槽
                cut_steps = self._build_cut_steps(part, step_id)
                plan.steps.extend(cut_steps)
                part_last_id = step_id + len(cut_steps) - 1
                step_id += len(cut_steps)

                # 如果这个细节需要阵列
                if part.is_repeating and part.repeat_strategy == "circular":
                    plan.steps.append(TaskStep(
                        step_id=step_id,
                        step_name=f"圆形阵列 → {part.repeat_count} 个{part.name}",
                        step_type=StepType.PATTERN,
                        tool="pattern_circular",
                        params={
                            "feature_ref": f"feature_{part_last_id}",
                            "count": part.repeat_count,
                            "angle": 360 / part.repeat_count,
                        },
                        depends_on=[part_last_id],
                    ))
                    step_id += 1
                elif part.is_repeating and part.repeat_strategy == "linear":
                    plan.steps.append(TaskStep(
                        step_id=step_id,
                        step_name=f"线性阵列 → {part.repeat_count} 个{part.name}",
                        step_type=StepType.PATTERN,
                        tool="pattern_linear",
                        params={
                            "feature_ref": f"feature_{part_last_id}",
                            "count_x": part.repeat_count,
                            "spacing_x": part.repeat_params.get("spacing", 20),
                            "count_y": 1,
                            "spacing_y": 0,
                        },
                        depends_on=[part_last_id],
                    ))
                    step_id += 1
            elif part.boolean_op == "modify":
                # 边缘处理：倒角/圆角
                tool = "chamfer" if part.shape == "chamfer" else "fillet"
                params = {"length": 2} if tool == "chamfer" else {"radius": 5}
                plan.steps.append(TaskStep(
                    step_id=step_id,
                    step_name=f"边缘处理: {part.shape}",
                    step_type=StepType.MODIFY,
                    tool=tool,
                    params=params,
                    depends_on=[step_id - 1],
                ))
                step_id += 1

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="保存模型",
            step_type=StepType.SAVE, tool="save_model", params={},
            depends_on=[step_id - 1],
        ))

    def _build_stacked_plan(self, decomp: DecompositionResult,
                            plan: TaskPlan) -> None:
        """多层堆叠计划"""
        step_id = 0

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="初始化文档",
            step_type=StepType.SETUP, tool="new_document", params={},
        ))
        step_id += 1

        for part in decomp.parts:
            part_steps = self._build_part_steps(part, step_id, part.name)
            plan.steps.extend(part_steps)
            step_id += len(part_steps)

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="保存模型",
            step_type=StepType.SAVE, tool="save_model", params={},
            depends_on=[step_id - 1],
        ))

    def _build_single_plan(self, decomp: DecompositionResult,
                           intent: Intent, plan: TaskPlan) -> None:
        """简单单体计划"""
        if not decomp.parts:
            # 回退到模板
            self._fallback_to_template(intent, plan)
            return

        step_id = 0
        plan.steps.append(TaskStep(
            step_id=step_id, step_name="初始化文档",
            step_type=StepType.SETUP, tool="new_document", params={},
        ))
        step_id += 1

        for part in decomp.parts:
            part_steps = self._build_part_steps(part, step_id, part.name)
            plan.steps.extend(part_steps)
            step_id += len(part_steps)

        plan.steps.append(TaskStep(
            step_id=step_id, step_name="保存模型",
            step_type=StepType.SAVE, tool="save_model", params={},
            depends_on=[step_id - 1],
        ))

    # ═══════════════════════════════════════════════════════════════
    # 部件 → 步骤转换
    # ═══════════════════════════════════════════════════════════════

    def _build_part_steps(self, part: DecomposedPart, start_id: int,
                          label: str) -> List[TaskStep]:
        """将一个部件转换为建模步骤"""
        steps = []
        sid = start_id

        pos = part.position
        x, y, z = pos.get("x", 0), pos.get("y", 0), pos.get("z", 0)

        if part.shape == "cylinder":
            # 圆柱：画圆 + 拉伸
            steps.append(TaskStep(
                step_id=sid, step_name=f"创建草图({label})",
                step_type=StepType.SKETCH, tool="create_sketch_on_plane",
                params={}, depends_on=[sid - 1] if sid > 0 else [],
            )); sid += 1

            r = part.dimensions.get("radius", part.dimensions.get("diameter", 30) / 2)
            steps.append(TaskStep(
                step_id=sid, step_name=f"画圆({label})",
                step_type=StepType.SKETCH, tool="draw_closed_circle",
                params={"x": x, "y": y, "radius": r},
                depends_on=[sid - 1],
            )); sid += 1

            steps.append(TaskStep(
                step_id=sid, step_name=f"关闭草图({label})",
                step_type=StepType.SKETCH, tool="close_sketch",
                params={}, depends_on=[sid - 1],
            )); sid += 1

            h = part.dimensions.get("height", 50)
            if z > 0:
                steps.append(TaskStep(
                    step_id=sid, step_name=f"拉伸({label}, z={z})",
                    step_type=StepType.FEATURE, tool="extrude_from",
                    params={"start": z, "length": h},
                    depends_on=[sid - 1],
                ))
            else:
                steps.append(TaskStep(
                    step_id=sid, step_name=f"拉伸({label})",
                    step_type=StepType.FEATURE, tool="extrude",
                    params={"length": h},
                    depends_on=[sid - 1],
                ))
            sid += 1

        elif part.shape == "block":
            # 方块：画矩形 + 拉伸
            steps.append(TaskStep(
                step_id=sid, step_name=f"创建草图({label})",
                step_type=StepType.SKETCH, tool="create_sketch_on_plane",
                params={}, depends_on=[sid - 1] if sid > 0 else [],
            )); sid += 1

            w = part.dimensions.get("width", 50)
            h = part.dimensions.get("height", part.dimensions.get("depth", 50))
            steps.append(TaskStep(
                step_id=sid, step_name=f"画矩形({label})",
                step_type=StepType.SKETCH, tool="draw_rectangle",
                params={"x": x - w/2, "y": y - h/2, "width": w, "height": h},
                depends_on=[sid - 1],
            )); sid += 1

            steps.append(TaskStep(
                step_id=sid, step_name=f"关闭草图({label})",
                step_type=StepType.SKETCH, tool="close_sketch",
                params={}, depends_on=[sid - 1],
            )); sid += 1

            ext_h = part.dimensions.get("length", part.dimensions.get("depth", 50))
            if z > 0:
                steps.append(TaskStep(
                    step_id=sid, step_name=f"拉伸({label}, z={z})",
                    step_type=StepType.FEATURE, tool="extrude_from",
                    params={"start": z, "length": ext_h},
                    depends_on=[sid - 1],
                ))
            else:
                steps.append(TaskStep(
                    step_id=sid, step_name=f"拉伸({label})",
                    step_type=StepType.FEATURE, tool="extrude",
                    params={"length": ext_h},
                    depends_on=[sid - 1],
                ))
            sid += 1

        elif part.shape == "sphere":
            r = part.dimensions.get("radius", 25)
            steps.append(TaskStep(
                step_id=sid, step_name=f"创建球体({label})",
                step_type=StepType.FEATURE, tool="sphere",
                params={"radius": r},
                depends_on=[sid - 1] if sid > 0 else [],
            )); sid += 1

        elif part.shape == "cone":
            r = part.dimensions.get("radius", 25)
            h = part.dimensions.get("height", 50)
            steps.append(TaskStep(
                step_id=sid, step_name=f"创建圆锥({label})",
                step_type=StepType.FEATURE, tool="cone",
                params={"radius": r, "height": h},
                depends_on=[sid - 1] if sid > 0 else [],
            )); sid += 1

        elif part.shape == "revolved":
            # 旋转体：交给 _build_revolve_plan 处理
            steps.append(TaskStep(
                step_id=sid, step_name=f"旋转体({label})",
                step_type=StepType.FEATURE, tool="revolve",
                params={"angle": 360},
                note="用 revolve 一步成型",
                depends_on=[sid - 1] if sid > 0 else [],
            )); sid += 1

        return steps

    def _build_cut_steps(self, part: DecomposedPart, start_id: int) -> List[TaskStep]:
        """将切除部件转换为建模步骤"""
        steps = []
        sid = start_id

        pos = part.position
        x, y, z = pos.get("x", 0), pos.get("y", 0), pos.get("z", 0)

        if part.shape == "cylinder":
            # 孔：画圆 + extrude_cut
            steps.append(TaskStep(
                step_id=sid, step_name=f"创建草图(打孔)",
                step_type=StepType.SKETCH, tool="create_sketch_on_plane",
                params={}, depends_on=[sid - 1] if sid > 0 else [],
            )); sid += 1

            r = part.dimensions.get("radius", 5)
            steps.append(TaskStep(
                step_id=sid, step_name=f"画孔({part.name})",
                step_type=StepType.SKETCH, tool="draw_closed_circle",
                params={"x": x, "y": y, "radius": r},
                depends_on=[sid - 1],
            )); sid += 1

            steps.append(TaskStep(
                step_id=sid, step_name="关闭草图",
                step_type=StepType.SKETCH, tool="close_sketch",
                params={}, depends_on=[sid - 1],
            )); sid += 1

            d = part.dimensions.get("depth", 20)
            steps.append(TaskStep(
                step_id=sid, step_name=f"切除({part.name})",
                step_type=StepType.FEATURE, tool="extrude_cut",
                params={"length": d},
                depends_on=[sid - 1],
            )); sid += 1

        elif part.shape == "block":
            # 槽：画矩形 + extrude_cut
            steps.append(TaskStep(
                step_id=sid, step_name=f"创建草图(开槽)",
                step_type=StepType.SKETCH, tool="create_sketch_on_plane",
                params={}, depends_on=[sid - 1] if sid > 0 else [],
            )); sid += 1

            w = part.dimensions.get("width", 20)
            h = part.dimensions.get("height", 5)
            steps.append(TaskStep(
                step_id=sid, step_name=f"画槽({part.name})",
                step_type=StepType.SKETCH, tool="draw_rectangle",
                params={"x": x - w/2, "y": y - h/2, "width": w, "height": h},
                depends_on=[sid - 1],
            )); sid += 1

            steps.append(TaskStep(
                step_id=sid, step_name="关闭草图",
                step_type=StepType.SKETCH, tool="close_sketch",
                params={}, depends_on=[sid - 1],
            )); sid += 1

            d = part.dimensions.get("depth", 5)
            steps.append(TaskStep(
                step_id=sid, step_name=f"切除({part.name})",
                step_type=StepType.FEATURE, tool="extrude_cut",
                params={"length": d},
                depends_on=[sid - 1],
            )); sid += 1

        return steps

    def _fallback_to_template(self, intent: Intent, plan: TaskPlan) -> None:
        """回退到简单模板"""
        if not intent.entities or not intent.entities[0].shape:
            plan.warnings.append("无法识别形状，建议 LLM 自由解析")
            return

        shape = intent.entities[0].shape
        if shape in self.TEMPLATES:
            template = self.TEMPLATES[shape]
            for i, (name, step_type, tool, default_params) in enumerate(template):
                plan.steps.append(TaskStep(
                    step_id=i + 1, step_name=name,
                    step_type=step_type, tool=tool, params=dict(default_params),
                    depends_on=[i] if i > 0 else [],
                ))

            if plan.steps[-1].tool != "save_model":
                plan.steps.append(TaskStep(
                    step_id=len(plan.steps), step_name="保存模型",
                    step_type=StepType.SAVE, tool="save_model", params={},
                    depends_on=[len(plan.steps) - 1],
                ))
        else:
            plan.warnings.append(f"未找到形状 '{shape}' 的模板，建议 LLM 解析")

    # ═══════════════════════════════════════════════════════════════
    # 其他意图类型
    # ═══════════════════════════════════════════════════════════════

    def _plan_modify(self, intent: Intent, plan: TaskPlan) -> None:
        model_state = self.memory.get_model_state()
        if model_state.feature_count == 0:
            plan.warnings.append("当前模型为空，无法修改。建议先创建模型。")
            return

        decomposition = self.decomposer.decompose(intent.description)
        plan.decomposition = decomposition
        plan.human_thought = decomposition.human_thought

        # 复用基体+细节的规划逻辑
        if decomposition.strategy in (DecompositionStrategy.BASE_THEN_CUT,
                                      DecompositionStrategy.BASE_THEN_ADD):
            self._build_base_detail_plan(decomposition, plan)
        else:
            plan.strategy = "llm_free_parse"
            plan.warnings.append("修改操作交给 LLM 解析")

    def _plan_query(self, intent: Intent, plan: TaskPlan) -> None:
        text = intent.description.lower()
        if any(kw in text for kw in ["体积", "volume"]):
            plan.steps.append(TaskStep(
                step_id=1, step_name="测量体积",
                step_type=StepType.FEATURE, tool="measure_volume", params={},
            ))
        elif any(kw in text for kw in ["质量", "mass", "多重"]):
            plan.steps.append(TaskStep(
                step_id=1, step_name="测量质量",
                step_type=StepType.FEATURE, tool="measure_mass", params={},
            ))
        elif any(kw in text for kw in ["距离", "distance"]):
            plan.steps.append(TaskStep(
                step_id=1, step_name="测量距离",
                step_type=StepType.FEATURE, tool="measure_distance",
                params={"x1": 0, "y1": 0, "z1": 0, "x2": 100, "y2": 0, "z2": 0},
            ))
        plan.strategy = "measure"

    def _plan_delete(self, intent: Intent, plan: TaskPlan) -> None:
        plan.strategy = "delete_feature"
        plan.warnings.append("删除特征需要 NX 中的特征 ID，当前仅支持标记")

    def validate_plan(self, plan: TaskPlan) -> List[str]:
        errors = []
        for step in plan.steps:
            if self.available_tools and step.tool not in self.available_tools:
                errors.append(f"步骤 {step.step_id}: 工具 '{step.tool}' 不在工具列表中")
        return errors