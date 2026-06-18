"""NX AI 建模助手 - Web 后端服务

将 CATIA 版本重构为 NX 版本。
核心变化：COM 调用 → NXOpen Python API（原生 Python，无需 COM）
"""
import os
import sys
import json
import uuid
import time
import threading
import subprocess
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from log_system import (log_task_start, log_task_end, log_operation,
                         log_error, log_fix, save_script)

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.resolve()
ENV_FILE = BASE_DIR / ".env"

# 强制加载 .env
_env_loaded = load_dotenv(ENV_FILE, override=True)
if not _env_loaded or not os.getenv("DEEPSEEK_API_KEY"):
    try:
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
    except Exception:
        pass

app = Flask(__name__,
            template_folder=str(BASE_DIR / "templates"))
OUTPUT_DIR = BASE_DIR / "output"
SCRIPTS_DIR = OUTPUT_DIR / "scripts"
MODELS_DIR = OUTPUT_DIR / "models"
for d in [SCRIPTS_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

_tasks_lock = threading.Lock()
_tasks: dict[str, dict] = {}

try:
    import httpx
except ImportError:
    httpx = None

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODELS = ["deepseek-chat", "deepseek-reasoner"]
_API_KEY = os.getenv("DEEPSEEK_API_KEY") or ""


# ═══════════════════════════════════════════════════════════
#  AI 助手：通用调用
# ═══════════════════════════════════════════════════════════

def _call_ai(system_prompt: str, user_msg: str, max_tokens: int = 4096) -> dict:
    """通用 AI 调用，返回 {"text": ...} 或 {"error": ...}"""
    api_key = _API_KEY or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return {"error": "请先配置 DEEPSEEK_API_KEY（在 .env 文件中设置）"}
    if httpx is None:
        return {"error": "httpx 未安装"}

    last_err = ""
    for model in DEEPSEEK_MODELS:
        try:
            resp = httpx.post(
                DEEPSEEK_API_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg},
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.1,
                    "stream": False,
                },
                timeout=120,
            )
            if resp.status_code != 200:
                last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
                continue
            text = resp.json()["choices"][0]["message"]["content"]
            return {"text": text}
        except Exception as e:
            last_err = str(e)
            continue
    return {"error": f"AI 调用失败: {last_err}"}


# ═══════════════════════════════════════════════════════════
#  AI 提示词 — NX 版本
# ═══════════════════════════════════════════════════════════

def _build_system_prompt() -> str:
    """构建 NX 建模的 AI 系统提示词

    NX 与 CATIA 的关键区别：
      - NX 使用 NXOpen Python API（原生 Python），不是 COM
      - NX 的 Builder 模式确保参数正确性
      - NX 的倒角/圆角/旋转 API 都稳定可用
      - 不需要特殊的 OpenEdition/CloseEdition 调用顺序
    """
    tools_path = BASE_DIR / "src" / "tools" / "tools.json"
    try:
        tool_defs = json.loads(tools_path.read_text(encoding="utf-8"))
    except Exception as e:
        return f"加载工具定义失败: {e}"

    tools_lines = []
    for t in tool_defs["tools"]:
        tools_lines.append(f"- {t['name']}: {t['description']}")
        for pname, pinfo in t.get("params", {}).items():
            opt = " (可选)" if pinfo.get("optional") else ""
            enum = f" [{','.join(pinfo.get('enum', []))}]" if pinfo.get("enum") else ""
            tools_lines.append(f"  参数 {pname}: {pinfo.get('type')}{opt}{enum}")
        if "returns" in t:
            r = t["returns"]
            tools_lines.append(f"  返回: ref({r.get('ref_type','?')}) — {r.get('description','')}")

    tools_text = "\n".join(tools_lines)

    return f"""你是 NX 建模专家。用户用自然语言描述想要的模型，你输出 JSON 工具调用序列。

可用的工具：
{tools_text}

与 CATIA 版本的关键区别（重要！）：
1. NX 使用 NXOpen Python API，所有工具都是原生 Python，不是 COM
2. NX 的倒角(chamfer)和圆角(fillet)API 稳定可用！可以放心使用
3. NX 的旋转体(revolve)API 稳定可用！可以放心使用
4. 草图创建后不需要 OpenEdition（NX 自动处理）
5. 画完图后需要 close_sketch 才能进行后续操作
6. extrude_cut 对应 NX 的 Subtract 布尔操作

规则：
1. 每次建模必须先调用 new_document
2. 草图画完后必须 close_sketch 才能拉伸/旋转
3. 用 ref 保存中间结果供后续步骤引用
4. 一个草图可以画多个几何（如多个圆表示多个孔）

输出格式 — 只输出 JSON 数组，不要多余文字：
[{{"tool": "new_document", "params": {{}}}},
 {{"tool": "create_sketch_on_plane", "params": {{"plane_id": "XY", "sketch_name": "s1"}}, "ref": "sketch_1"}},
 {{"tool": "draw_closed_circle", "params": {{"sketch": "sketch_1", "x": 0, "y": 0, "radius": 15}}}},
 {{"tool": "close_sketch", "params": {{"sketch": "sketch_1"}}}},
 {{"tool": "extrude", "params": {{"sketch": "sketch_1", "length": 30}}, "ref": "pad_1"}},
 {{"tool": "save_model", "params": {{"path": "C:/model.prt"}}}}]"""


# ═══════════════════════════════════════════════════════════
#  后台任务处理
# ═══════════════════════════════════════════════════════════

def _process_task(task_id: str, user_prompt: str) -> None:
    """后台任务：NL → AI 规划 JSON → Executor 执行 → NX 出模"""
    t_start = time.time()
    log_task_start(task_id, user_prompt)
    _update_task(task_id, "processing", "AI 正在分析需求并规划建模步骤...")

    # 1. AI 规划
    system_prompt = _build_system_prompt()
    ai_result = _call_ai(system_prompt, user_prompt, max_tokens=4096)
    if "error" in ai_result:
        log_task_end(task_id, "error", f"AI 规划失败: {ai_result['error']}")
        _update_task(task_id, "error", f"AI 规划失败: {ai_result['error']}")
        return

    reply = ai_result["text"]

    # 2. 解析 JSON
    json_str = reply.strip()
    if "```" in json_str:
        m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", json_str, re.DOTALL)
        if m:
            json_str = m.group(1)
    if "[" in json_str and "]" in json_str:
        json_str = json_str[json_str.index("["):json_str.rindex("]")+1]

    try:
        steps = json.loads(json_str)
    except json.JSONDecodeError as e:
        err = f"AI 返回的 JSON 解析失败: {e}"
        log_task_end(task_id, "error", err)
        _update_task(task_id, "error", err)
        return

    # 3. 保存规划脚本到日志
    save_script(task_id, json.dumps(steps, ensure_ascii=False, indent=2))
    _update_task(task_id, "processing",
                 f"AI 规划完成（{len(steps)} 步），正在执行建模...",
                 steps=steps, total_steps=len(steps), current_step=0)

    # 4. 执行（尝试直连 NX，失败则生成 Journal 文件）
    from tools import NXSession
    from tools.executor import ToolExecutor
    from tools.io import save_model

    session = NXSession(mode="auto")
    try:
        executor = ToolExecutor(session, task_id=task_id)
        result = executor.execute(steps)

        if result["status"] == "ok":
            # 保存模型
            model_path = MODELS_DIR / f"model_{task_id}.prt"
            save_model(session, str(model_path))

            # 如果 Journal 模式，需要执行 journal 文件
            if not session.is_direct_mode:
                journal_path = session.write_journal(str(SCRIPTS_DIR))
                _update_task(task_id, "processing", "正在启动 NX 执行建模脚本...")
                try:
                    proc = session.execute_journal(journal_path, wait=True, timeout=300)
                    if proc.returncode != 0:
                        log_task_end(task_id, "warning",
                                     f"建模脚本已生成但 NX 执行返回非零: {proc.stderr[:200]}",
                                     model_path=str(model_path))
                        _update_task(task_id, "warning",
                                     f"脚本已生成（{journal_path}），请手动在 NX 中运行",
                                     model_path=str(model_path),
                                     script_path=str(journal_path))
                        return
                except subprocess.TimeoutExpired:
                    _update_task(task_id, "warning", "NX 执行超时，脚本已保存可手动运行",
                                 script_path=str(journal_path))
                    return

            duration_s = time.time() - t_start
            log_task_end(task_id, "completed", "建模已完成",
                         model_path=str(model_path), duration_s=duration_s)
            _update_task(task_id, "completed", "建模完成 ✅",
                         model_path=str(model_path),
                         steps_detail=result.get("steps", []))
        else:
            err = f"执行失败（步骤 {result.get('failed_step','?')}）: {result.get('error','')}"
            log_task_end(task_id, "error", err)
            _update_task(task_id, "error", err,
                         steps_detail=result.get("steps", []))
    except Exception as e:
        err = f"执行异常: {e}"
        log_task_end(task_id, "error", err)
        _update_task(task_id, "error", err)
    finally:
        try:
            session.update()
        except Exception:
            pass


def _update_task(task_id: str, status: str, message: str, **extra) -> None:
    with _tasks_lock:
        if task_id in _tasks:
            _tasks[task_id].update({"status": status, "message": message, **extra})


# ═══════════════════════════════════════════════════════════
#  Flask Routes
# ═══════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(force=True)
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "请输入模型描述"}), 400

    task_id = uuid.uuid4().hex
    with _tasks_lock:
        _tasks[task_id] = {"status": "queued", "message": "任务已加入队列", "prompt": prompt}

    t = threading.Thread(target=_process_task, args=(task_id, prompt), daemon=True)
    t.start()

    return jsonify({"task_id": task_id})


@app.route("/api/status/<task_id>")
def api_status(task_id: str):
    with _tasks_lock:
        task = _tasks.get(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify({k: task[k] for k in ("status", "message", "model_path", "script_path",
                                          "steps", "total_steps", "current_step",
                                          "steps_detail") if k in task})


@app.route("/api/open-nx", methods=["POST"])
def api_open_nx():
    """Bring the running NX window to the foreground."""
    try:
        from tools.nx_session import NXOPEN_AVAILABLE, NXOpen
        if NXOPEN_AVAILABLE:
            session = NXOpen.Session.GetSession()
            # NX is always visible; just bring to front
            import win32gui
            try:
                hwnd = win32gui.FindWindow(None, "NX")
                if hwnd:
                    win32gui.ShowWindow(hwnd, 1)
                    win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass
    except ImportError:
        return jsonify({"error": "NX 直连模式未配置，请运行 Journal 脚本"}), 500
    except Exception as exc:
        return jsonify({"error": f"无法连接到 NX: {exc}"}), 500
    return jsonify({"success": True})


@app.route("/api/debug")
def api_debug():
    key = os.getenv("DEEPSEEK_API_KEY", "")
    from tools.nx_session import NXOPEN_AVAILABLE as nx_avail, NXOPEN_VERSION as nx_ver
    return jsonify({
        "has_key": bool(key),
        "key_length": len(key),
        "nxopen_available": nx_avail,
        "nxopen_version": nx_ver,
        "env_file_exists": ENV_FILE.exists(),
    })


@app.route("/api/test-ai")
def api_test_ai():
    result = _call_ai("You are a CAD modeling expert. Reply briefly in Chinese.",
                      "测试连接：回复OK", max_tokens=100)
    if "error" in result:
        return jsonify({"status": "error", "message": result["error"]})
    return jsonify({
        "status": "ok",
        "reply_preview": result.get("text", "")[:200],
    })


# ═══════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5005"))
    from tools.nx_session import NXOPEN_AVAILABLE as nx_avail
    print(f"🌐  NX AI 建模助手  →  http://127.0.0.1:{port}")
    print(f"📁  输出目录: {OUTPUT_DIR}")
    print(f"🔑  API Key: {'✅ 已配置' if os.getenv('DEEPSEEK_API_KEY') else '❌ 未配置'}")
    print(f"🔧  NXOpen: {'✅ 可用（直连模式）' if nx_avail else '⚠️  Journal 模式（需启动 NX 执行脚本）'}")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
