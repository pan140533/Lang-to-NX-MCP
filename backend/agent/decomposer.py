"""
结构分解模块

在规划之前，像人一样分析模型结构：
  - 找出哪些部分是重复的 → 用阵列/镜像
  - 找出哪些部分是对称的 → 用镜像
  - 找出哪些是旋转体 → 用 revolve
  - 找出哪些是基体 + 细节 → 先主体再打孔/倒角

核心理念：
  遇到可以镜像、旋转、偏移、阵列完成的重复性任务，
  就绝不要一个一个小部件去画。

示例：
  "三叶风扇" → 不是画3片叶子，而是画1片叶子 → 圆形阵列3个
  "四个螺栓孔" → 不是画4个孔，而是画1个孔 → 圆形阵列4个
  "阶梯" → 不是画每一级台阶，而是画1级 → 线性阵列
  "花瓶" → 不是逐层堆叠，而是画截面 → revolve
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from enum import Enum
import re


class DecompositionStrategy(Enum):
    """分解策略"""
    # 阵列类
    CIRCULAR_PATTERN = "circular_pattern"      # 圆形阵列（风扇叶片、齿轮齿、螺栓孔）
    LINEAR_PATTERN = "linear_pattern"           # 线性阵列（阶梯、栅栏、齿条）
    MIRROR = "mirror"                           # 镜像（左右对称的翅膀、支架）

    # 旋转成型
    REVOLVE = "revolve"                         # 旋转体（花瓶、碗、轮子、轴、瓶子）

    # 基体 + 细节
    BASE_THEN_CUT = "base_then_cut"             # 先建主体，再切除（打孔、挖槽）
    BASE_THEN_ADD = "base_then_add"             # 先建主体，再叠加（凸台、加强筋）

    # 多层堆叠
    STACKED = "stacked"                         # 多层堆叠（不同高度的柱子叠在一起）

    # 简单单体
    SINGLE = "single"                           # 单一形状，直接建


@dataclass
class DecomposedPart:
    """分解后的一个部件"""
    name: str                             # 部件名称：hub / blade / hole / base
    shape: str                            # 形状：cylinder / block / cone / sphere
    dimensions: Dict[str, float] = field(default_factory=dict)
    position: Dict[str, float] = field(default_factory=dict)  # 相对位置
    is_repeating: bool = False            # 是否重复部件
    repeat_count: int = 1                 # 重复次数
    repeat_strategy: str = ""             # 重复策略：circular / linear / mirror
    repeat_params: Dict[str, float] = field(default_factory=dict)  # 阵列参数
    depends_on: List[str] = field(default_factory=list)  # 依赖的部件名
    boolean_op: str = "create"            # create / subtract / unite


@dataclass
class DecompositionResult:
    """结构分解结果"""
    description: str                               # 原始描述
    strategy: DecompositionStrategy = DecompositionStrategy.SINGLE  # 主策略
    parts: List[DecomposedPart] = field(default_factory=list)
    reasoning: str = ""                            # 分解推理过程
    build_order: List[str] = field(default_factory=list)  # 建造顺序
    human_thought: str = ""                        # 人类建模思路（给 AI 看的思考过程）


class StructuralDecomposer:
    """
    结构分解器 — 在建模前像人一样分析模型结构

    思路：
      1. 读取用户描述
      2. 识别重复/对称/旋转特征
      3. 拆解为「基体 + 重复部件 + 细节」
      4. 输出人类思维过程和分解计划
    """

    # ═══════════════════════════════════════════════════════════════
    # 模式识别规则
    # ═══════════════════════════════════════════════════════════════

    # 圆形阵列模式
    CIRCULAR_PATTERNS = [
        # (正则, 部件名, 基体名, 默认数量, 识别描述)
        (r'(\d+)\s*叶|(\d+)\s*片.*叶|(\d+)\s*[瓣翅]', 'blade', 'hub', 3, '多叶片结构'),
        (r'(\d+)\s*个.*孔|(\d+)\s*孔|(\d+)\s*个.*洞', 'hole', 'base', 4, '多孔结构'),
        (r'(\d+)\s*齿|(\d+)\s*个.*齿', 'tooth', 'gear_body', 8, '齿轮结构'),
        (r'(\d+)\s*[根条].*辐|(\d+)\s*辐条', 'spoke', 'hub', 5, '辐条结构'),
        (r'(\d+)\s*个.*螺栓|(\d+)\s*螺栓', 'bolt', 'flange', 4, '螺栓分布'),
        (r'(\d+)\s*[根个].*柱子|(\d+)\s*根.*柱', 'pillar', 'base', 4, '柱子分布'),
        (r'(\d+)\s*个.*脚|(\d+)\s*脚', 'leg', 'table_top', 4, '桌脚/支脚'),
    ]

    # 线性阵列模式
    LINEAR_PATTERNS = [
        (r'(\d+)\s*[级层].*台阶|(\d+)\s*级阶梯|(\d+)\s*级.*梯', 'step', 'stair_base', 5, '阶梯结构'),
        (r'(\d+)\s*[根个].*栅栏|(\d+)\s*栅栏', 'fence_post', 'ground', 6, '栅栏结构'),
        (r'(\d+)\s*[个条].*槽|一排.*槽', 'slot', 'base', 4, '排槽结构'),
        (r'(\d+)\s*[个个].*散热片|散热片', 'fin', 'base', 8, '散热片'),
        (r'齿条|rack', 'tooth', 'rack_body', 10, '齿条'),
    ]

    # 镜像模式
    MIRROR_PATTERNS = [
        (r'左右.*对称|对称.*左右|两边.*一样', 'half', 'center', '左右对称'),
        (r'翅膀|机翼|一对.*翼', 'wing', 'body', '成对翅膀/翼'),
        (r'两边.*支架|两侧.*支撑', 'bracket', 'body', '双侧支架'),
    ]

    # 旋转体模式
    REVOLVE_PATTERNS = [
        (r'花瓶|vase|杯子|碗|瓶|罐|桶|杯', 'body', '旋转体'),
        (r'轮子|轮胎|轮毂|圆盘|飞轮', 'wheel', '旋转体'),
        (r'轴|shaft|转轴|主轴', 'shaft', '旋转体'),
        (r'球|sphere|ball', 'sphere', '球体'),
        (r'圆锥|cone|锥体|漏斗', 'cone', '旋转体'),
        (r'灯泡|灯罩|灯泡', 'bulb', '旋转体'),
    ]

    # 基体+细节模式
    BASE_DETAIL_PATTERNS = [
        (r'上面.*孔|打.*孔|钻.*孔|开.*孔', 'base', 'hole', '先建主体再打孔'),
        (r'上面.*槽|开.*槽|挖.*槽', 'base', 'slot', '先建主体再开槽'),
        (r'.*底座.*上面|.*上面.*底座', 'base', 'top', '底座+上部'),
        (r'倒角|chamfer|圆角|fillet', 'body', 'edge', '基体+边缘处理'),
    ]

    # ═══════════════════════════════════════════════════════════════
    # 中文数字映射
    # ═══════════════════════════════════════════════════════════════

    CN_NUM_MAP = {
        "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    }

    def _normalize_chinese_numerals(self, text: str) -> str:
        """将中文数字替换为阿拉伯数字，便于正则匹配"""
        result = text
        for cn, num in sorted(self.CN_NUM_MAP.items(), key=lambda x: -len(x[0])):
            result = result.replace(cn, str(num))
        return result

    def decompose(self, description: str) -> DecompositionResult:
        """
        分析描述文本，拆解模型结构

        返回 DecompositionResult，包含：
          - 分解后的部件列表
          - 建造顺序
          - 人类思维过程
        """
        # 先做中文数字标准化
        normalized = self._normalize_chinese_numerals(description)
        result = DecompositionResult(description=description)

        # 按优先级检测模式
        # 优先级：阵列 > 镜像 > 旋转体 > 基体+细节 > 单体

        # 1. 检测圆形阵列
        circular = self._detect_circular(normalized)
        if circular:
            result.strategy = DecompositionStrategy.CIRCULAR_PATTERN
            result.parts = circular
            result.reasoning = self._build_reasoning(circular, "圆形阵列")
            result.build_order = self._compute_build_order(circular)
            result.human_thought = self._think_like_human(circular, result.strategy)
            return result

        # 2. 检测线性阵列
        linear = self._detect_linear(normalized)
        if linear:
            result.strategy = DecompositionStrategy.LINEAR_PATTERN
            result.parts = linear
            result.reasoning = self._build_reasoning(linear, "线性阵列")
            result.build_order = self._compute_build_order(linear)
            result.human_thought = self._think_like_human(linear, result.strategy)
            return result

        # 3. 检测镜像
        mirror = self._detect_mirror(normalized)
        if mirror:
            result.strategy = DecompositionStrategy.MIRROR
            result.parts = mirror
            result.reasoning = self._build_reasoning(mirror, "镜像")
            result.build_order = self._compute_build_order(mirror)
            result.human_thought = self._think_like_human(mirror, result.strategy)
            return result

        # 4. 检测旋转体
        revolve = self._detect_revolve(normalized)
        if revolve:
            result.strategy = DecompositionStrategy.REVOLVE
            result.parts = revolve
            result.reasoning = self._build_reasoning(revolve, "旋转成型")
            result.build_order = self._compute_build_order(revolve)
            result.human_thought = self._think_like_human(revolve, result.strategy)
            return result

        # 5. 检测基体+细节
        base_detail = self._detect_base_detail(normalized)
        if base_detail:
            result.strategy = DecompositionStrategy.BASE_THEN_CUT
            result.parts = base_detail
            result.reasoning = self._build_reasoning(base_detail, "基体+细节")
            result.build_order = self._compute_build_order(base_detail)
            result.human_thought = self._think_like_human(base_detail, result.strategy)
            return result

        # 6. 检测多层堆叠
        stacked = self._detect_stacked(normalized)
        if stacked:
            result.strategy = DecompositionStrategy.STACKED
            result.parts = stacked
            result.reasoning = self._build_reasoning(stacked, "多层堆叠")
            result.build_order = self._compute_build_order(stacked)
            result.human_thought = self._think_like_human(stacked, result.strategy)
            return result

        # 7. 回退：简单单体
        result.strategy = DecompositionStrategy.SINGLE
        result.parts = self._detect_single(normalized)
        result.reasoning = "单一形状，直接建模"
        result.build_order = [p.name for p in result.parts]
        result.human_thought = self._think_like_human(result.parts, result.strategy)
        return result

    # ═══════════════════════════════════════════════════════════════
    # 模式检测方法
    # ═══════════════════════════════════════════════════════════════

    def _detect_circular(self, text: str) -> List[DecomposedPart]:
        """检测圆形阵列模式"""
        for pattern, part_name, base_name, default_count, desc in self.CIRCULAR_PATTERNS:
            match = re.search(pattern, text)
            if match:
                # 提取数量
                count = default_count
                for g in match.groups():
                    if g and g.isdigit():
                        count = int(g)
                        break

                parts = [
                    DecomposedPart(
                        name=base_name,
                        shape=self._infer_shape(base_name),
                        position={"x": 0, "y": 0, "z": 0},
                        is_repeating=False,
                    ),
                    DecomposedPart(
                        name=part_name,
                        shape=self._infer_shape(part_name),
                        position={"x": 30, "y": 0, "z": 0},  # 默认偏移
                        is_repeating=True,
                        repeat_count=count,
                        repeat_strategy="circular",
                        repeat_params={"count": count, "total_angle": 360},
                        depends_on=[base_name],
                    ),
                ]
                return parts

        return []

    def _detect_linear(self, text: str) -> List[DecomposedPart]:
        """检测线性阵列模式"""
        for pattern, part_name, base_name, default_count, desc in self.LINEAR_PATTERNS:
            match = re.search(pattern, text)
            if match:
                count = default_count
                for g in match.groups():
                    if g and g.isdigit():
                        count = int(g)
                        break

                parts = [
                    DecomposedPart(
                        name=base_name,
                        shape=self._infer_shape(base_name),
                        position={"x": 0, "y": 0, "z": 0},
                    ),
                    DecomposedPart(
                        name=part_name,
                        shape=self._infer_shape(part_name),
                        position={"x": 0, "y": 0, "z": 0},
                        is_repeating=True,
                        repeat_count=count,
                        repeat_strategy="linear",
                        repeat_params={"count": count, "spacing": 20, "direction": "x"},
                        depends_on=[base_name],
                    ),
                ]
                return parts

        return []

    def _detect_mirror(self, text: str) -> List[DecomposedPart]:
        """检测镜像模式"""
        for pattern, part_name, base_name, desc in self.MIRROR_PATTERNS:
            match = re.search(pattern, text)
            if match:
                parts = [
                    DecomposedPart(
                        name=base_name,
                        shape=self._infer_shape(base_name),
                        position={"x": 0, "y": 0, "z": 0},
                    ),
                    DecomposedPart(
                        name=part_name,
                        shape=self._infer_shape(part_name),
                        position={"x": 20, "y": 0, "z": 0},
                        is_repeating=True,
                        repeat_count=2,
                        repeat_strategy="mirror",
                        repeat_params={"plane": "yz"},
                        depends_on=[base_name],
                    ),
                ]
                return parts

        return []

    def _detect_revolve(self, text: str) -> List[DecomposedPart]:
        """检测旋转体"""
        for pattern, part_name, desc in self.REVOLVE_PATTERNS:
            if re.search(pattern, text):
                return [
                    DecomposedPart(
                        name=part_name,
                        shape="revolved",
                        position={"x": 0, "y": 0, "z": 0},
                        is_repeating=False,
                    )
                ]
        return []

    def _detect_base_detail(self, text: str) -> List[DecomposedPart]:
        """检测基体+细节模式"""
        parts = []

        # 先找主体
        base_shape = self._find_main_shape(text)
        parts.append(DecomposedPart(
            name="base",
            shape=base_shape,
            position={"x": 0, "y": 0, "z": 0},
        ))

        # 再找细节
        for pattern, base_name, detail_name, desc in self.BASE_DETAIL_PATTERNS:
            if re.search(pattern, text) and base_name != "base":
                continue

            if detail_name in ("hole", "slot"):
                parts.append(DecomposedPart(
                    name=detail_name,
                    shape="cylinder" if detail_name == "hole" else "block",
                    position={"x": 0, "y": 0, "z": 0},
                    is_repeating=self._has_count(text) > 1,
                    repeat_count=self._has_count(text),
                    repeat_strategy="circular" if self._has_count(text) > 1 else "",
                    repeat_params={"count": self._has_count(text), "total_angle": 360}
                    if self._has_count(text) > 1 else {},
                    boolean_op="subtract",
                    depends_on=["base"],
                ))
            elif detail_name in ("edge",):
                parts.append(DecomposedPart(
                    name=detail_name,
                    shape="chamfer" if "倒角" in text else "fillet",
                    depends_on=["base"],
                    boolean_op="modify",
                ))

        return parts if len(parts) > 1 else []

    def _detect_stacked(self, text: str) -> List[DecomposedPart]:
        """检测多层堆叠"""
        parts = []
        # 找"底座"、"上面"、"顶部"等层次关键词
        if "底座" in text or "底板" in text:
            parts.append(DecomposedPart(
                name="base",
                shape="block",
                dimensions={"width": 100, "height": 100, "depth": 10},
                position={"x": 0, "y": 0, "z": 0},
            ))
        if "上面" in text or "顶部" in text:
            h = 10 if parts else 0
            parts.append(DecomposedPart(
                name="top",
                shape=self._find_main_shape(text),
                position={"x": 0, "y": 0, "z": h},
                depends_on=["base"] if parts else [],
            ))

        return parts if len(parts) >= 2 else []

    def _detect_single(self, text: str) -> List[DecomposedPart]:
        """简单单体检测"""
        shape = self._find_main_shape(text)
        return [
            DecomposedPart(
                name=shape,
                shape=shape,
                position={"x": 0, "y": 0, "z": 0},
            )
        ]

    # ═══════════════════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════════════════

    def _find_main_shape(self, text: str) -> str:
        """从文本中找出主要形状"""
        shape_keywords = [
            ("圆柱", "cylinder"), ("方块", "block"), ("立方体", "block"),
            ("球", "sphere"), ("圆锥", "cone"), ("圆环", "torus"),
            ("板", "block"), ("管", "cylinder"), ("柱", "cylinder"),
        ]
        for kw, shape in shape_keywords:
            if kw in text:
                return shape
        return "block"  # 默认方块

    def _infer_shape(self, name: str) -> str:
        """根据部件名推断形状"""
        shape_map = {
            "hub": "cylinder", "blade": "block", "hole": "cylinder",
            "tooth": "block", "spoke": "cylinder", "bolt": "cylinder",
            "pillar": "cylinder", "leg": "cylinder", "step": "block",
            "fence_post": "cylinder", "slot": "block", "fin": "block",
            "half": "block", "wing": "block", "bracket": "block",
            "body": "block", "base": "block", "gear_body": "cylinder",
            "flange": "cylinder", "stair_base": "block", "ground": "block",
            "rack_body": "block", "center": "block", "top": "block",
            "table_top": "block", "wheel": "cylinder", "shaft": "cylinder",
            "sphere": "sphere", "cone": "cone", "bulb": "sphere",
        }
        return shape_map.get(name, "block")

    def _has_count(self, text: str) -> int:
        """检测文本中的数量"""
        match = re.search(r'(\d+)\s*[个只条根]', text)
        return int(match.group(1)) if match else 0

    def _build_reasoning(self, parts: List[DecomposedPart], strategy: str) -> str:
        """构建推理过程说明"""
        lines = [f"策略：{strategy}"]
        for p in parts:
            if p.is_repeating:
                lines.append(
                    f"  - {p.name}（{p.shape}）：重复 {p.repeat_count} 次，"
                    f"策略={p.repeat_strategy}，参数={p.repeat_params}"
                )
            else:
                lines.append(f"  - {p.name}（{p.shape}）：单次创建")
        return "\n".join(lines)

    def _compute_build_order(self, parts: List[DecomposedPart]) -> List[str]:
        """计算建造顺序（依赖关系拓扑排序）"""
        order = []
        remaining = list(parts)
        while remaining:
            for p in list(remaining):
                if all(dep in order for dep in p.depends_on):
                    order.append(p.name)
                    remaining.remove(p)
        return order

    def _think_like_human(self, parts: List[DecomposedPart],
                          strategy: DecompositionStrategy) -> str:
        """生成人类思维过程描述"""
        if strategy == DecompositionStrategy.CIRCULAR_PATTERN:
            return self._think_circular(parts)
        elif strategy == DecompositionStrategy.LINEAR_PATTERN:
            return self._think_linear(parts)
        elif strategy == DecompositionStrategy.MIRROR:
            return self._think_mirror(parts)
        elif strategy == DecompositionStrategy.REVOLVE:
            return self._think_revolve(parts)
        elif strategy == DecompositionStrategy.BASE_THEN_CUT:
            return self._think_base_detail(parts)
        elif strategy == DecompositionStrategy.STACKED:
            return self._think_stacked(parts)
        else:
            return self._think_single(parts)

    def _think_circular(self, parts: List[DecomposedPart]) -> str:
        base = next((p for p in parts if not p.is_repeating), None)
        repeating = next((p for p in parts if p.is_repeating), None)
        if not base or not repeating:
            return ""

        count = repeating.repeat_count
        return (
            f"人类思路：\n"
            f"  这个模型有 {count} 个相同的 {repeating.name} 围绕中心均匀分布。\n"
            f"  我不会傻到分别画 {count} 个 {repeating.name}。\n"
            f"  正确做法是：\n"
            f"    1. 先画中间的 {base.name}（{base.shape}）\n"
            f"    2. 再画一个 {repeating.name}（{repeating.shape}）\n"
            f"    3. 用圆形阵列把 {repeating.name} 绕中心复制 {count} 份\n"
            f"  这样只需建 2 个部件，而不是 {count + 1} 个。"
        )

    def _think_linear(self, parts: List[DecomposedPart]) -> str:
        base = next((p for p in parts if not p.is_repeating), None)
        repeating = next((p for p in parts if p.is_repeating), None)
        if not base or not repeating:
            return ""

        count = repeating.repeat_count
        return (
            f"人类思路：\n"
            f"  这个模型有 {count} 个 {repeating.name} 沿直线排列。\n"
            f"  正确做法是：\n"
            f"    1. 先画 {base.name}\n"
            f"    2. 再画一个 {repeating.name}\n"
            f"    3. 用线性阵列沿 X 方向复制 {count} 份\n"
            f"  这样只需建 2 个部件，而不是 {count + 1} 个。"
        )

    def _think_mirror(self, parts: List[DecomposedPart]) -> str:
        base = next((p for p in parts if not p.is_repeating), None)
        half = next((p for p in parts if p.is_repeating), None)
        if not base or not half:
            return ""

        return (
            f"人类思路：\n"
            f"  这个模型左右对称。\n"
            f"  正确做法是：\n"
            f"    1. 先画 {base.name}\n"
            f"    2. 画一侧的 {half.name}\n"
            f"    3. 用镜像复制到另一侧\n"
            f"  这样只需建 2 个部件，而不是画两边。"
        )

    def _think_revolve(self, parts: List[DecomposedPart]) -> str:
        return (
            f"人类思路：\n"
            f"  这是一个旋转对称体（花瓶/碗/轴/轮子）。\n"
            f"  我不会去逐层堆叠——那样既慢又不精确。\n"
            f"  正确做法是：\n"
            f"    1. 画出截面轮廓（半剖面）\n"
            f"    2. 用 revolve 绕中心轴旋转 360°\n"
            f"  这样一步到位，自动生成光滑的旋转体。"
        )

    def _think_base_detail(self, parts: List[DecomposedPart]) -> str:
        base = next((p for p in parts if p.boolean_op == "create"), None)
        details = [p for p in parts if p.boolean_op in ("subtract", "modify")]
        if not base:
            return ""

        detail_names = ", ".join(d.name for d in details)
        return (
            f"人类思路：\n"
            f"  这是「基体 + 细节」结构。\n"
            f"  正确做法是：\n"
            f"    1. 先建主体 {base.name}（{base.shape}）\n"
            f"    2. 再处理细节：{detail_names}\n"
            f"  先粗后细，先大后小——这是建模的基本法则。"
        )

    def _think_stacked(self, parts: List[DecomposedPart]) -> str:
        return (
            f"人类思路：\n"
            f"  这是多层结构，从下往上建。\n"
            f"  正确做法是按 Z 轴从低到高依次创建每一层。"
        )

    def _think_single(self, parts: List[DecomposedPart]) -> str:
        if not parts:
            return "无法识别形状，交给 LLM 自由解析。"
        return (
            f"人类思路：\n"
            f"  这是一个简单的单体模型（{parts[0].shape}）。\n"
            f"  直接创建即可，不需要分解。"
        )


# 便捷函数
def decompose_structure(description: str) -> DecompositionResult:
    """快速分解结构"""
    decomposer = StructuralDecomposer()
    return decomposer.decompose(description)