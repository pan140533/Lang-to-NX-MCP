"""Journal 脚本生成器 — 调用固定 NXModeler API

架构：
  JSON 步骤 → journal_gen.py → C# 脚本（调用 NXModeler 方法）
                                 ↓
                           run_journal.exe → NX

  NXModeler 的方法实现是固定的（nx_modeler.cs），永不猜测 API。
"""
from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path
from typing import Optional
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from log_system import log_operation, log_error

NX_ROOT = os.environ.get("UGII_BASE_DIR", "")
NX_EXE = os.path.join(NX_ROOT, "NXBIN", "run_journal.exe")
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output" / "models"
MODELER_PATH = Path(__file__).parent / "nx_modeler.cs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class JournalGenerator:

    def __init__(self, part_name: str = ""):
        self.part_name = part_name or f"m_{uuid.uuid4().hex[:8]}"
        self._refs: dict[str, str] = {}

    def generate(self, steps: list[dict]) -> str:
        # 1. 读取 NXModeler 固定实现
        if MODELER_PATH.exists():
            modeler_code = MODELER_PATH.read_text(encoding="utf-8")
            # 去掉 using 和注释头
            lines = []
            skip_until_class = True
            for line in modeler_code.split("\n"):
                if skip_until_class:
                    if line.strip().startswith("public class NXModeler"):
                        skip_until_class = False
                        lines.append(line)
                    continue
                lines.append(line)
            modeler_body = "\n".join(lines)
        else:
            modeler_body = "public class NXModeler {} // not found"

        # 2. 生成步骤调用代码（在 NXModeler 方法内）
        step_lines = []
        step_lines.append("using System;")
        step_lines.append("using System.Collections.Generic;")
        step_lines.append("using NXOpen;")
        step_lines.append("using NXOpen.Features;")
        step_lines.append("using NXOpen.GeometricUtilities;")
        step_lines.append("")
        step_lines.append("public class NXJournal")
        step_lines.append("{")
        step_lines.append("  public static void Main(string[] args)")
        step_lines.append("  {")
        step_lines.append("    NXModeler m = new NXModeler();")
        step_lines.append("    m.Init();")
        step_lines.append("    m.outPath = \"" + str(OUTPUT_DIR).replace("\\", "\\\\") + "\";")
        step_lines.append("")

        for i, step in enumerate(steps):
            tool = step.get("tool", "")
            params = step.get("params", {})
            ref = step.get("ref", "")

            method_name = f"_gen_{tool}"
            method = getattr(self, method_name, None)
            if method is None:
                step_lines.append(f"    // ? 跳过: {tool}")
                continue

            step_lines.append(f"    // 步骤 {i+1}: {tool}")
            try:
                call_line = method(params)
                if call_line:
                    step_lines.append(call_line)
                if ref and call_line:
                    self._refs[ref] = call_line
            except Exception as e:
                step_lines.append(f"    // ! 失败: {e}")

        # 最终保存
        step_lines.append("")
        fp = str(OUTPUT_DIR / f"{self.part_name}.prt")
        step_lines.append(f'    m.Tool_SaveModel(@"{fp.replace(chr(92), chr(92)+chr(92))}");')
        step_lines.append("  }")
        step_lines.append("}")
        step_lines.append("")

        # 3. 合并
        return "\n".join(step_lines) + modeler_body

    # ─── JSON 步骤 → C# 方法调用 ───

    def _gen_new_document(self, p: dict) -> str:
        return f"    m.Tool_NewDocument(\"{self.part_name}\");"

    def _gen_create_sketch_on_plane(self, p: dict) -> str:
        return "    m.Tool_CreateSketch();"

    def _gen_close_sketch(self, p: dict) -> str:
        return "    m.Tool_CloseSketch();"

    def _gen_draw_closed_circle(self, p: dict) -> str:
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        r = p.get("radius", 10.0)
        return f"    m.Tool_DrawCircle({float(x)}, {float(y)}, {float(r)});"

    def _gen_draw_line(self, p: dict) -> str:
        x1 = p.get("x1", 0.0)
        y1 = p.get("y1", 0.0)
        x2 = p.get("x2", 50.0)
        y2 = p.get("y2", 0.0)
        return f"    m.Tool_DrawLine({float(x1)}, {float(y1)}, {float(x2)}, {float(y2)});"

    def _gen_draw_rectangle(self, p: dict) -> str:
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        w = p.get("width", 100.0)
        h = p.get("height", 60.0)
        return f"    m.Tool_DrawRectangle({float(x)}, {float(y)}, {float(w)}, {float(h)});"

    def _gen_extrude(self, p: dict) -> str:
        length = p.get("length", 10.0)
        return f"    m.Tool_Extrude({float(length)});"

    def _gen_extrude_from(self, p: dict) -> str:
        start = p.get("start", 0.0)
        length = p.get("length", 10.0)
        return f"    m.Tool_ExtrudeFrom({float(start)}, {float(length)});"

    def _gen_extrude_cut(self, p: dict) -> str:
        length = p.get("length", 10.0)
        return f"    m.Tool_ExtrudeCut({float(length)});"



    def _gen_cone(self, p: dict) -> str:
        r = p.get('radius', 20.0)
        h = p.get('height', 50.0)
        return f'    m.Tool_Cone({float(r)}, {float(h)});'

    def _gen_sphere(self, p: dict) -> str:
        r = p.get('radius', 25.0)
        return f'    m.Tool_Sphere({float(r)});'

    def _gen_save_model(self, p: dict) -> str:
        path = p.get("path", "")
        if path:
            return f'    m.Tool_SaveModel(@"{path.replace(chr(92), chr(92)+chr(92))}");'
        return ""

    # ─── 工具方法 ───

    def save_journal(self, code: str, output_path: Optional[str] = None) -> str:
        if output_path is None:
            output_path = str(Path(__file__).parent.parent.parent / "output" / "scripts"
                              / f"journal_{self.part_name}.cs")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(code, encoding="utf-8")
        return output_path

    def launch_nx(self, jpath: str, wait: bool = False,
                  timeout: int = 300) -> Optional[subprocess.CompletedProcess]:
        if not os.path.exists(NX_EXE):
            msg = f"NX not found: {NX_EXE}"
            log_error("launch_nx", msg)
            print(f"? {msg}")
            return None
        cmd = [NX_EXE, os.path.abspath(jpath)]
        log_operation("launch_nx", "start", {"cmd": " ".join(cmd)})
        print(f"run_journal: {' '.join(cmd)}")
        if wait:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            log_operation("launch_nx", "done", {"exit": proc.returncode})
            print(f"  exit: {proc.returncode}")
            if proc.stderr:
                print(f"  err: {proc.stderr[:300]}")
            return proc
        else:
            subprocess.Popen(cmd)
            return None

    @staticmethod
    def convert_and_run(steps, name="", launch=True):
        gen = JournalGenerator(name)
        code = gen.generate(steps)
        jp = gen.save_journal(code)
        print(f"Saved: {jp}")
        if launch:
            gen.launch_nx(jp, wait=False)
        return jp, code
