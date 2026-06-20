"""
意图识别模块

分析用户输入，判断意图类型、提取关键实体、确定建模策略。

意图类型：
  CREATE   — 创建新模型（"画一个圆柱"）
  MODIFY   — 修改已有模型（"在这个圆柱上打孔"）
  QUERY    — 查询信息（"体积是多少"）
  DELETE   — 删除特征（"删掉那个孔"）
  ANALYZE  — 分析请求（"这个零件能承受多大压力"）
  CHAT     — 闲聊/帮助（"你能做什么"）
"""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict


class IntentType(Enum):
    CREATE = "create"
    MODIFY = "modify"
    QUERY = "query"
    DELETE = "delete"
    ANALYZE = "analyze"
    CHAT = "chat"


@dataclass
class EntityInfo:
    """从用户输入中提取的实体信息"""
    shape: Optional[str] = None       # 形状类型：圆柱/方块/球/圆锥/孔/槽/...
    dimensions: Dict[str, float] = field(default_factory=dict)  # 尺寸：{直径:50, 高度:100}
    position: Dict[str, float] = field(default_factory=dict)    # 位置：{x:0, y:0, z:50}
    reference: Optional[str] = None   # 引用的已有特征：在XX上、在XX旁边
    material: Optional[str] = None    # 材料信息
    quantity: Optional[int] = None    # 数量：4个孔、6个螺栓
    arrangement: Optional[str] = None # 排列方式：圆形阵列、线性阵列


@dataclass
class Intent:
    """意图分析结果"""
    type: IntentType
    description: str                    # 原始用户输入
    entities: List[EntityInfo] = field(default_factory=list)
    confidence: float = 0.0             # 置信度 0-1
    modeling_strategy: str = ""         # 推荐建模策略
    needs_clarification: bool = False   # 是否需要追问
    clarification_question: str = ""    # 追问内容
    next_action_hint: str = ""          # 下一步提示（给 AI 自己看的）


class IntentRecognition:
    """意图识别器 — 分析用户输入，告诉 AI「用户在说什么」"""

    # 关键词 → 意图类型映射
    CREATE_KEYWORDS = [
        "创建", "画", "做", "造", "生成", "建", "新建", "给我",
        "做一个", "画一个", "建一个", "生成一个", "来一个",
        "create", "make", "build", "draw",
    ]
    MODIFY_KEYWORDS = [
        "修改", "改", "添加", "加", "打孔", "开槽", "倒角", "圆角",
        "打", "挖", "切", "削", "阵列", "镜像", "偏移", "移动",
        "modify", "add", "cut", "chamfer", "fillet", "hole",
    ]
    QUERY_KEYWORDS = [
        "多少", "多大", "多重", "什么", "查询", "测量", "体积",
        "面积", "质量", "距离", "尺寸", "属性",
        "what", "how", "measure", "volume", "mass", "distance",
    ]
    DELETE_KEYWORDS = [
        "删除", "去掉", "移除", "删掉", "不要",
        "delete", "remove",
    ]
    ANALYZE_KEYWORDS = [
        "分析", "仿真", "受力", "强度", "应力", "热", "流体",
        "analyze", "simulate", "stress", "thermal",
    ]
    CHAT_KEYWORDS = [
        "帮助", "help", "你能做什么", "功能", "怎么用",
        "你好", "谢谢",
    ]

    # 形状关键词
    SHAPE_PATTERNS = {
        "圆柱": ["圆柱", "柱子", "圆柱体", "cylinder"],
        "方块": ["方块", "立方体", "块", "长方体", "盒子", "block", "box", "cube"],
        "球": ["球", "球体", "sphere", "ball"],
        "圆锥": ["圆锥", "锥体", "cone"],
        "圆环": ["圆环", "环", "甜甜圈", "torus", "ring"],
        "孔": ["孔", "洞", "hole", "钻孔"],
        "槽": ["槽", "沟槽", "slot", "groove"],
        "凸台": ["凸台", "boss", "凸起"],
        "管": ["管", "管道", "pipe", "tube"],
        "板": ["板", "平板", "plate"],
    }

    def __init__(self):
        pass

    def recognize(self, text: str, context: Optional[Dict] = None) -> Intent:
        """
        识别用户意图

        参数:
          text: 用户输入文本
          context: 当前会话上下文（可选，用于判断 MODIFY 等）

        返回:
          Intent 对象，包含意图类型、实体、策略等
        """
        text_lower = text.lower().strip()

        # 1. 确定意图类型
        intent_type = self._classify_intent(text_lower, context)

        # 2. 提取实体
        entities = self._extract_entities(text, intent_type)

        # 3. 确定建模策略
        strategy = self._determine_strategy(text, entities, intent_type)

        # 4. 计算置信度
        confidence = self._calc_confidence(intent_type, entities)

        # 5. 判断是否需要追问
        needs_clarification, question = self._check_clarification(intent_type, entities)

        # 6. 生成下一步提示
        next_hint = self._generate_next_hint(intent_type, entities, strategy)

        return Intent(
            type=intent_type,
            description=text,
            entities=entities,
            confidence=confidence,
            modeling_strategy=strategy,
            needs_clarification=needs_clarification,
            clarification_question=question,
            next_action_hint=next_hint,
        )

    def _classify_intent(self, text: str, context: Optional[Dict] = None) -> IntentType:
        """分类意图类型"""
        # 有上下文且提到已存在特征 → MODIFY
        if context and context.get("features"):
            for kw in self.MODIFY_KEYWORDS:
                if kw in text:
                    return IntentType.MODIFY

        scores = {
            IntentType.CREATE: self._score_keywords(text, self.CREATE_KEYWORDS),
            IntentType.MODIFY: self._score_keywords(text, self.MODIFY_KEYWORDS),
            IntentType.QUERY: self._score_keywords(text, self.QUERY_KEYWORDS),
            IntentType.DELETE: self._score_keywords(text, self.DELETE_KEYWORDS),
            IntentType.ANALYZE: self._score_keywords(text, self.ANALYZE_KEYWORDS),
            IntentType.CHAT: self._score_keywords(text, self.CHAT_KEYWORDS),
        }
        return max(scores, key=scores.get)

    def _score_keywords(self, text: str, keywords: List[str]) -> int:
        return sum(1 for kw in keywords if kw in text)

    def _extract_entities(self, text: str, intent_type: IntentType) -> List[EntityInfo]:
        """从文本中提取实体信息"""
        entities = []

        if intent_type in (IntentType.CREATE, IntentType.MODIFY):
            entity = EntityInfo()

            # 识别形状
            for shape_name, patterns in self.SHAPE_PATTERNS.items():
                for pat in patterns:
                    if pat in text:
                        entity.shape = shape_name
                        break
                if entity.shape:
                    break

            # 提取尺寸（数字 + 单位）
            entity.dimensions = self._extract_dimensions(text)

            # 提取数量
            entity.quantity = self._extract_quantity(text)

            # 提取排列方式
            if "阵列" in text or "pattern" in text.lower():
                entity.arrangement = "圆形阵列" if "圆" in text else "线性阵列"

            entities.append(entity)

        return entities

    def _extract_dimensions(self, text: str) -> Dict[str, float]:
        """从文本中提取尺寸参数"""
        import re
        dims = {}

        # 匹配模式：数字 + 可选单位
        patterns = [
            (r'直径\s*(\d+(?:\.\d+)?)', 'diameter'),
            (r'(\d+(?:\.\d+)?)\s*毫米.*直径', 'diameter'),
            (r'半径\s*(\d+(?:\.\d+)?)', 'radius'),
            (r'高度\s*(\d+(?:\.\d+)?)', 'height'),
            (r'长度\s*(\d+(?:\.\d+)?)', 'length'),
            (r'宽度\s*(\d+(?:\.\d+)?)', 'width'),
            (r'深度\s*(\d+(?:\.\d+)?)', 'depth'),
            (r'厚度\s*(\d+(?:\.\d+)?)', 'thickness'),
            (r'距离\s*(\d+(?:\.\d+)?)', 'distance'),
            (r'(\d+(?:\.\d+)?)\s*mm', None),  # 通用数字
        ]

        for pattern, key in patterns:
            match = re.search(pattern, text)
            if match:
                val = float(match.group(1))
                if key:
                    dims[key] = val
                elif len(dims) == 0:
                    dims['size'] = val

        return dims

    def _extract_quantity(self, text: str) -> Optional[int]:
        """提取数量"""
        import re
        match = re.search(r'(\d+)\s*[个只条根]', text)
        if match:
            return int(match.group(1))
        return None

    def _determine_strategy(self, text: str, entities: List[EntityInfo],
                            intent_type: IntentType) -> str:
        """确定建模策略"""
        if intent_type == IntentType.CREATE:
            if not entities or not entities[0].shape:
                return "llm_parse"  # 让 LLM 自由解析

            shape = entities[0].shape
            rotational = ["球", "圆锥", "碗", "杯", "花瓶", "轴", "轮子", "圆盘"]
            if any(r in text for r in rotational):
                return "revolve"  # 旋转成型
            if shape in ("圆柱", "管"):
                return "extrude_circle"  # 圆拉伸
            if shape in ("方块", "板"):
                return "extrude_rectangle"  # 矩形拉伸
            if shape in ("孔", "槽"):
                return "extrude_cut"  # 切除

        if intent_type == IntentType.MODIFY:
            return "modify_existing"

        return "llm_parse"

    def _calc_confidence(self, intent_type: IntentType,
                         entities: List[EntityInfo]) -> float:
        """计算置信度"""
        score = 0.5  # 基础分

        if intent_type == IntentType.CREATE:
            if entities and entities[0].shape:
                score += 0.3
            if entities and entities[0].dimensions:
                score += 0.2

        return min(score, 1.0)

    def _check_clarification(self, intent_type: IntentType,
                             entities: List[EntityInfo]) -> tuple:
        """检查是否需要追问用户"""
        if intent_type == IntentType.CREATE:
            if not entities or not entities[0].shape:
                return True, "请问您想创建什么形状的模型？比如圆柱、方块、球体？"
            if not entities[0].dimensions:
                return True, f"请问这个{entities[0].shape}的尺寸是多少？比如直径和高度。"

        if intent_type == IntentType.MODIFY:
            if not entities:
                return True, "请问您想对当前模型做什么修改？"

        return False, ""

    def _generate_next_hint(self, intent_type: IntentType,
                            entities: List[EntityInfo], strategy: str) -> str:
        """生成下一步提示（给 AI 自己看的）"""
        hints = {
            IntentType.CREATE: "→ 下一步：调用 TaskPlanner 将意图拆解为建模步骤",
            IntentType.MODIFY: "→ 下一步：从 Memory 获取当前模型状态，定位要修改的特征",
            IntentType.QUERY: "→ 下一步：调用 NX 测量 API 获取数据",
            IntentType.DELETE: "→ 下一步：从 Memory 找到特征 ID，执行删除",
            IntentType.ANALYZE: "→ 下一步：调用分析模块（暂未实现）",
            IntentType.CHAT: "→ 下一步：直接回复用户，无需建模",
        }
        return hints.get(intent_type, "")


# 便捷函数
def recognize_intent(text: str, context: Optional[Dict] = None) -> Intent:
    """快速识别意图"""
    recognizer = IntentRecognition()
    return recognizer.recognize(text, context)