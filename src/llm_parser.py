"""
LLM 解析模块
负责将自然语言转换为建模步骤序列（JSON）。
支持单步（简单形状）和多步（复杂结构如鸟居）。
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import os


# ── 单步模型（原有）──

class BlockDimensions(BaseModel):
    length: float; width: float; height: float

class CylinderDimensions(BaseModel):
    diameter: float; height: float

class ConeDimensions(BaseModel):
    base_diameter: float; top_diameter: float; height: float

class SphereDimensions(BaseModel):
    diameter: float

class Position(BaseModel):
    type: str = "absolute"
    x: Optional[float] = 0
    y: Optional[float] = 0
    z: Optional[float] = 0
    reference_feature_id: Optional[str] = None
    location: Optional[str] = None
    offset: Optional[Dict[str, float]] = None

class FeatureCommand(BaseModel):
    command_type: str  # "add_feature", "new_part", "query", "delete"
    feature_type: Optional[str] = None
    block: Optional[BlockDimensions] = None
    cylinder: Optional[CylinderDimensions] = None
    cone: Optional[ConeDimensions] = None
    sphere: Optional[SphereDimensions] = None
    position: Optional[Position] = None
    boolean_op: str = "create"
    feature_id_to_delete: Optional[str] = None


# ── 多步规划模型（新增）──

class ModelingStep(BaseModel):
    """一步建模操作"""
    step_name: str  # 描述性名称，如 "左底座"
    tool: str       # 工具名：draw_circle / draw_rectangle / extrude / extrude_from / revolve 等
    params: Dict    # 参数

class ModelingPlan(BaseModel):
    """完整的建模规划"""
    description: str  # 用户输入的原始描述
    steps: List[ModelingStep]


# ── 可用工具清单（给LLM参考）──

TOOL_DESCRIPTIONS = """
可用工具列表（按功能分类）：

══ 基础操作 ══
- new_document — 创建新文件（每次第一步）
- create_sketch_on_plane — 创建XY平面草图
- close_sketch — 关闭当前草图

══ 画图工具 ══
- draw_closed_circle(x, y, radius) — 画圆
- draw_rectangle(x, y, width, height) — 画矩形
- draw_line(x1, y1, x2, y2) — 画直线

══ 拉伸（把2D草图变成3D）══
- extrude(length) — 从 Z=0 向上拉伸
- extrude_from(start, length) — 从指定高度拉伸

══ 旋转（适合圆形/对称零件）══
- revolve(angle=360) — 把草图绕Z轴旋转成实体
  适用于：花瓶、轮子、圆盘、轴类、碗、杯子等旋转对称的零件

══ 切除（在已有实体上开孔/挖槽）══
- extrude_cut(length) — 切除材料
  适用于：开孔、挖槽、去除不需要的部分

══ 边缘处理 ══
- chamfer(length) — 倒角（削掉棱边）
- fillet(radius) — 圆角（把棱边磨圆）

══ 高级形状 ══
- cone(radius, height) — 圆锥
- sphere(radius) — 球体

坐标系统：XY为水平面，Z为垂直方向（高度）。
X=左右宽度，Y=前后深度，Z=上下高度。

建模策略建议：
1. 旋转对称零件（花瓶、碗、杯、轮子、轴）→ 画截面轮廓 → revolve
2. 开孔/挖槽 → 先建主体 → 再画要切掉的形状 → extrude_cut
3. 多个部件 → 分别画出各个部件，用 extrude_from 控制位置
4. 边缘美化 → chamfer(倒角) / fillet(圆角) 最后加

注意：不是所有模型都需要底座！只有实际需要底座的才加。
"""


class LLMParser:
    """LLM 解析器"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.llm = ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=model,
            temperature=0.7,
        )
        self.parser = PydanticOutputParser(pydantic_object=FeatureCommand)

    def parse_command(self, description: str, context: Optional[List[dict]] = None) -> FeatureCommand:
        """解析用户指令（单步模式）"""
        context_str = ""
        if context:
            context_str = "\n当前零件已有特征:\n" + "\n".join(
                [f"  - {f['feature_id']}: {f['type']} ({f['parameters']})" for f in context]
            )

        fmt_instructions = self.parser.get_format_instructions()
        template = """你是CAD建模专家。将用户的自然语言描述解析为建模指令。

{tool_desc}

请分析用户的描述，确定：
1. command_type: "add_feature" / "new_part" / "query"
2. feature_type: "block" / "cylinder" / "cone" / "sphere" / None
3. 对应的尺寸参数
4. 位置（默认中心在原点）
5. 布尔操作

{fmt}

注意：如果用户描述的复杂结构（如"鸟居"、"房子"、"桌子"），将 command_type 设为 "add_feature"，feature_type 设为无法识别的类型就返回 None。"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", template),
            ("user", "描述: {description}{context}"),
        ])

        messages = prompt.format_messages(
            tool_desc=TOOL_DESCRIPTIONS,
            fmt=fmt_instructions,
            description=description,
            context=context_str
        )
        output = self.llm.invoke(messages)
        return self.parser.parse(output.content)

    def parse_plan(self, description: str) -> ModelingPlan:
        """解析复杂描述为多步建模规划"""
        template = """你是CAD建模专家。用户描述了一个需要多步制作的模型。
请将模型拆解为一系列建模步骤，按正确的顺序排列。

{tool_desc}

请返回JSON格式（不用Markdown代码块）：
{json_example}

思考步骤（重要）：
1. 这个模型由哪些部件组成？识别每个部件的形状特征
2. 如果部件是旋转对称的（圆形、对称、弧形）→ 用 revolve 而不是 extrude！
3. 如果需要在主体上去除材料 → 用 extrude_cut
4. 每个部件在什么位置（X=宽度、Y=深度、Z=高度）？
5. 部件之间有什么关系（谁在谁上面）？用 extrude_from 控制起始高度
6. 按从下到上的顺序排列步骤

工具选择指南：
- 旋转对称零件（花瓶、球体、轮子、轴、碗、杯子）：用 revolve
- 方形的零件（盒子、桌子、底座）：用 draw_rectangle + extrude
- 需要开孔/挖槽：先建主体，再画要切掉的形状，最后 extrude_cut
- 圆形截面但直线拉伸（圆柱、柱子）：用 draw_closed_circle + extrude

重要：返回纯JSON，不要markdown格式。"""
        json_example = '{\n  "description": "做一个杯子",\n  "steps": [\n    {"step_name": "杯体轮廓", "tool": "draw_rectangle", "params": {"x": 0, "y": 0, "width": 40, "height": 80}},\n    {"step_name": "杯体轮廓", "tool": "close_sketch", "params": {}},\n    {"step_name": "杯体", "tool": "revolve", "params": {"angle": 360}},\n    {"step_name": "掏空", "tool": "create_sketch_on_plane", "params": {}},\n    {"step_name": "掏空", "tool": "draw_closed_circle", "params": {"x": 0, "y": 0, "radius": 30}},\n    {"step_name": "掏空", "tool": "close_sketch", "params": {}},\n    {"step_name": "掏空", "tool": "extrude_cut", "params": {"length": 70}}\n  ]\n}'

        prompt = ChatPromptTemplate.from_messages([
            ("system", template),
            ("user", "描述: {description}"),
        ])

        messages = prompt.format_messages(
            tool_desc=TOOL_DESCRIPTIONS,
            json_example=json_example,
            description=description
        )
        output = self.llm.invoke(messages)

        # 解析JSON
        text = output.content.strip()
        # 去掉可能的markdown代码头尾
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])

        try:
            data = json.loads(text)
            return ModelingPlan(description=data.get("description", description),
                               steps=[ModelingStep(**s) for s in data.get("steps", [])])
        except Exception as e:
            # 如果解析失败，返回最简单的plan
            return ModelingPlan(description=description, steps=[
                ModelingStep(step_name="块", tool="draw_rectangle", params={"x": 0, "y": 0, "width": 100, "height": 100}),
                ModelingStep(step_name="块", tool="close_sketch", params={}),
                ModelingStep(step_name="块", tool="extrude", params={"length": 100}),
            ])


# 保存训练数据
def save_training_data(description: str, plan: ModelingPlan):
    """将用户的描述和生成的规划保存为训练数据"""
    import os
    from datetime import datetime

    data_dir = os.path.join(os.path.dirname(__file__), "..", "training_data")
    os.makedirs(data_dir, exist_ok=True)

    filename = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(data_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "description": description,
            "plan": plan.model_dump(),
            "timestamp": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)

    return filepath
