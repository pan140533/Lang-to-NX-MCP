from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import uuid
import json
from pydantic import BaseModel
from typing import Optional, Dict, Any
from session_manager import SessionManager, FeatureData
from log_system import log_operation, log_error, log_task_start, log_task_end
import config  # 导入配置文件
from backend.journal.generator import generate_output_name

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

# Agent Pipeline 缓存（按 session 隔离）
_agent_pipelines: Dict[str, Any] = {}

# 输出目录
OUTPUT_DIR = config.OUTPUT_DIR
os.makedirs(OUTPUT_DIR, exist_ok=True)


class CommandRequest(BaseModel):
    """指令请求"""
    session_id: Optional[str] = None
    description: str


def _get_agent_pipeline(session_id: str):
    """为指定 session 创建或获取 Agent Pipeline"""
    if session_id in _agent_pipelines:
        return _agent_pipelines[session_id]

    from backend.agent.intent import IntentRecognition
    from backend.agent.memory import ContextMemory
    from backend.agent.planner import TaskPlanner
    from backend.agent.executor import Executor, AgentPipeline
    from backend.journal.generator import JournalGenerator

    memory = ContextMemory()
    planner = TaskPlanner(memory=memory)

    # 先用占位函数创建 executor 和 pipeline
    executor = Executor(memory, planner, lambda x: "", lambda x: (True, {}))
    pipeline = AgentPipeline(IntentRecognition(), memory, planner, executor)

    def generator_func(tool_calls):
        """将 tool_calls 转为 C# 代码"""
        name = pipeline.current_output_name or f"plan_{session_id}"
        gen = JournalGenerator(part_name=name)
        return gen.generate(tool_calls)

    def executor_func(code):
        """保存 C# 代码到 journal 文件并启动 NX 执行"""
        name = pipeline.current_output_name or f"plan_{session_id}"
        gen = JournalGenerator(part_name=name)
        jpath = gen.save_journal(code)
        result = subprocess.run(
            [config.NX_EXE, os.path.abspath(jpath)],
            capture_output=True, text=True, timeout=120,
            encoding='gbk', errors='ignore'
        )
        if result.returncode == 0:
            part_file = os.path.join(OUTPUT_DIR, f"{name}.prt")
            return True, {"files": [part_file], "features": []}
        else:
            return False, {"error": result.stderr[:300]}

    executor._generate = generator_func
    executor._execute = executor_func

    _agent_pipelines[session_id] = pipeline
    return pipeline


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
    """执行建模指令 — 统一通过 Agent Pipeline 处理"""
    log_task_start("execute_command", {"description": request.description[:80]})
    try:
        # 1. 创建或获取会话
        if not request.session_id:
            session = session_manager.create_session()
            session_id = session.session_id
        else:
            session_id = request.session_id
            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="会话不存在")

        # 2. 获取 Agent Pipeline（会话级别的，带上下文记忆）
        pipeline = _get_agent_pipeline(session_id)

        # 3. 生成标准化输出名称并注入流水线
        output_name = generate_output_name(request.description)
        pipeline.current_output_name = output_name
        # 中文项目名（用于前端展示）
        project_name = request.description.strip()[:30] or "未命名"

        # 4. Agent Pipeline 处理：意图识别 → 结构分解 → 任务规划 → 代码生成 → NX 执行
        print(f"[Agent] 处理: {request.description[:80]}")
        result = pipeline.process(request.description)

        # 4. 从 Agent 的规划结果中提取前端渲染特征
        plan = pipeline.last_plan
        if plan and plan.steps:
            features = plan_steps_to_features(plan.steps)
            result["features"] = features
            result["steps_count"] = len(plan.steps)
            result["strategy"] = plan.strategy
            if plan.human_thought:
                result["human_thought"] = plan.human_thought[:200]

            # 同步 Agent 执行结果到 session_manager（供前端查询）
            if result.get("status") == "success":
                for feat in features:
                    session_manager.add_feature(session_id, FeatureData(
                        feature_id=feat.get("feature_id", f"feat_{uuid.uuid4().hex[:8]}"),
                        type=feat.get("type", "unknown"),
                        parameters=feat.get("parameters", {}),
                        position=feat.get("position", {}),
                        boolean_op=feat.get("boolean_op", "create"),
                        order=feat.get("order", len(features)),
                    ))
        else:
            result["features"] = []

        result["session_id"] = session_id
        result["output_name"] = output_name
        result["project_name"] = project_name
        print(f"[Agent] 结果: {result.get('status')}, 步骤: {result.get('steps_count', 0)}, 输出: {output_name}")
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
        elif t in ("draw_closed_circle", "draw_circle"):
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
                    "position": {"calculated_coords": {
                        "x": current["x"] + current["width"] / 2,
                        "y": current["y"] + current.get("height", current["width"]) / 2,
                        "z": start
                    }},
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
        elif t == "pattern_circular":
            # 圆形阵列：复制最后一个特征 count-1 次（原特征已占一个位置）
            count = p.get("count", 2)
            angle = p.get("angle", 360.0)
            if features and count > 1:
                last = features[-1]
                radius = 0
                # 尝试从特征位置推断半径
                pos = last.get("position", {}).get("calculated_coords", {})
                cx, cy = pos.get("x", 0), pos.get("y", 0)
                radius = (cx**2 + cy**2) ** 0.5
                if radius < 0.1:
                    radius = 30  # 默认半径
                for i in range(1, count):
                    import math
                    rad = math.radians(angle * i)
                    new_pos = {
                        "x": radius * math.cos(rad),
                        "y": radius * math.sin(rad),
                        "z": pos.get("z", 0)
                    }
                    features.append({
                        "feature_id": f"feat_{len(features)}",
                        "type": last["type"],
                        "parameters": dict(last.get("parameters", {})),
                        "position": {"calculated_coords": new_pos},
                        "boolean_op": "create",
                        "order": len(features)
                    })
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
    from backend.journal.generator import JournalGenerator

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
        encoding='gbk', errors='ignore'
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
    from backend.journal.generator import JournalGenerator
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
        encoding='gbk', errors='ignore'
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

