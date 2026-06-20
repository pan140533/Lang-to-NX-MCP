"""
上下文记忆模块

让 AI 记住：
  - 当前零件有什么特征（ModelState）
  - 用户在关注什么（Focus）
  - 之前做过什么操作（History）
  - 建模到了哪个阶段（Phase）

设计原则：
  - 每次对话都携带当前状态，AI 不需要「猜」
  - 状态变化后立即更新，保证一致性
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ModelPhase(Enum):
    """建模阶段"""
    EMPTY = "empty"           # 空白文档
    SKETCHING = "sketching"   # 正在画草图
    FEATURE_CREATING = "feature_creating"  # 正在创建特征
    DETAILING = "detailing"   # 细节处理（倒角/圆角/孔）
    COMPLETE = "complete"     # 模型完成


@dataclass
class MemoryEntry:
    """一条记忆记录"""
    timestamp: str
    action: str               # 做了什么：create_sketch / extrude / chamfer
    description: str          # 人类可读描述
    feature_id: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    result: str = "success"   # success / failed


@dataclass
class ModelState:
    """当前模型状态 — 让 AI 知道「模型现在长什么样」"""
    feature_count: int = 0
    features: List[Dict[str, Any]] = field(default_factory=list)
    bounding_box: Optional[Dict[str, float]] = None  # {x_min, x_max, y_min, y_max, z_min, z_max}
    total_volume: Optional[float] = None
    last_sketch_plane: str = "XY"  # 最后使用的草图平面
    phase: ModelPhase = ModelPhase.EMPTY

    def summary(self) -> str:
        """生成人类可读的状态摘要"""
        if self.feature_count == 0:
            return "当前模型：空白（无特征）"

        lines = [f"当前模型：{self.feature_count} 个特征"]
        for f in self.features[-5:]:  # 最近5个
            shape = f.get("shape", "未知")
            pos = f.get("position", {})
            x, y, z = pos.get("x", 0), pos.get("y", 0), pos.get("z", 0)
            lines.append(f"  - {shape} @ ({x}, {y}, {z})")
        if len(self.features) > 5:
            lines.append(f"  ... 还有 {len(self.features) - 5} 个特征")
        return "\n".join(lines)

    def to_context_dict(self) -> Dict[str, Any]:
        """转为可传给 LLM 的上下文字典"""
        return {
            "feature_count": self.feature_count,
            "features": self.features,
            "phase": self.phase.value,
            "last_sketch_plane": self.last_sketch_plane,
            "summary": self.summary(),
        }


@dataclass
class Focus:
    """当前关注焦点 — AI 正在关注哪个特征/区域"""
    feature_id: Optional[str] = None
    feature_name: str = ""
    position: Dict[str, float] = field(default_factory=dict)
    reason: str = ""  # 为什么关注这个

    def is_set(self) -> bool:
        return self.feature_id is not None


class ContextMemory:
    """
    上下文记忆管理器

    用法：
      mem = ContextMemory()
      mem.record("创建了圆柱", "cylinder", {"diameter": 50, "height": 100})
      mem.focus_on("feat_001", "圆柱", {"x": 0, "y": 0, "z": 0}, "用户刚创建")
      context = mem.get_context_for_llm()  # 给 LLM 看的上下文
    """

    def __init__(self, max_history: int = 20):
        self._history: List[MemoryEntry] = []
        self._model_state = ModelState()
        self._focus = Focus()
        self._max_history = max_history
        self._user_messages: List[str] = []  # 用户说过的话

    # ── 记录操作 ──

    def record(self, description: str, action: str,
               feature_id: Optional[str] = None,
               params: Optional[Dict] = None,
               result: str = "success") -> None:
        """记录一次操作"""
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            description=description,
            feature_id=feature_id,
            params=params or {},
            result=result,
        )
        self._history.append(entry)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def record_user_message(self, text: str) -> None:
        """记录用户说的话"""
        self._user_messages.append(text)
        if len(self._user_messages) > 10:
            self._user_messages = self._user_messages[-10:]

    # ── 模型状态 ──

    def update_model_state(self, features: List[Dict[str, Any]]) -> None:
        """更新模型状态"""
        self._model_state.features = features
        self._model_state.feature_count = len(features)

        # 推断阶段
        if len(features) == 0:
            self._model_state.phase = ModelPhase.EMPTY
        elif any(f.get("shape") in ("倒角", "圆角", "孔", "槽") for f in features[-3:]):
            self._model_state.phase = ModelPhase.DETAILING
        elif len(features) > 0:
            self._model_state.phase = ModelPhase.FEATURE_CREATING

        # 更新边界框
        if features:
            xs, ys, zs = [], [], []
            for f in features:
                pos = f.get("position", {})
                dims = f.get("dimensions", {})
                x, y, z = pos.get("x", 0), pos.get("y", 0), pos.get("z", 0)
                xs.append(x); ys.append(y); zs.append(z)
                # 粗估：加上尺寸
                w = dims.get("width", dims.get("length", dims.get("diameter", 50)))
                h = dims.get("height", dims.get("diameter", 50))
                d = dims.get("depth", dims.get("width", 50))
                xs.append(x + w / 2); ys.append(y + d / 2); zs.append(z + h / 2)
                xs.append(x - w / 2); ys.append(y - d / 2); zs.append(z)
            self._model_state.bounding_box = {
                "x_min": min(xs), "x_max": max(xs),
                "y_min": min(ys), "y_max": max(ys),
                "z_min": min(zs), "z_max": max(zs),
            }

    # ── 关注焦点 ──

    def focus_on(self, feature_id: str, name: str,
                 position: Dict[str, float], reason: str = "") -> None:
        """设置关注焦点"""
        self._focus = Focus(
            feature_id=feature_id,
            feature_name=name,
            position=position,
            reason=reason,
        )

    def clear_focus(self) -> None:
        """清除焦点"""
        self._focus = Focus()

    # ── 上下文生成 ──

    def get_context_for_llm(self) -> str:
        """
        生成给 LLM 看的上下文摘要
        让 AI 知道「当前是什么情况」
        """
        parts = []

        # 模型状态
        parts.append("【当前模型状态】")
        parts.append(self._model_state.summary())

        # 关注焦点
        if self._focus.is_set():
            parts.append("")
            parts.append(f"【当前关注】{self._focus.feature_name} ({self._focus.reason})")

        # 最近操作
        if self._history:
            parts.append("")
            parts.append("【最近操作】")
            for entry in self._history[-3:]:
                parts.append(f"  - [{entry.result}] {entry.description}")

        # 用户历史
        if self._user_messages:
            parts.append("")
            parts.append("【用户历史消息】")
            for msg in self._user_messages[-3:]:
                parts.append(f"  - {msg}")

        return "\n".join(parts)

    def get_next_action_suggestions(self) -> List[str]:
        """
        根据当前状态，给 AI 建议下一步可以做什么
        """
        suggestions = []

        if self._model_state.phase == ModelPhase.EMPTY:
            suggestions.append("创建第一个特征（圆柱/方块/球体）")
            suggestions.append("创建草图开始手绘")

        elif self._model_state.phase == ModelPhase.FEATURE_CREATING:
            suggestions.append("添加更多特征")
            suggestions.append("对当前特征进行倒角/圆角处理")
            suggestions.append("在已有特征上打孔/开槽")

        elif self._model_state.phase == ModelPhase.DETAILING:
            suggestions.append("保存模型")
            suggestions.append("测量体积/质量")
            suggestions.append("导出为 STL 格式")

        elif self._model_state.phase == ModelPhase.COMPLETE:
            suggestions.append("保存模型")
            suggestions.append("开始新零件")
            suggestions.append("导出为其他格式")

        return suggestions

    # ── 查询 ──

    def get_last_feature(self) -> Optional[Dict[str, Any]]:
        """获取最近创建的特征"""
        if self._model_state.features:
            return self._model_state.features[-1]
        return None

    def get_feature_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """按名称查找特征"""
        for f in self._model_state.features:
            if f.get("name") == name or f.get("id") == name:
                return f
        return None

    def get_model_state(self) -> ModelState:
        return self._model_state

    def get_focus(self) -> Focus:
        return self._focus

    def get_history(self, n: int = 5) -> List[MemoryEntry]:
        return self._history[-n:]