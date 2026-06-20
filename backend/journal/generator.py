"""Journal 脚本生成器 — 调用固定 NXModeler API

架构：
  JSON 步骤 → generator.py → C# 脚本（调用 NXModeler 方法）
                                 ↓
                           run_journal.exe → NX

  NXModeler 的方法实现是固定的（nx_modeler.cs），永不猜测 API。
"""
from __future__ import annotations

import os
import re
import subprocess
import uuid
from datetime import datetime
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


def generate_output_name(description: str, index: int = 0) -> str:
    """生成标准化输出名称

    格式：年_月_日_时_分_项目名称（AI自动生成）_x
    示例：2026_06_20_15_30_三叶风扇（AI自动生成）_0

    Args:
        description: 用户输入的建模描述（从中提取项目名称）
        index: 序号，默认 0；批量建模时递增 0, 1, 2...

    Returns:
        格式化的名称字符串
    """
    now = datetime.now()
    timestamp = now.strftime("%Y_%m_%d_%H_%M")

    # 从描述中提取项目名称：去掉特殊字符，取前 20 个字符
    project = re.sub(r'[\\/:*?"<>|]', '', description).strip()[:20]
    if not project:
        project = "未命名"

    return f"{timestamp}_{project}（AI自动生成）_{index}"


class JournalGenerator:

    def __init__(self, part_name: str = "", description: str = "", index: int = 0):
        """初始化生成器

        Args:
            part_name: 部件名称（旧模式，兼容用）
            description: 用户描述，用于自动生成标准化名称
            index: 序号，默认 0
        """
        if description:
            self.part_name = generate_output_name(description, index)
        else:
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

        # 2. 生成步骤调用代码
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
                step_lines.append(f"    // ? 跳过未实现: {tool}")
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

    # ═══════════════════════════════════════════════════════════════════════
    # 文档操作
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_new_document(self, p: dict) -> str:
        return f"    m.Tool_NewDocument(\"{self.part_name}\");"

    def _gen_save_model(self, p: dict) -> str:
        path = p.get("path", "")
        if path:
            return f'    m.Tool_SaveModel(@"{path.replace(chr(92), chr(92)+chr(92))}");'
        return ""

    # ═══════════════════════════════════════════════════════════════════════
    # 草图操作
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_create_sketch(self, p: dict) -> str:
        """别名：create_sketch = create_sketch_on_plane"""
        return "    m.Tool_CreateSketch();"

    def _gen_create_sketch_on_plane(self, p: dict) -> str:
        return "    m.Tool_CreateSketch();"

    def _gen_create_sketch_on_face(self, p: dict) -> str:
        face_index = p.get("face_index", 0)
        return f"    m.Tool_CreateSketchOnFace({int(face_index)});"

    def _gen_close_sketch(self, p: dict) -> str:
        return "    m.Tool_CloseSketch();"

    # ═══════════════════════════════════════════════════════════════════════
    # 绘图工具
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_draw_circle(self, p: dict) -> str:
        """别名：draw_circle = draw_closed_circle"""
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        r = p.get("radius", 10.0)
        return f"    m.Tool_DrawCircle({float(x)}, {float(y)}, {float(r)});"

    def _gen_draw_closed_circle(self, p: dict) -> str:
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        r = p.get("radius", 10.0)
        return f"    m.Tool_DrawCircle({float(x)}, {float(y)}, {float(r)});"

    def _gen_draw_arc(self, p: dict) -> str:
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        r = p.get("radius", 10.0)
        start = p.get("start_angle", 0.0)
        end = p.get("end_angle", 90.0)
        return f"    m.Tool_DrawArc({float(x)}, {float(y)}, {float(r)}, {float(start)}, {float(end)});"

    def _gen_draw_rectangle(self, p: dict) -> str:
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        w = p.get("width", 100.0)
        h = p.get("height", 60.0)
        return f"    m.Tool_DrawRectangle({float(x)}, {float(y)}, {float(w)}, {float(h)});"

    def _gen_draw_line(self, p: dict) -> str:
        x1 = p.get("x1", 0.0)
        y1 = p.get("y1", 0.0)
        x2 = p.get("x2", 50.0)
        y2 = p.get("y2", 0.0)
        return f"    m.Tool_DrawLine({float(x1)}, {float(y1)}, {float(x2)}, {float(y2)});"

    def _gen_draw_polyline(self, p: dict) -> str:
        points = p.get("points", [])
        if not points:
            return "    // ! 多段线缺少点数据"
        pts_str = ", ".join([f"new Point3d({float(pt[0])}, {float(pt[1])}, 0)" for pt in points])
        return f"    m.Tool_DrawPolyline(new Point3d[]{{{pts_str}}});"

    def _gen_draw_spline(self, p: dict) -> str:
        points = p.get("points", [])
        if not points:
            return "    // ! 样条曲线缺少点数据"
        pts_str = ", ".join([f"new Point3d({float(pt[0])}, {float(pt[1])}, 0)" for pt in points])
        return f"    m.Tool_DrawSpline(new Point3d[]{{{pts_str}}});"

    # ═══════════════════════════════════════════════════════════════════════
    # 基本体素
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_block(self, p: dict) -> str:
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        z = p.get("z", 0.0)
        l = p.get("length", 100.0)
        w = p.get("width", 100.0)
        h = p.get("height", 100.0)
        return f"    m.Tool_Block({float(x)}, {float(y)}, {float(z)}, {float(l)}, {float(w)}, {float(h)});"

    def _gen_cylinder(self, p: dict) -> str:
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        z = p.get("z", 0.0)
        r = p.get("radius", 25.0)
        h = p.get("height", 50.0)
        return f"    m.Tool_Cylinder({float(x)}, {float(y)}, {float(z)}, {float(r)}, {float(h)});"

    def _gen_cone(self, p: dict) -> str:
        r = p.get("radius", 20.0)
        h = p.get("height", 50.0)
        return f"    m.Tool_Cone({float(r)}, {float(h)});"

    def _gen_sphere(self, p: dict) -> str:
        r = p.get("radius", 25.0)
        return f"    m.Tool_Sphere({float(r)});"

    def _gen_torus(self, p: dict) -> str:
        major = p.get("major_radius", 50.0)
        minor = p.get("minor_radius", 10.0)
        return f"    m.Tool_Torus({float(major)}, {float(minor)});"

    # ═══════════════════════════════════════════════════════════════════════
    # 扫描特征
    # ═══════════════════════════════════════════════════════════════════════

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

    def _gen_revolve(self, p: dict) -> str:
        angle = p.get("angle", 360.0)
        return f"    m.Tool_Revolve({float(angle)});"

    def _gen_sweep(self, p: dict) -> str:
        path_points = p.get("path_points", [])
        if not path_points:
            return "    // ! 扫掠缺少路径点"
        pts_str = ", ".join([f"new Point3d({float(pt[0])}, {float(pt[1])}, {float(pt[2])})" for pt in path_points])
        return f"    m.Tool_Sweep(new Point3d[]{{{pts_str}}});"

    def _gen_loft(self, p: dict) -> str:
        sections = p.get("sections", [])
        if not sections:
            return "    // ! 放样缺少截面"
        refs_str = ", ".join([f'"{ref}"' for ref in sections])
        return f"    m.Tool_Loft(new string[]{{{refs_str}}});"

    # ═══════════════════════════════════════════════════════════════════════
    # 布尔操作
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_boolean_unite(self, p: dict) -> str:
        target = p.get("target_body", "")
        tool = p.get("tool_body", "")
        return f'    m.Tool_BooleanUnite("{target}", "{tool}");'

    def _gen_boolean_subtract(self, p: dict) -> str:
        target = p.get("target_body", "")
        tool = p.get("tool_body", "")
        return f'    m.Tool_BooleanSubtract("{target}", "{tool}");'

    def _gen_boolean_intersect(self, p: dict) -> str:
        target = p.get("target_body", "")
        tool = p.get("tool_body", "")
        return f'    m.Tool_BooleanIntersect("{target}", "{tool}");'

    # ═══════════════════════════════════════════════════════════════════════
    # 细节特征
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_chamfer(self, p: dict) -> str:
        length = p.get("length", 2.0)
        return f"    m.Tool_Chamfer({float(length)});"

    def _gen_fillet(self, p: dict) -> str:
        radius = p.get("radius", 5.0)
        return f"    m.Tool_Fillet({float(radius)});"

    def _gen_edge_blend(self, p: dict) -> str:
        radius = p.get("radius", 5.0)
        edges = p.get("edge_indices", [])
        if not edges:
            return f"    m.Tool_Fillet({float(radius)});"
        edges_str = ", ".join([str(int(e)) for e in edges])
        return f"    m.Tool_EdgeBlend({float(radius)}, new int[]{{{edges_str}}});"

    def _gen_shell(self, p: dict) -> str:
        thickness = p.get("thickness", 2.0)
        face_idx = p.get("remove_face_index", -1)
        return f"    m.Tool_Shell({float(thickness)}, {int(face_idx)});"

    def _gen_hole(self, p: dict) -> str:
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        d = p.get("diameter", 10.0)
        depth = p.get("depth", 20.0)
        hole_type = p.get("hole_type", "simple")
        return f'    m.Tool_Hole({float(x)}, {float(y)}, {float(d)}, {float(depth)}, "{hole_type}");'

    def _gen_pocket(self, p: dict) -> str:
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        l = p.get("length", 50.0)
        w = p.get("width", 30.0)
        d = p.get("depth", 10.0)
        return f"    m.Tool_Pocket({float(x)}, {float(y)}, {float(l)}, {float(w)}, {float(d)});"

    def _gen_boss(self, p: dict) -> str:
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        d = p.get("diameter", 20.0)
        h = p.get("height", 30.0)
        return f"    m.Tool_Boss({float(x)}, {float(y)}, {float(d)}, {float(h)});"

    def _gen_pad(self, p: dict) -> str:
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        l = p.get("length", 40.0)
        w = p.get("width", 20.0)
        h = p.get("height", 15.0)
        return f"    m.Tool_Pad({float(x)}, {float(y)}, {float(l)}, {float(w)}, {float(h)});"

    def _gen_slot(self, p: dict) -> str:
        x = p.get("x", 0.0)
        y = p.get("y", 0.0)
        l = p.get("length", 60.0)
        w = p.get("width", 10.0)
        d = p.get("depth", 5.0)
        return f"    m.Tool_Slot({float(x)}, {float(y)}, {float(l)}, {float(w)}, {float(d)});"

    def _gen_groove(self, p: dict) -> str:
        d = p.get("diameter", 30.0)
        w = p.get("width", 5.0)
        depth = p.get("depth", 3.0)
        return f"    m.Tool_Groove({float(d)}, {float(w)}, {float(depth)});"

    def _gen_thread(self, p: dict) -> str:
        cyl_ref = p.get("cylinder_ref", "")
        thread_type = p.get("thread_type", "metric")
        length = p.get("length", 20.0)
        return f'    m.Tool_Thread("{cyl_ref}", "{thread_type}", {float(length)});'

    def _gen_pattern_linear(self, p: dict) -> str:
        ref = p.get("feature_ref", "")
        cx = p.get("count_x", 2)
        sx = p.get("spacing_x", 50.0)
        cy = p.get("count_y", 1)
        sy = p.get("spacing_y", 0.0)
        return f'    m.Tool_PatternLinear("{ref}", {int(cx)}, {float(sx)}, {int(cy)}, {float(sy)});'

    def _gen_pattern_circular(self, p: dict) -> str:
        ref = p.get("feature_ref", "")
        count = p.get("count", 6)
        angle = p.get("angle", 360.0)
        return f'    m.Tool_PatternCircular("{ref}", {int(count)}, {float(angle)});'

    def _gen_mirror_feature(self, p: dict) -> str:
        ref = p.get("feature_ref", "")
        plane = p.get("mirror_plane", "YZ")
        return f'    m.Tool_MirrorFeature("{ref}", "{plane}");'

    # ═══════════════════════════════════════════════════════════════════════
    # 曲面建模
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_through_curves(self, p: dict) -> str:
        sections = p.get("sections", [])
        if not sections:
            return "    // ! 通过曲线组缺少截面"
        refs_str = ", ".join([f'"{ref}"' for ref in sections])
        return f"    m.Tool_ThroughCurves(new string[]{{{refs_str}}});"

    def _gen_through_curve_mesh(self, p: dict) -> str:
        primary = p.get("primary_curves", [])
        cross = p.get("cross_curves", [])
        if not primary or not cross:
            return "    // ! 通过曲线网格缺少曲线"
        p_str = ", ".join([f'"{ref}"' for ref in primary])
        c_str = ", ".join([f'"{ref}"' for ref in cross])
        return f"    m.Tool_ThroughCurveMesh(new string[]{{{p_str}}}, new string[]{{{c_str}}});"

    def _gen_ruled(self, p: dict) -> str:
        c1 = p.get("curve1_ref", "")
        c2 = p.get("curve2_ref", "")
        return f'    m.Tool_Ruled("{c1}", "{c2}");'

    def _gen_bounded_plane(self, p: dict) -> str:
        curves = p.get("boundary_curves", [])
        if not curves:
            return "    // ! 有界平面缺少边界曲线"
        refs_str = ", ".join([f'"{ref}"' for ref in curves])
        return f"    m.Tool_BoundedPlane(new string[]{{{refs_str}}});"

    def _gen_fill_surface(self, p: dict) -> str:
        curves = p.get("boundary_curves", [])
        if not curves:
            return "    // ! 填充曲面缺少边界曲线"
        refs_str = ", ".join([f'"{ref}"' for ref in curves])
        return f"    m.Tool_FillSurface(new string[]{{{refs_str}}});"

    def _gen_offset_surface(self, p: dict) -> str:
        face = p.get("face_ref", "")
        dist = p.get("distance", 5.0)
        return f'    m.Tool_OffsetSurface("{face}", {float(dist)});'

    def _gen_extension(self, p: dict) -> str:
        face = p.get("face_ref", "")
        edge = p.get("edge_ref", "")
        length = p.get("length", 10.0)
        return f'    m.Tool_Extension("{face}", "{edge}", {float(length)});'

    def _gen_trim_surface(self, p: dict) -> str:
        face = p.get("face_ref", "")
        curves = p.get("boundary_curves", [])
        if not curves:
            return "    // ! 修剪曲面缺少边界曲线"
        refs_str = ", ".join([f'"{ref}"' for ref in curves])
        return f'    m.Tool_TrimSurface("{face}", new string[]{{{refs_str}}});'

    def _gen_face_blend(self, p: dict) -> str:
        f1 = p.get("face1_ref", "")
        f2 = p.get("face2_ref", "")
        r = p.get("radius", 10.0)
        return f'    m.Tool_FaceBlend("{f1}", "{f2}", {float(r)});'

    # ═══════════════════════════════════════════════════════════════════════
    # 同步建模
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_move_face(self, p: dict) -> str:
        faces = p.get("face_indices", [])
        dist = p.get("distance", 5.0)
        dir = p.get("direction", "Z")
        if not faces:
            return "    // ! 移动面缺少面索引"
        faces_str = ", ".join([str(int(f)) for f in faces])
        return f'    m.Tool_MoveFace(new int[]{{{faces_str}}}, {float(dist)}, "{dir}");'

    def _gen_delete_face(self, p: dict) -> str:
        faces = p.get("face_indices", [])
        if not faces:
            return "    // ! 删除面缺少面索引"
        faces_str = ", ".join([str(int(f)) for f in faces])
        return f"    m.Tool_DeleteFace(new int[]{{{faces_str}}});"

    def _gen_replace_face(self, p: dict) -> str:
        faces = p.get("face_indices", [])
        target = p.get("target_face_ref", "")
        if not faces:
            return "    // ! 替换面缺少面索引"
        faces_str = ", ".join([str(int(f)) for f in faces])
        return f'    m.Tool_ReplaceFace(new int[]{{{faces_str}}}, "{target}");'

    def _gen_resize_face(self, p: dict) -> str:
        faces = p.get("face_indices", [])
        new_d = p.get("new_diameter", 0.0)
        new_r = p.get("new_radius", 0.0)
        if not faces:
            return "    // ! 调整面大小缺少面索引"
        faces_str = ", ".join([str(int(f)) for f in faces])
        return f"    m.Tool_ResizeFace(new int[]{{{faces_str}}}, {float(new_d)}, {float(new_r)});"

    # ═══════════════════════════════════════════════════════════════════════
    # 变换操作
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_translate(self, p: dict) -> str:
        dx = p.get("dx", 0.0)
        dy = p.get("dy", 0.0)
        dz = p.get("dz", 0.0)
        return f"    m.Tool_Translate({float(dx)}, {float(dy)}, {float(dz)});"

    def _gen_rotate(self, p: dict) -> str:
        axis = p.get("axis", "Z")
        angle = p.get("angle", 90.0)
        return f"    m.Tool_Rotate({float(angle)}, \"{axis}\");"

    def _gen_scale(self, p: dict) -> str:
        factor = p.get("factor", 1.0)
        return f"    m.Tool_Scale({float(factor)});"

    # ═══════════════════════════════════════════════════════════════════════
    # 测量与查询
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_measure_distance(self, p: dict) -> str:
        p1 = p.get("point1", [0, 0, 0])
        p2 = p.get("point2", [0, 0, 0])
        return f"    m.Tool_MeasureDistance(new Point3d({float(p1[0])}, {float(p1[1])}, {float(p1[2])}), new Point3d({float(p2[0])}, {float(p2[1])}, {float(p2[2])}));"

    def _gen_measure_volume(self, p: dict) -> str:
        return "    m.Tool_MeasureVolume();"

    def _gen_measure_mass(self, p: dict) -> str:
        density = p.get("density", 7850.0)
        return f"    m.Tool_MeasureMass({float(density)});"

    # ─── 工具方法 ───

    def save_journal(self, code: str, output_path: Optional[str] = None) -> str:
        if output_path is None:
            output_path = str(Path(__file__).parent.parent.parent / "output" / "scripts"
                              / f"journal_{self.part_name}.cs")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(code, encoding="utf-8-sig")
        return output_path

    def launch_nx(self, jpath: str, wait: bool = False,
                  timeout: int = 300) -> Optional[subprocess.CompletedProcess]:
        if not os.path.exists(NX_EXE):
            msg = f"NX not found: {NX_EXE}"
            log_error("launch_nx", msg)
            print(f"[!] {msg}")
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