"""50 级基准测试 — 前 10 个任务测试

测试流程：
  1. 加载 tools.json 和 AI 系统提示词
  2. 对每个任务调用 DeepSeek AI 生成 JSON 规划
  3. 验证 JSON 格式正确
  4. 验证所有工具名存在于 tools.json 注册表中
  5. 验证 ref 引用链正确
  6. 生成执行报告
"""
import sys
import os
import json
import re
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ── 配置 ──
API_KEY = os.getenv("DEEPSEEK_API_KEY") or ""
if not API_KEY:
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "DEEPSEEK_API_KEY" in line and "=" in line:
                API_KEY = line.split("=", 1)[1].strip()

OUTPUT_DIR = Path(__file__).parent.parent / "output"
REPORT_DIR = OUTPUT_DIR / "benchmark"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ── 等级 1 任务（最简单的 5 个） ──
TASKS_L1 = [
    {
        "id": 1,
        "name": "圆柱体",
        "prompt": "创建一个直径 50mm、高 80mm 的圆柱体，中心在原点",
        "tags": ["circle", "extrude"],
        "min_tools": ["new_document", "create_sketch_on_plane", "draw_closed_circle", "close_sketch", "extrude", "save_model"],
    },
    {
        "id": 2,
        "name": "长方体",
        "prompt": "创建一个 100×60×30mm 的长方体，左下角在原点",
        "tags": ["rectangle", "extrude"],
        "min_tools": ["new_document", "create_sketch_on_plane", "draw_rectangle", "close_sketch", "extrude", "save_model"],
    },
    {
        "id": 3,
        "name": "圆管",
        "prompt": "创建一个外径 60mm、内径 30mm、高 40mm 的圆管，中心在原点",
        "tags": ["circle", "extrude", "extrude_cut"],
        "min_tools": ["new_document", "create_sketch_on_plane", "draw_closed_circle", "close_sketch", "extrude", "save_model"],
    },
    {
        "id": 4,
        "name": "底板带方孔",
        "prompt": "创建一个 80×50×20mm 的底板，中心有一个 30×20mm 的通孔",
        "tags": ["rectangle", "extrude", "extrude_cut"],
        "min_tools": ["new_document", "create_sketch_on_plane", "draw_rectangle", "close_sketch", "extrude", "save_model"],
    },
    {
        "id": 5,
        "name": "L 形角铁",
        "prompt": "创建一个 L 形角铁，两臂 80×40mm，壁厚 8mm，拉伸长度 60mm",
        "tags": ["rectangle", "extrude"],
        "min_tools": ["new_document", "create_sketch_on_plane", "draw_rectangle", "close_sketch", "extrude", "save_model"],
    },
]

# ── 等级 2 任务（6-10） ──
TASKS_L2 = [
    {
        "id": 6,
        "name": "倒角长方体",
        "prompt": "创建一个 60×40×30mm 的长方体，所有 12 条棱边倒角 3mm",
        "tags": ["rectangle", "extrude", "chamfer"],
        "min_tools": ["new_document", "create_sketch_on_plane", "draw_rectangle", "close_sketch", "extrude", "chamfer", "save_model"],
    },
    {
        "id": 7,
        "name": "圆角长方体",
        "prompt": "创建一个 60×40×30mm 的长方体，顶面 4 条棱边圆角 R5",
        "tags": ["rectangle", "extrude", "fillet"],
        "min_tools": ["new_document", "create_sketch_on_plane", "draw_rectangle", "close_sketch", "extrude", "fillet", "save_model"],
    },
    {
        "id": 8,
        "name": "台阶轴",
        "prompt": "创建一个台阶轴：三段直径分别为 40mm、30mm、20mm，长度分别为 30mm、30mm、20mm，总长 80mm",
        "tags": ["circle", "extrude", "offset_plane"],
        "min_tools": ["new_document", "create_sketch_on_plane", "offset_plane", "draw_closed_circle", "close_sketch", "extrude", "save_model"],
    },
    {
        "id": 9,
        "name": "底板四孔",
        "prompt": "创建一个 80×50×20mm 的底板，四角距离边缘 10mm 处各有一个直径 10mm 的通孔",
        "tags": ["rectangle", "extrude", "circle", "extrude_cut"],
        "min_tools": ["new_document", "create_sketch_on_plane", "draw_rectangle", "draw_closed_circle", "close_sketch", "extrude", "extrude_cut", "save_model"],
    },
    {
        "id": 10,
        "name": "圆柱两端倒角",
        "prompt": "创建一个直径 30mm、长 100mm 的圆柱，两端各倒角 C2",
        "tags": ["circle", "extrude", "chamfer"],
        "min_tools": ["new_document", "create_sketch_on_plane", "draw_closed_circle", "close_sketch", "extrude", "chamfer", "save_model"],
    },
]

ALL_TASKS = TASKS_L1 + TASKS_L2


# ── 工具验证 ──
TOOLS_PATH = Path(__file__).parent.parent / "src" / "tools" / "tools.json"
TOOL_NAMES = set()
if TOOLS_PATH.exists():
    for t in json.loads(TOOLS_PATH.read_text(encoding="utf-8")).get("tools", []):
        TOOL_NAMES.add(t["name"])


import httpx

def call_ai(system_prompt: str, user_msg: str, max_tokens: int = 4096) -> dict:
    """调用 DeepSeek API"""
    api_key = API_KEY
    if not api_key:
        return {"error": "API Key 未配置"}
    try:
        resp = httpx.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            },
            timeout=120,
        )
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        text = resp.json()["choices"][0]["message"]["content"]
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}


def extract_json(text: str) -> str:
    """从 AI 回复中提取 JSON 数组"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    if "[" in text and "]" in text:
        return text[text.index("["):text.rindex("]")+1]
    return text


def validate_steps(steps: list[dict], task: dict) -> dict:
    """验证 JSON 规划是否有效"""
    issues = []
    used_refs = set()
    defined_refs = set()

    for i, step in enumerate(steps):
        tool = step.get("tool", "")
        params = step.get("params", {})
        ref = step.get("ref", "")

        # 1. 工具名是否存在
        if tool not in TOOL_NAMES:
            issues.append(f"步骤 {i+1}: 未知工具 '{tool}'")

        # 2. new_document 是否在第一步
        if i == 0 and tool != "new_document":
            issues.append(f"步骤 1: 第一步应该是 new_document，实际是 '{tool}'")

        # 3. ref 引用是否已定义
        for pname, pvalue in params.items():
            if isinstance(pvalue, str) and pvalue.startswith("[ref:") or (
                isinstance(pvalue, str) and pvalue in used_refs
            ):
                if pvalue not in defined_refs and pvalue not in used_refs:
                    issues.append(f"步骤 {i+1}: 引用 '{pvalue}' 未定义")

        # 4. 登记 ref
        if ref:
            defined_refs.add(ref)

    return {
        "step_count": len(steps),
        "issues": issues,
        "tools_used": [s.get("tool") for s in steps],
        "valid": len(issues) == 0,
    }


# ── 构建 AI 提示词 ──
def build_system_prompt() -> str:
    tools_path = Path(__file__).parent.parent / "src" / "tools" / "tools.json"
    tool_defs = json.loads(tools_path.read_text(encoding="utf-8"))
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

NX 与 CATIA 版本的关键区别：
- NX 的 chamfer/fillet/revolve API 稳定可用！可以放心使用
- 草图创建后不需要 OpenEdition
- 画完图后必须 close_sketch

规则：
1. 每次建模必须先调用 new_document
2. 草图画完后必须 close_sketch 才能拉伸
3. 用 ref 保存中间结果供后续步骤引用
4. 一个草图可以画多个几何（如多个圆表示多个孔）

只输出 JSON 数组，不要多余文字：
[{{"tool": "new_document", "params": {{}}}},
 {{"tool": "create_sketch_on_plane", "params": {{"plane_id": "XY", "sketch_name": "s1"}}, "ref": "sketch_1"}},
 {{"tool": "draw_closed_circle", "params": {{"sketch": "sketch_1", "x": 0, "y": 0, "radius": 25}}}},
 {{"tool": "close_sketch", "params": {{"sketch": "sketch_1"}}}},
 {{"tool": "extrude", "params": {{"sketch": "sketch_1", "length": 30}}, "ref": "pad_1"}},
 {{"tool": "save_model", "params": {{"path": "C:/model.prt"}}}}]"""


def run_test(system_prompt: str, task: dict) -> dict:
    """运行单个任务的测试"""
    result = {
        "id": task["id"],
        "name": task["name"],
        "status": "pending",
        "ai_response": "",
        "steps": [],
        "validation": {},
        "errors": [],
        "duration_ms": 0,
    }

    # 阶段 1: AI 规划
    print(f"\n  🤖 AI 规划中...", end=" ")
    t0 = time.time()
    ai_result = call_ai(system_prompt, task["prompt"])
    t1 = time.time()
    result["duration_ms"] = round((t1 - t0) * 1000, 1)

    if "error" in ai_result:
        result["status"] = "error"
        result["errors"].append(f"AI 调用失败: {ai_result['error']}")
        return result

    reply = ai_result["text"]
    result["ai_response"] = reply

    # 阶段 2: 解析 JSON
    json_str = extract_json(reply)
    try:
        steps = json.loads(json_str)
        result["steps"] = steps
    except json.JSONDecodeError as e:
        result["status"] = "error"
        result["errors"].append(f"JSON 解析失败: {e}")
        return result

    # 阶段 3: 验证
    validation = validate_steps(steps, task)
    result["validation"] = validation

    if validation["valid"]:
        result["status"] = "pass"
    else:
        result["status"] = "warn"
        result["errors"] = validation["issues"]

    return result


def print_result(task_num: int, name: str, result: dict):
    """打印单个测试结果"""
    status_icon = {
        "pass": "✅",
        "warn": "⚠️ ",
        "error": "❌",
        "pending": "⏳",
    }.get(result["status"], "❓")

    tools_str = ", ".join(result.get("validation", {}).get("tools_used", []))
    print(f"  {status_icon} #{task_num:2d} {name:<12s} ({result['duration_ms']:>6.1f}ms)  [{tools_str}]")

    if result["status"] == "warn":
        for e in result["errors"]:
            print(f"       ⚠️  {e}")
    elif result["status"] == "error":
        for e in result["errors"]:
            print(f"       ❌  {e}")


# ── 主程序 ──
if __name__ == "__main__":
    print("=" * 60)
    print("  NX AI 建模基准测试 — 50 级任务前 10 个")
    print("=" * 60)

    if not API_KEY:
        print("\n❌ 请先在 .env 中配置 DEEPSEEK_API_KEY")
        sys.exit(1)

    system_prompt = build_system_prompt()

    # 测试第 1 组（任务 1-5）
    print(f"\n{'─'*60}")
    print("  📋 Lv.1 — 基础草图+拉伸（任务 1-5）")
    print(f"{'─'*60}")

    results = []
    for task in ALL_TASKS:
        print(f"\n  ── #{task['id']:2d} {task['name']} ──")
        print(f"     描述: \"{task['prompt']}\"")
        result = run_test(system_prompt, task)
        print_result(task["id"], task["name"], result)
        results.append(result)

        # 保存 json 到报告
        report_file = REPORT_DIR / f"task_{task['id']:02d}_{task['name']}.json"
        report_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 汇总 ──
    print(f"\n{'='*60}")
    print("  测试汇总")
    print(f"{'='*60}")
    pass_count = sum(1 for r in results if r["status"] == "pass")
    warn_count = sum(1 for r in results if r["status"] == "warn")
    error_count = sum(1 for r in results if r["status"] == "error")
    total_ms = sum(r["duration_ms"] for r in results)

    print(f"\n  ✅ 通过: {pass_count}  ⚠️  警告: {warn_count}  ❌ 失败: {error_count}")
    print(f"  总耗时: {total_ms/1000:.1f}s 平均: {total_ms/len(results):.0f}ms/任务")

    print(f"\n  详细报告: {REPORT_DIR}/")
    print(f"\n  {'─'*60}")

    for r in results:
        status_icon = {"pass": "✅", "warn": "⚠️ ", "error": "❌"}.get(r["status"], "❓")
        step_count = r.get("validation", {}).get("step_count", 0)
        tools_used = r.get("validation", {}).get("tools_used", [])
        print(f"  {status_icon} #{r['id']:2d} {r['name']:<12s}  {step_count:2d}步  {', '.join(tools_used[:5])}")

    print(f"{'─'*60}")
    print(f"  报告已保存至: {REPORT_DIR}/")
