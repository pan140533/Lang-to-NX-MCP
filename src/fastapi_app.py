from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import uuid
import json
from pydantic import BaseModel
from typing import Optional, Tuple
from session_manager import SessionManager, FeatureData
from llm_parser import LLMParser
from geometry_utils import BoundingBox, calculate_position
from log_system import log_operation, log_error, log_task_start, log_task_end
import config  # 导入配置文件

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化会话管理器
session_manager = SessionManager(storage_dir=config.SESSION_DIR)

# LLM 解析器（延迟初始化）
llm_parser = None

def get_llm_parser():
    """获取 LLM 解析器实例（延迟初始化）"""
    global llm_parser
    if llm_parser is None:
        llm_parser = LLMParser(
            api_key=config.LLM_CONFIG["api_key"],
            base_url=config.LLM_CONFIG["base_url"],
            model=config.LLM_CONFIG["model"]
        )
    return llm_parser


class CommandRequest(BaseModel):
    """指令请求"""
    session_id: Optional[str] = None
    description: str


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    part_file: Optional[str] = None
    features: list
    message: str


# 配置（从 config.py 导入）
OUTPUT_DIR = config.OUTPUT_DIR



# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.post("/api/session/new")
def create_new_session():
    """创建新的建模会话"""
    try:
        session = session_manager.create_session()
        return {
            "status": "success",
            "session_id": session.session_id,
            "message": "新会话已创建"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/command")
def execute_command(request: CommandRequest):
    """执行建模指令（支持会话）"""
    log_task_start("execute_command", {"description": request.description[:80]})
    try:
        # 如果没有 session_id，创建新会话
        if not request.session_id:
            session = session_manager.create_session()
            session_id = session.session_id
        else:
            session_id = request.session_id
            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="会话不存在")

        # 获取当前会话的特征列表（用于上下文）
        features = session_manager.get_features(session_id)
        context = [
            {
                "feature_id": f.feature_id,
                "type": f.type,
                "parameters": f.parameters
            }
            for f in features
        ]
        
        # 使用 LLM 解析指令（延迟初始化）
        parser = get_llm_parser()
        command = parser.parse_command(request.description, context)

        print(f"[DEBUG] 解析后的指令: {command}")

        # 如果无法识别为简单形状，尝试多步规划
        if command.command_type == "add_feature" and not command.feature_type:
            print(f"[DEBUG] 尝试多步规划...")
            plan = parser.parse_plan(request.description)
            print(f"[DEBUG] 规划步骤数: {len(plan.steps)}")

            # 保存训练数据
            try:
                from llm_parser import save_training_data
                save_training_data(request.description, plan)
            except Exception as e:
                print(f"[DEBUG] 保存训练数据失败: {e}")

            # 执行规划
            result = execute_plan(session_id, plan)
            return result

        # 处理不同类型的指令
        if command.command_type == "new_part":
            session_manager.clear_session(session_id)
            return {
                "status": "success",
                "session_id": session_id,
                "message": "已开始新零件",
                "features": []
            }

        elif command.command_type == "query":
            features = session_manager.get_features(session_id)
            return {
                "status": "success",
                "session_id": session_id,
                "features": [f.model_dump() for f in features],
                "message": f"当前有 {len(features)} 个特征"
            }

        elif command.command_type == "add_feature":
            if not command.feature_type:
                return {"status": "error", "message": "无法识别模型类型"}
            result = add_feature_to_session(session_id, command)
            return result
        
        else:
            return {
                "status": "error",
                "message": f"不支持的指令类型: {command.command_type}"
            }
            
        return result

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        log_error("execute_command", str(e), {"traceback": error_detail[:500]})
        return {
            "status": "error",
            "message": f"执行失败: {str(e)}",
            "detail": error_detail
        }


def plan_steps_to_features(plan_steps: list) -> list:
    """将规划步骤转换为前端 Three.js 能渲染的特征列表"""
    features = []
    current = {}  # 当前正在构建的特征

    for step in plan_steps:
        t = step.tool
        p = step.params

        if t == "draw_rectangle":
            current = {"type": "block", "x": p.get("x", 0), "y": p.get("y", 0),
                       "width": p.get("width", 100), "height": p.get("height", 60)}
        elif t == "draw_closed_circle":
            current = {"type": "cylinder", "x": p.get("x", 0), "y": p.get("y", 0),
                       "radius": p.get("radius", 25)}
        elif t == "revolve":
            if current and current["type"] == "block":
                # 矩形旋转 → 圆柱/圆盘
                r = max(current["width"], current.get("height", current["width"])) / 2
                h = current["height"]
                features.append({
                    "feature_id": f"feat_{len(features)}",
                    "type": "cylinder",
                    "parameters": {"diameter": r * 2, "height": h},
                    "position": {"calculated_coords": {"x": 0, "y": 0, "z": 0}},
                    "boolean_op": "create", "order": len(features)
                })
                current = {}
            elif current and current["type"] == "cylinder":
                r = current["radius"]
                features.append({
                    "feature_id": f"feat_{len(features)}",
                    "type": "cylinder",
                    "parameters": {"diameter": r * 2, "height": r * 2},
                    "position": {"calculated_coords": {"x": 0, "y": 0, "z": 0}},
                    "boolean_op": "create", "order": len(features)
                })
                current = {}
        elif t in ("extrude", "extrude_from"):
            if not current:
                continue
            length = p.get("length", 50)
            start = p.get("start", 0)
            if current["type"] == "block":
                features.append({
                    "feature_id": f"feat_{len(features)}",
                    "type": "block",
                    "parameters": {"length": current["width"], "width": current.get("height", current["width"]),
                                   "height": length},
                    "position": {"calculated_coords": {"x": current["x"], "y": current["y"], "z": start}},
                    "boolean_op": "create", "order": len(features)
                })
            elif current["type"] == "cylinder":
                features.append({
                    "feature_id": f"feat_{len(features)}",
                    "type": "cylinder",
                    "parameters": {"diameter": current["radius"] * 2, "height": length},
                    "position": {"calculated_coords": {"x": current["x"], "y": current["y"], "z": start}},
                    "boolean_op": "create", "order": len(features)
                })
            current = {}
        elif t in ("cone", "sphere"):
            features.append({
                "feature_id": f"feat_{len(features)}",
                "type": t,
                "parameters": {"radius": p.get("radius", 25), "height": p.get("height", 50)} if t == "cone"
                             else {"diameter": p.get("radius", 25) * 2},
                "position": {"calculated_coords": {"x": 0, "y": 0, "z": 0}},
                "boolean_op": "create", "order": len(features)
            })

    return features


def execute_plan(session_id: str, plan) -> dict:
    """执行多步建模规划"""
    from tools.journal_gen import JournalGenerator

    # 规划步骤全部转为可执行步骤（过滤掉重复的 new_document）
    steps = [{"tool": "new_document", "params": {}}]
    for step in plan.steps:
        if step.tool != "new_document":
            steps.append({"tool": step.tool, "params": step.params})

    # 生成并执行 C# Journal
    gen = JournalGenerator(f"plan_{session_id}")
    code = gen.generate(steps)
    jpath = gen.save_journal(code)

    result = subprocess.run(
        [config.NX_EXE, os.path.abspath(jpath)],
        capture_output=True, text=True, timeout=120,
        encoding='utf-8', errors='ignore'
    )

    if result.returncode == 0:
        part_file = os.path.join(OUTPUT_DIR, f"plan_{session_id}.prt")
        frontend_features = plan_steps_to_features(plan.steps)
        return {
            "status": "success",
            "session_id": session_id,
            "part_file": part_file,
            "features": frontend_features,
            "message": f"模型已生成（{len(plan.steps)}步）",
            "steps_count": len(plan.steps)
        }
    else:
        return {
            "status": "error",
            "message": f"执行失败: {result.stderr[:300]}"
        }


def add_feature_to_session(session_id: str, command):
    """向会话添加特征（使用 C# + run_journal.exe 执行）"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    feature_id = f"feat_{uuid.uuid4().hex[:8]}"
    feature_type = command.feature_type
    boolean_op = command.boolean_op

    # 解析位置
    origin_x, origin_y, origin_z = 0, 0, 0
    if command.position:
        origin_x = command.position.x or 0
        origin_y = command.position.y or 0
        origin_z = command.position.z or 0

    # 提取参数
    params = {}
    if feature_type == "block" and command.block:
        params = {"length": command.block.length, "width": command.block.width, "height": command.block.height}
    elif feature_type == "cylinder" and command.cylinder:
        params = {"diameter": command.cylinder.diameter, "height": command.cylinder.height}
    elif feature_type == "sphere" and command.sphere:
        params = {"diameter": command.sphere.diameter}
    elif feature_type == "cone" and command.cone:
        params = {"radius": command.cone.base_diameter / 2, "height": command.cone.height}

    # 收集所有特征
    all_features = list(session.features) + [type("Feat", (), {
        "feature_id": feature_id, "type": feature_type,
        "parameters": params, "position": {"calculated_coords": {"x": origin_x, "y": origin_y, "z": origin_z}},
        "boolean_op": boolean_op
    })]

    # 转换为 JSON 步骤
    from tools.journal_gen import JournalGenerator
    steps = [{"tool": "new_document", "params": {}}]
    for feat in all_features:
        ft = feat.type if not isinstance(feat, dict) else feat["type"]
        p = feat.parameters if not isinstance(feat, dict) else feat["params"]
        pos = feat.position if not isinstance(feat, dict) else feat["pos"]
        op = feat.boolean_op if not isinstance(feat, dict) else feat["op"]
        x = pos.get("calculated_coords", {}).get("x", 0) if isinstance(pos, dict) else 0
        y = pos.get("calculated_coords", {}).get("y", 0) if isinstance(pos, dict) else 0
        z = pos.get("calculated_coords", {}).get("z", 0) if isinstance(pos, dict) else 0

        steps.append({"tool": "create_sketch_on_plane", "params": {}})
        if ft == "block":
            l = p.get("length", 100); w = p.get("width", 100)
            steps.append({"tool": "draw_rectangle", "params": {"x": x, "y": y, "width": l, "height": w}})
            steps.append({"tool": "close_sketch", "params": {}})
            steps.append({"tool": "extrude_from", "params": {"start": z, "length": p.get("height", 50)}})
        elif ft == "cylinder":
            r = p.get("diameter", 50) / 2
            steps.append({"tool": "draw_closed_circle", "params": {"x": x, "y": y, "radius": r}})
            steps.append({"tool": "close_sketch", "params": {}})
            if op in ("subtract", "cut"):
                steps.append({"tool": "extrude_cut", "params": {"length": p.get("height", 50)}})
            else:
                steps.append({"tool": "extrude_from", "params": {"start": z, "length": p.get("height", 50)}})
        elif ft == "sphere":
            r = p.get("diameter", 50) / 2
            steps.append({"tool": "close_sketch", "params": {}})
            steps.append({"tool": "sphere", "params": {"radius": r}})
        elif ft == "cone":
            r = p.get("radius", 25)
            h = p.get("height", 50)
            steps.append({"tool": "close_sketch", "params": {}})
            steps.append({"tool": "cone", "params": {"radius": r, "height": h}})
        else:
            steps.append({"tool": "draw_rectangle", "params": {"x": x, "y": y, "width": 50, "height": 50}})
            steps.append({"tool": "close_sketch", "params": {}})
            steps.append({"tool": "extrude_from", "params": {"start": z, "length": 50}})

    # 生成并执行 C# Journal
    gen = JournalGenerator(f"session_{session_id}")
    code = gen.generate(steps)
    jpath = gen.save_journal(code)

    result = subprocess.run(
        [config.NX_EXE, os.path.abspath(jpath)],
        capture_output=True, text=True, timeout=120,
        encoding='utf-8', errors='ignore'
    )

    if result.returncode == 0:
        # 保存特征到会话
        session_manager.add_feature(session_id, FeatureData(
            feature_id=feature_id,
            type=feature_type,
            parameters=params,
            position={"type": "absolute", "calculated_coords": {"x": origin_x, "y": origin_y, "z": origin_z}},
            boolean_op=boolean_op,
            order=len(session.features) + 1
        ))
        return {
            "status": "success",
            "session_id": session_id,
            "part_file": os.path.join(OUTPUT_DIR, f"session_{session_id}.prt"),
            "features": [f.model_dump() for f in session_manager.get_features(session_id)],
            "message": f"已添加 {feature_type}"
        }
    else:
        return {
            "status": "error",
            "message": f"NX 执行失败: {result.stderr[:200]}"
        }

