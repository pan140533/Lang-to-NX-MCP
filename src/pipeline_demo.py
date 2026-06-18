"""NL → AI → JSON → Executor → NX 模型 完整链路 demo

与 CATIA 版本的架构区别：
  - CATIA 版本通过 COM 与 CATIA 通信
  - NX 版本通过 NXOpen Python API 直接与 NX 通信
  - NX 的倒角/圆角/旋转 API 均稳定可用
"""
import sys
import os
import json
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import httpx
from tools import NXSession
from tools.executor import ToolExecutor
from tools.io import new_document, save_model
from log_system import log_operation, log_error

OUTPUT_DIR = Path(__file__).parent.parent / "output"
MODELS_DIR = OUTPUT_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = os.getenv("DEEPSEEK_API_KEY") or ""
if not API_KEY:
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "DEEPSEEK_API_KEY" in line and "=" in line:
                API_KEY = line.split("=", 1)[1].strip()

if not API_KEY:
    print("❌ 请先配置 DEEPSEEK_API_KEY 在 .env 文件中")
    sys.exit(1)


def call_ai(system_prompt: str, user_msg: str) -> str:
    """调用 DeepSeek API"""
    resp = httpx.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            "max_tokens": 4096,
            "temperature": 0.1,
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise Exception(f"API error: {resp.status_code} - {resp.text[:200]}")
    return resp.json()["choices"][0]["message"]["content"]


# ── 加载 tools.json 作为 AI 参考 ──
tools_path = Path(__file__).parent / "tools" / "tools.json"
tool_defs = json.loads(tools_path.read_text(encoding="utf-8"))

tools_desc = []
for t in tool_defs["tools"]:
    params_desc = []
    for pname, pinfo in t.get("params", {}).items():
        opt = " (可选)" if pinfo.get("optional") else ""
        enum = f" 可选值: {pinfo.get('enum')}" if pinfo.get("enum") else ""
        params_desc.append(f"    {pname}: {pinfo.get('type')}{opt} — {pinfo.get('description')}{enum}")
    ret_desc = ""
    if "returns" in t:
        ret_desc = f"  → 返回: ref={t['returns'].get('ref_type')} ({t['returns'].get('description')})"
    tools_desc.append(f"  {t['name']}: {t['description']}")
    if params_desc:
        tools_desc.append("\n".join(params_desc))
    if ret_desc:
        tools_desc.append(f"  {ret_desc}")
    tools_desc.append("")

TOOLS_TEXT = "\n".join(tools_desc)

SYSTEM_PROMPT = f"""你是 NX 建模专家。用户用自然语言描述想要的模型，你输出 JSON 工具调用序列。

可用的工具：
{TOOLS_TEXT}

NX 与 CATIA 的关键区别：
  - NX 使用 NXOpen Python API（原生 Python 接口），不是 COM
  - NX 的 chamfer/fillet/revolve API 稳定可用！可以放心使用
  - 草图创建后不需要 OpenEdition
  - extrude_cut 对应 NX 的 Subtract 布尔操作

规则：
1. 每次建模必须先调用 new_document
2. 草图画完后必须 close_sketch 才能拉伸
3. 可以用 ref 保存中间结果供后续步骤引用

只输出 JSON 数组，不要多余文字：
[
  {{"tool": "new_document", "params": {{}}}},
  {{"tool": "create_sketch_on_plane", "params": {{"plane_id": "XY", "sketch_name": "s1"}}, "ref": "sketch_1"}},
  {{"tool": "draw_closed_circle", "params": {{"sketch": "sketch_1", "x": 0, "y": 0, "radius": 15}}}},
  {{"tool": "close_sketch", "params": {{"sketch": "sketch_1"}}}},
  {{"tool": "extrude", "params": {{"sketch": "sketch_1", "length": 30}}, "ref": "pad_1"}},
  {{"tool": "save_model", "params": {{"path": "C:/model.prt"}}}}
]"""


def nl_to_model(prompt: str) -> dict:
    """自然语言 → 模型"""
    print(f"\n{'='*55}")
    print(f"  输入: {prompt}")
    print(f"{'='*55}")

    # 1. AI 规划
    print("\n🤖 AI 规划中...")
    try:
        reply = call_ai(SYSTEM_PROMPT, prompt)
    except Exception as e:
        return {"status": "error", "error": f"AI 调用失败: {e}"}

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
        return {"status": "error", "error": f"AI 返回的 JSON 解析失败: {e}", "raw": reply}

    print(f"  AI 规划了 {len(steps)} 步:")
    for s in steps:
        print(f"    {s.get('tool')} {s.get('params', {})}")

    # 3. 执行
    print("\n⚙️  执行引擎运行中...")
    session = NXSession()
    executor = ToolExecutor(session)
    result = executor.execute(steps)

    # 4. 保存
    if result["status"] == "ok":
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.abspath(str(MODELS_DIR / f"nx_model_{ts}.prt"))
        save_model(session, model_path)
        print(f"\n✅ 建模完成！保存至: {model_path}")
        result["model_path"] = model_path
        result["steps_detail"] = result.pop("steps", [])
    else:
        print(f"\n❌ 失败于步骤 {result.get('failed_step')}: {result.get('error')}")

    session.close()
    result["raw_ai_reply"] = reply
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NL → NX 模型")
    parser.add_argument("prompt", nargs="*", help="自然语言描述，如 '建一个80×60的底板加圆柱凸台'")
    args = parser.parse_args()

    if args.prompt:
        prompts = [" ".join(args.prompt)]
    else:
        prompts = ["建一个80×60×10的底板，中心加一个直径30高20的圆柱凸台"]

    for prompt in prompts:
        result = nl_to_model(prompt)
        if result["status"] == "ok":
            print(f"\n🎉 成功: {result.get('model_path')}")
        else:
            print(f"\n💥 失败: {result.get('error')}")
            print(f"  原始回复: {result.get('raw', '')[:300]}")
