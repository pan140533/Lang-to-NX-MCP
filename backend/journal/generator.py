"""
C# Journal 脚本生成器

将 JSON 格式的工具调用列表转换为完整的 C# Journal 脚本，
通过 nx_modeler.cs 中固定的 NXOpen API 封装来执行。

架构：
  JSON tool_calls → generator.py → .cs 文件 → run_journal.exe → NX

数据流：
  [{"tool": "block", "params": {...}}, ...]
    → _gen_block() 生成 "m.Tool_Block(...);"
    → 拼装为完整 C# 脚本（using + class NXJournal + class NXModeler）
    → 保存 .cs 文件 → run_journal.exe 执行
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from backend.config import config


class JournalGenerator:
    """Journal 脚本生成器

    用法:
        gen = JournalGenerator()
        code = gen.generate(tool_calls)  # tool_calls = [{"tool": "block", "params": {...}}, ...]
        path = gen.save_journal(code)
    """

    def __init__(self, tag: str = ""):
        self.tag = tag or f"mcp_{uuid.uuid4().hex[:8]}"
        self._refs: dict[str, str] = {}

    # ═══════════════════════════════════════════════════════════════════════
    # 核心方法
    # ═══════════════════════════════════════════════════════════════════════

    def generate(self, steps: list[dict]) -> str:
        """将工具调用列表转为 C# 代码字符串"""
        # 1. 读取 nx_modeler.cs 类体
        modeler_body = self._load_modeler_body()

        # 2. 生成步骤调用
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
        step_lines.append("    m.outPath = @\"" + config.output_dir.replace("\\", "\\\\") + "\";")
        step_lines.append("")

        for i, step in enumerate(steps):
            tool = step.get("tool", "")
            params = step.get("params", {})
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
            except Exception as e:
                step_lines.append(f"    // ! 生成失败: {e}")

        # 保存（使用配置中的输出目录）
        step_lines.append("")
        output_models = os.path.join(config.output_dir, "models")
        os.makedirs(output_models, exist_ok=True)
        part_path = os.path.join(output_models, f"{self.tag}.prt").replace("\\", "\\\\")
        step_lines.append(f'    m.Tool_SaveModel(@"{part_path}");')
        step_lines.append("  }")
        step_lines.append("}")
        step_lines.append("")

        return "\n".join(step_lines) + "\n" + modeler_body

    def save_journal(self, code: str) -> str:
        """保存 .cs 文件，返回完整路径"""
        script_dir = os.path.join(config.output_dir, "scripts")
        os.makedirs(script_dir, exist_ok=True)
        cs_path = os.path.join(script_dir, f"journal_{self.tag}.cs")
        with open(cs_path, "w", encoding="utf-8-sig") as f:
            f.write(code)
        return os.path.abspath(cs_path)

    def _load_modeler_body(self) -> str:
        """加载 nx_modeler.cs 中的 NXModeler 类体"""
        modeler_path = Path(__file__).parent / "nx_modeler.cs"
        if not modeler_path.exists():
            return "public class NXModeler { public void Init() {} public string outPath; public void Tool_SaveModel(string p) {} }"

        lines = modeler_path.read_text(encoding="utf-8").split("\n")
        # 去掉 using 和注释头，只保留 public class NXModeler 及之后
        body_lines = []
        in_class = False
        for line in lines:
            if not in_class:
                if line.strip().startswith("public class NXModeler"):
                    in_class = True
                    body_lines.append(line)
                continue
            body_lines.append(line)
        return "\n".join(body_lines)

    # ═══════════════════════════════════════════════════════════════════════
    # 文档操作
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_new_document(self, p: dict) -> str:
        return f'    m.Tool_NewDocument("{self.tag}");'

    def _gen_save_model(self, p: dict) -> str:
        path = p.get("path", "")
        if path:
            safe = path.replace("\\", "\\\\")
            return f'    m.Tool_SaveModel(@"{safe}");'
        return ""

    # ═══════════════════════════════════════════════════════════════════════
    # 草图操作
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_create_sketch(self, p: dict) -> str:
        return "    m.Tool_CreateSketch();"

    def _gen_create_sketch_on_plane(self, p: dict) -> str:
        return "    m.Tool_CreateSketch();"

    def _gen_create_sketch_on_face(self, p: dict) -> str:
        fi = p.get("face_index", 0)
        return f"    m.Tool_CreateSketchOnFace({int(fi)});"

    def _gen_close_sketch(self, p: dict) -> str:
        return "    m.Tool_CloseSketch();"

    # ═══════════════════════════════════════════════════════════════════════
    # 绘图工具
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_draw_circle(self, p: dict) -> str:
        x = p.get("x", 0.0); y = p.get("y", 0.0); r = p.get("radius", 10.0)
        return f"    m.Tool_DrawCircle({float(x)}, {float(y)}, {float(r)});"

    def _gen_draw_closed_circle(self, p: dict) -> str:
        x = p.get("x", 0.0); y = p.get("y", 0.0); r = p.get("radius", 10.0)
        return f"    m.Tool_DrawCircle({float(x)}, {float(y)}, {float(r)});"

    def _gen_draw_arc(self, p: dict) -> str:
        x = p.get("x", 0.0); y = p.get("y", 0.0); r = p.get("radius", 10.0)
        sa = p.get("start_angle", 0.0); ea = p.get("end_angle", 90.0)
        return f"    m.Tool_DrawArc({float(x)}, {float(y)}, {float(r)}, {float(sa)}, {float(ea)});"

    def _gen_draw_rectangle(self, p: dict) -> str:
        x = p.get("x", 0.0); y = p.get("y", 0.0)
        w = p.get("width", 100.0); h = p.get("height", 60.0)
        return f"    m.Tool_DrawRectangle({float(x)}, {float(y)}, {float(w)}, {float(h)});"

    def _gen_draw_line(self, p: dict) -> str:
        x1 = p.get("x1", 0.0); y1 = p.get("y1", 0.0)
        x2 = p.get("x2", 50.0); y2 = p.get("y2", 0.0)
        return f"    m.Tool_DrawLine({float(x1)}, {float(y1)}, {float(x2)}, {float(y2)});"

    def _gen_draw_polyline(self, p: dict) -> str:
        pts = p.get("points", [])
        if not pts:
            return "    // ! 多段线缺少点数据"
        pts_str = ", ".join([f"new Point3d({float(pt[0])}, {float(pt[1])}, 0)" for pt in pts])
        return f"    m.Tool_DrawPolyline(new Point3d[]{{{pts_str}}});"

    def _gen_draw_spline(self, p: dict) -> str:
        pts = p.get("points", [])
        if not pts:
            return "    // ! 样条曲线缺少点数据"
        pts_str = ", ".join([f"new Point3d({float(pt[0])}, {float(pt[1])}, 0)" for pt in pts])
        return f"    m.Tool_DrawSpline(new Point3d[]{{{pts_str}}});"

    # ═══════════════════════════════════════════════════════════════════════
    # 基本体素
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_block(self, p: dict) -> str:
        x = p.get("x", 0.0); y = p.get("y", 0.0); z = p.get("z", 0.0)
        l = p.get("length", 100.0); w = p.get("width", 100.0); h = p.get("height", 100.0)
        return f"    m.Tool_Block({float(x)}, {float(y)}, {float(z)}, {float(l)}, {float(w)}, {float(h)});"

    def _gen_cylinder(self, p: dict) -> str:
        x = p.get("x", 0.0); y = p.get("y", 0.0); z = p.get("z", 0.0)
        r = p.get("radius", 25.0); h = p.get("height", 50.0)
        return f"    m.Tool_Cylinder({float(x)}, {float(y)}, {float(z)}, {float(r)}, {float(h)});"

    def _gen_cone(self, p: dict) -> str:
        r = p.get("radius", 20.0); h = p.get("height", 50.0)
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
        start = p.get("start", 0.0); length = p.get("length", 10.0)
        return f"    m.Tool_ExtrudeFrom({float(start)}, {float(length)});"

    def _gen_extrude_cut(self, p: dict) -> str:
        length = p.get("length", 10.0)
        return f"    m.Tool_ExtrudeCut({float(length)});"

    def _gen_revolve(self, p: dict) -> str:
        angle = p.get("angle", 360.0)
        return f"    m.Tool_Revolve({float(angle)});"

    def _gen_sweep(self, p: dict) -> str:
        pts = p.get("path_points", [])
        if not pts:
            return "    // ! 扫掠缺少路径点"
        pts_str = ", ".join([f"new Point3d({float(pt[0])}, {float(pt[1])}, {float(pt[2])})" for pt in pts])
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
        return f'    m.Tool_BooleanUnite("{p.get("target_body", "")}", "{p.get("tool_body", "")}");'

    def _gen_boolean_subtract(self, p: dict) -> str:
        return f'    m.Tool_BooleanSubtract("{p.get("target_body", "")}", "{p.get("tool_body", "")}");'

    def _gen_boolean_intersect(self, p: dict) -> str:
        return f'    m.Tool_BooleanIntersect("{p.get("target_body", "")}", "{p.get("tool_body", "")}");'

    # ═══════════════════════════════════════════════════════════════════════
    # 细节特征
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_chamfer(self, p: dict) -> str:
        return f"    m.Tool_Chamfer({float(p.get('length', 2.0))});"

    def _gen_fillet(self, p: dict) -> str:
        return f"    m.Tool_Fillet({float(p.get('radius', 5.0))});"

    def _gen_edge_blend(self, p: dict) -> str:
        r = p.get("radius", 5.0)
        edges = p.get("edge_indices", [])
        if not edges:
            return f"    m.Tool_Fillet({float(r)});"
        es = ", ".join([str(int(e)) for e in edges])
        return f"    m.Tool_EdgeBlend({float(r)}, new int[]{{{es}}});"

    def _gen_shell(self, p: dict) -> str:
        t = p.get("thickness", 2.0); fi = p.get("remove_face_index", -1)
        return f"    m.Tool_Shell({float(t)}, {int(fi)});"

    def _gen_hole(self, p: dict) -> str:
        x = p.get("x", 0.0); y = p.get("y", 0.0)
        d = p.get("diameter", 10.0); dp = p.get("depth", 20.0)
        ht = p.get("hole_type", "simple")
        return f'    m.Tool_Hole({float(x)}, {float(y)}, {float(d)}, {float(dp)}, "{ht}");'

    def _gen_pocket(self, p: dict) -> str:
        x = p.get("x", 0.0); y = p.get("y", 0.0)
        l = p.get("length", 50.0); w = p.get("width", 30.0); d = p.get("depth", 10.0)
        return f"    m.Tool_Pocket({float(x)}, {float(y)}, {float(l)}, {float(w)}, {float(d)});"

    def _gen_boss(self, p: dict) -> str:
        x = p.get("x", 0.0); y = p.get("y", 0.0)
        d = p.get("diameter", 20.0); h = p.get("height", 30.0)
        return f"    m.Tool_Boss({float(x)}, {float(y)}, {float(d)}, {float(h)});"

    def _gen_pad(self, p: dict) -> str:
        x = p.get("x", 0.0); y = p.get("y", 0.0)
        l = p.get("length", 40.0); w = p.get("width", 20.0); h = p.get("height", 15.0)
        return f"    m.Tool_Pad({float(x)}, {float(y)}, {float(l)}, {float(w)}, {float(h)});"

    def _gen_slot(self, p: dict) -> str:
        x = p.get("x", 0.0); y = p.get("y", 0.0)
        l = p.get("length", 60.0); w = p.get("width", 10.0); d = p.get("depth", 5.0)
        return f"    m.Tool_Slot({float(x)}, {float(y)}, {float(l)}, {float(w)}, {float(d)});"

    def _gen_groove(self, p: dict) -> str:
        d = p.get("diameter", 30.0); w = p.get("width", 5.0); dp = p.get("depth", 3.0)
        return f"    m.Tool_Groove({float(d)}, {float(w)}, {float(dp)});"

    def _gen_thread(self, p: dict) -> str:
        ref = p.get("cylinder_ref", ""); tp = p.get("thread_type", "metric"); l = p.get("length", 20.0)
        return f'    m.Tool_Thread("{ref}", "{tp}", {float(l)});'

    def _gen_pattern_linear(self, p: dict) -> str:
        ref = p.get("feature_ref", "")
        cx = p.get("count_x", 2); sx = p.get("spacing_x", 50.0)
        cy = p.get("count_y", 1); sy = p.get("spacing_y", 0.0)
        return f'    m.Tool_PatternLinear("{ref}", {int(cx)}, {float(sx)}, {int(cy)}, {float(sy)});'

    def _gen_pattern_circular(self, p: dict) -> str:
        ref = p.get("feature_ref", ""); cnt = p.get("count", 6); a = p.get("angle", 360.0)
        return f'    m.Tool_PatternCircular("{ref}", {int(cnt)}, {float(a)});'

    def _gen_mirror_feature(self, p: dict) -> str:
        ref = p.get("feature_ref", ""); pl = p.get("mirror_plane", "YZ")
        return f'    m.Tool_MirrorFeature("{ref}", "{pl}");'

    # ═══════════════════════════════════════════════════════════════════════
    # 曲面建模
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_through_curves(self, p: dict) -> str:
        sections = p.get("sections", [])
        if not sections:
            return "    // ! 通过曲线组缺少截面"
        rs = ", ".join([f'"{r}"' for r in sections])
        return f"    m.Tool_ThroughCurves(new string[]{{{rs}}});"

    def _gen_through_curve_mesh(self, p: dict) -> str:
        pri = p.get("primary_curves", []); cross = p.get("cross_curves", [])
        if not pri or not cross:
            return "    // ! 通过曲线网格缺少曲线"
        ps = ", ".join([f'"{r}"' for r in pri]); cs = ", ".join([f'"{r}"' for r in cross])
        return f"    m.Tool_ThroughCurveMesh(new string[]{{{ps}}}, new string[]{{{cs}}});"

    def _gen_ruled(self, p: dict) -> str:
        return f'    m.Tool_Ruled("{p.get("curve1_ref", "")}", "{p.get("curve2_ref", "")}");'

    def _gen_bounded_plane(self, p: dict) -> str:
        curves = p.get("boundary_curves", [])
        if not curves:
            return "    // ! 有界平面缺少边界曲线"
        rs = ", ".join([f'"{r}"' for r in curves])
        return f"    m.Tool_BoundedPlane(new string[]{{{rs}}});"

    def _gen_fill_surface(self, p: dict) -> str:
        curves = p.get("boundary_curves", [])
        if not curves:
            return "    // ! 填充曲面缺少边界曲线"
        rs = ", ".join([f'"{r}"' for r in curves])
        return f"    m.Tool_FillSurface(new string[]{{{rs}}});"

    def _gen_offset_surface(self, p: dict) -> str:
        return f'    m.Tool_OffsetSurface("{p.get("face_ref", "")}", {float(p.get("distance", 5.0))});'

    def _gen_extension(self, p: dict) -> str:
        return f'    m.Tool_Extension("{p.get("face_ref", "")}", "{p.get("edge_ref", "")}", {float(p.get("length", 10.0))});'

    def _gen_trim_surface(self, p: dict) -> str:
        face = p.get("face_ref", ""); curves = p.get("boundary_curves", [])
        if not curves:
            return "    // ! 修剪曲面缺少边界曲线"
        rs = ", ".join([f'"{r}"' for r in curves])
        return f'    m.Tool_TrimSurface("{face}", new string[]{{{rs}}});'

    def _gen_face_blend(self, p: dict) -> str:
        f1 = p.get("face1_ref", ""); f2 = p.get("face2_ref", ""); r = p.get("radius", 10.0)
        return f'    m.Tool_FaceBlend("{f1}", "{f2}", {float(r)});'

    # ═══════════════════════════════════════════════════════════════════════
    # 变换操作
    # ═══════════════════════════════════════════════════════════════════════

    def _gen_translate(self, p: dict) -> str:
        dx = p.get("dx", 0.0); dy = p.get("dy", 0.0); dz = p.get("dz", 0.0)
        return f"    m.Tool_Translate({float(dx)}, {float(dy)}, {float(dz)});"

    def _gen_rotate(self, p: dict) -> str:
        axis = p.get("axis", "Z"); angle = p.get("angle", 90.0)
        return f"    m.Tool_Rotate({float(angle)}, \"{axis}\");"

    def _gen_scale(self, p: dict) -> str:
        return f"    m.Tool_Scale({float(p.get('factor', 1.0))});"

# ═══════════════════════════════════════════════════════════════════════
# 装配 Journal
#
# 装配不是"往 NXModeler 里加方法"能解决的：它需要 NXOpen.Assemblies 命名空间、
# 需要先把装配体设为工作部件，而且入口是 ComponentAssembly 而不是 Part。
# 因此这里单独生成一份自包含的 Journal（类名固定为 NXJournal，NX 约定的入口类）。
#
# NX 官方 Matrix3x3 约定（NXOpen.xml，ComponentAssembly 类说明）：
#   "The first column of the matrix specifies the X axis, the second the Y
#    axis, and the third the Z axis."
# 对应字段即为 Xx,Xy,Xz = 组件 X 轴向量；Yx,Yy,Yz = Y 轴；Zx,Zy,Zz = Z 轴。
# ═══════════════════════════════════════════════════════════════════════


def _cs_verbatim(text: str) -> str:
    """转义为 C# 逐字字符串（@"..."）的内容。

    逐字字符串里反斜杠是字面量，所以 Windows 路径必须原样保留、不能翻倍；
    只需把双引号写成两个双引号。
    """
    return str(text).replace('"', '""')


_ASSEMBLY_JOURNAL_TEMPLATE = r'''using System;
using System.Globalization;
using System.IO;
using NXOpen;
using NXOpen.Assemblies;

// Generated by backend/journal/generator.py
// Flow: new/open assembly -> add component (position + orientation) -> verify -> save
public class NXJournal
{
    static string reportPath = @"@@REPORT@@";

    static void Log(string msg)
    {
        Console.WriteLine("### " + msg);
        if (reportPath.Length > 0)
        {
            try { File.AppendAllText(reportPath, msg + Environment.NewLine); }
            catch (Exception) { }
        }
    }

    static string Num(double v)
    {
        return v.ToString("0.######", CultureInfo.InvariantCulture);
    }

    public static void Main(string[] args)
    {
        Session session = Session.GetSession();
        try { session.ListingWindow.Open(); }
        catch (Exception) { }

        string assemblyPath = @"@@ASSEMBLY@@";
        string partPath = @"@@PART@@";
        string componentName = "@@NAME@@";
        string[] refsets = new string[] { @@REFSETS@@ };

        // Parts that are themselves assemblies reference their children by name,
        // and NX resolves those relative to the referencing part's folder. When we
        // work on a copy that lives elsewhere, add the original folder to the search
        // path so sibling components (screws, plates, ...) still resolve.
        string[] searchDirs = new string[] { @@SEARCH_DIRS@@ };
        if (searchDirs.Length > 0)
        {
            bool[] searchSubDirs = new bool[searchDirs.Length];
            for (int i = 0; i < searchSubDirs.Length; i++) { searchSubDirs[i] = false; }
            try
            {
                session.Parts.LoadOptions.SetSearchDirectories(searchDirs, searchSubDirs);
                Log("SEARCH_DIRS " + searchDirs.Length);
            }
            catch (Exception ex) { Log("WARN SetSearchDirectories failed: " + ex.Message); }
        }

        Log("START create_new=@@CREATE_NEW@@ assembly=" + assemblyPath);
        Log("START component_part=" + partPath);

        Part assemblyPart = null;
        if (@@CREATE_NEW@@)
        {
            assemblyPart = session.Parts.NewDisplay(assemblyPath, Part.Units.Millimeters);
            Log("NEW assembly part created: " + assemblyPart.FullPath);
        }
        else
        {
            PartLoadStatus openStatus;
            assemblyPart = session.Parts.OpenDisplay(assemblyPath, out openStatus);
            Log("OPENED assembly part: " + assemblyPart.FullPath);
        }

        try { session.Parts.SetWork(assemblyPart); }
        catch (Exception ex) { Log("WARN SetWork failed: " + ex.Message); }

        Point3d basePoint = new Point3d(@@PX@@, @@PY@@, @@PZ@@);
        Matrix3x3 orientation = new Matrix3x3();
        orientation.Xx = @@O0@@; orientation.Xy = @@O1@@; orientation.Xz = @@O2@@;
        orientation.Yx = @@O3@@; orientation.Yy = @@O4@@; orientation.Yz = @@O5@@;
        orientation.Zx = @@O6@@; orientation.Zy = @@O7@@; orientation.Zz = @@O8@@;

        Component comp = null;
        string usedRefset = "";
        string lastError = "";
        PartLoadStatus loadStatus = null;

        for (int i = 0; i < refsets.Length; i++)
        {
            try
            {
                comp = assemblyPart.ComponentAssembly.AddComponent(
                    partPath, refsets[i], componentName, basePoint, orientation, @@LAYER@@, out loadStatus);
                usedRefset = refsets[i];
                break;
            }
            catch (NXException ex)
            {
                lastError = ex.Message;
                comp = null;
            }
        }

        if (comp == null)
        {
            Log("ERROR AddComponent failed. Last error: " + lastError);
            Log("FAILED");
            return;
        }

        if (loadStatus != null)
        {
            Log("ADDED component=" + comp.Name + " refset=[" + usedRefset
                + "] unloaded_parts=" + loadStatus.NumberUnloadedParts);
            // Surface unresolved sub-components instead of letting them slip by:
            // the assembly is still valid, but geometry would be missing.
            for (int i = 0; i < loadStatus.NumberUnloadedParts; i++)
            {
                Log("UNLOADED " + loadStatus.GetPartName(i)
                    + " :: " + loadStatus.GetStatusDescription(i));
            }
        }
        else
        {
            Log("ADDED component=" + comp.Name + " refset=[" + usedRefset + "]");
        }

        // Read back the transform NX actually recorded for this component
        Point3d gotPos;
        Matrix3x3 gotOri;
        comp.GetPosition(out gotPos, out gotOri);
        Log("VERIFY_POS " + Num(gotPos.X) + " " + Num(gotPos.Y) + " " + Num(gotPos.Z));
        Log("VERIFY_ORI " + Num(gotOri.Xx) + " " + Num(gotOri.Xy) + " " + Num(gotOri.Xz) + " "
                          + Num(gotOri.Yx) + " " + Num(gotOri.Yy) + " " + Num(gotOri.Yz) + " "
                          + Num(gotOri.Zx) + " " + Num(gotOri.Zy) + " " + Num(gotOri.Zz));
        Log("VERIFY_REF " + comp.ReferenceSet);
        Log("VERIFY_DISPLAY " + comp.DisplayName);

        PartSaveStatus saveStatus = assemblyPart.Save(BasePart.SaveComponents.True, BasePart.CloseAfterSave.False);
        Log("SAVED " + assemblyPart.FullPath + " unsaved_parts=" + saveStatus.NumberUnsavedParts);
        Log("DONE");
    }
}
'''


def generate_assembly_journal(params: dict) -> str:
    """生成「新建/打开装配体 → 插入组件 → 回读校验 → 保存」的 C# Journal。

    params:
        assembly_path  (str): 目标装配体 .prt 绝对路径
        part_path      (str): 被装配的 .prt 绝对路径
        position       ([x, y, z]): 组件原点在装配体世界坐标系中的位置
        orientation    ([9 个 float]): 3x3 姿态矩阵，按 NX 的"列序"展开：
                       [Xx, Xy, Xz, Yx, Yy, Yz, Zx, Zy, Zz]
                       第 1 列 = 组件 X 轴，第 2 列 = Y 轴，第 3 列 = Z 轴。
                       （绕 Z 轴转 +90° 即 X 轴指向 +Y：(0,1,0, -1,0,0, 0,0,1)）
        component_name (str): 组件名，默认 "COMPONENT"
        reference_sets (list[str]): 参考集候选列表，按顺序尝试；
                       默认 ["MODEL", "Entire Part", ""]，前一个失败自动回退。
        layer          (int): 图层。-1 = 沿用原部件图层（默认）；0 = 工作图层；1-256 = 指定图层。
        create_new     (bool): True 用 NewDisplay 新建装配体；False 打开已有装配体文件。
        search_dirs    (list[str]): 额外的部件搜索目录。被装配的部件如果本身是装配体，
                       它的子组件是按"引用方所在目录"解析的；当我们在别处操作副本时，
                       把原目录加进来，兄弟部件（螺钉、压板等）才找得到。
        report_path    (str): 可选。Journal 会同时把日志写进该文件，
                       这样即使 stdout 被吞掉也能核对执行结果。

    Returns:
        str: 完整的 C# Journal 源码（UTF-8 BOM 由 executor 负责写入）
    """
    pos = list(params["position"])
    ori = list(params["orientation"])
    if len(pos) != 3:
        raise ValueError(f"position 需要 3 个数，收到 {len(pos)} 个")
    if len(ori) != 9:
        raise ValueError(f"orientation 需要 9 个数（3x3），收到 {len(ori)} 个")

    refsets = params.get("reference_sets") or ["MODEL", "Entire Part", ""]
    refsets_cs = ", ".join(f'"{_cs_verbatim(r)}"' for r in refsets)

    search_dirs = [d for d in (params.get("search_dirs") or []) if d]
    search_dirs_cs = ", ".join(f'@"{_cs_verbatim(d)}"' for d in search_dirs)

    replacements = {
        "@@REPORT@@": _cs_verbatim(params.get("report_path", "")),
        "@@ASSEMBLY@@": _cs_verbatim(params["assembly_path"]),
        "@@PART@@": _cs_verbatim(params["part_path"]),
        "@@NAME@@": _cs_verbatim(params.get("component_name", "COMPONENT")),
        "@@REFSETS@@": refsets_cs,
        "@@SEARCH_DIRS@@": search_dirs_cs,
        "@@CREATE_NEW@@": "true" if params.get("create_new", True) else "false",
        "@@PX@@": repr(float(pos[0])),
        "@@PY@@": repr(float(pos[1])),
        "@@PZ@@": repr(float(pos[2])),
        "@@LAYER@@": str(int(params.get("layer", -1))),
    }
    for i, value in enumerate(ori):
        replacements[f"@@O{i}@@"] = repr(float(value))

    code = _ASSEMBLY_JOURNAL_TEMPLATE
    for token, value in replacements.items():
        code = code.replace(token, value)

    leftover = [t for t in ("@@",) if t in code]
    if leftover:
        raise ValueError("装配 Journal 模板仍有未替换的占位符")
    return code

# ═══════════════════════════════════════════════════════════════════════
# 表达式 Journal
#
# 为什么不复用 NXModeler：更新表达式是"打开一个已存在的部件 → 改 RHS →
# 更新 → 保存"，生命周期和 NXModeler 那套"新建部件再建模"正好相反，
# 所以同样单独生成一份自包含 Journal。
#
# 用到的 API（均经 NX 11 NXOpen.dll 反射确认）：
#   BasePart.Expressions : ExpressionCollection
#   ExpressionCollection.FindObject(string) -> Expression（找不到返回 null）
#   ExpressionCollection.Edit(Expression, string newRightHandSide)
#   Session.SetUndoMark / UpdateManager.DoUpdate(UndoMarkId) / DeleteUndoMark
#   BasePart.Save(SaveComponents, CloseAfterSave) / SaveAs(string)
# ═══════════════════════════════════════════════════════════════════════


def _cs_quoted(text: str) -> str:
    """转义为 C# 普通字符串字面量的内容（首尾引号由调用方补）。"""
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


def format_expression_rhs(value) -> str:
    """把表达式新值转成 NX 能接受的右端字符串（RHS）。

    数字 → 紧凑十进制（100.0 → "100"，12.5 → "12.5"）；
    字符串 → 原样透传，这样可以传公式，例如 "d1*2"。
    """
    if isinstance(value, bool):
        raise ValueError("表达式值不支持布尔类型")
    if isinstance(value, str):
        return value
    return f"{float(value):.10g}"


_EXPRESSION_JOURNAL_TEMPLATE = r'''using System;
using System.Globalization;
using System.IO;
using NXOpen;

// Generated by backend/journal/generator.py
// Flow: open existing part -> edit expressions -> update -> save / SaveAs
public class NXJournal
{
    static string reportPath = @"@@REPORT@@";

    static int updated = 0;
    static int failed = 0;

    static void Log(string msg)
    {
        Console.WriteLine("### " + msg);
        if (reportPath.Length > 0)
        {
            try { File.AppendAllText(reportPath, msg + Environment.NewLine); }
            catch (Exception) { }
        }
    }

    static void EditExpr(BasePart workPart, string name, string rhs)
    {
        // FindObject throws NXException ("No object found with this name") when the
        // expression is absent -- it does not return null. Catch it so one bad name
        // is reported instead of aborting the whole journal.
        Expression expr;
        try
        {
            expr = workPart.Expressions.FindObject(name);
        }
        catch (Exception)
        {
            expr = null;
        }

        if (expr == null)
        {
            Log("EXPR_MISSING " + name);
            failed = failed + 1;
            return;
        }

        string oldRhs = expr.RightHandSide;
        try
        {
            workPart.Expressions.Edit(expr, rhs);
            Log("EXPR_OK " + name + " [" + oldRhs + "] -> [" + expr.RightHandSide + "]");
            updated = updated + 1;
        }
        catch (Exception ex)
        {
            Log("EXPR_ERR " + name + " : " + ex.Message);
            failed = failed + 1;
        }
    }

    public static void Main(string[] args)
    {
        Session session = Session.GetSession();
        try { session.ListingWindow.Open(); } catch (Exception) { }

        string partPath = @"@@PART@@";
        Log("OPEN " + partPath);

        PartLoadStatus loadStatus;
        Part workPart = session.Parts.OpenDisplay(partPath, out loadStatus);
        try { session.Parts.SetWork(workPart); } catch (Exception) { }
        Log("EXPR_TOTAL @@COUNT@@");

        // UndoMarkId is nested inside Session, so it must be qualified.
        // The mark has to be created BEFORE the edits: DoUpdate(markId) then
        // regenerates everything that changed since that mark. Setting the
        // mark afterwards makes DoUpdate throw "Update undo happened".
        Session.UndoMarkId markId = session.SetUndoMark(
            Session.MarkVisibility.Visible, "Update expression data");

@@CALLS@@

        // All-or-nothing: if any expression failed, skip update+save so the part
        // never ends up with only half of the requested parameters applied.
        if (failed > 0)
        {
            Log("SUMMARY updated=" + updated + " failed=" + failed);
            Log("FAILED");
            return;
        }

        // DoUpdate rolls back to markId and throws if any feature fails to
        // regenerate. Turn that into a readable reason instead of the bare
        // "Update undo happened" message.
        try
        {
            session.UpdateManager.DoUpdate(markId);
            Log("MODEL_UPDATED");
        }
        catch (Exception ex)
        {
            Log("UPDATE_ERR " + ex.Message);
            try
            {
                ErrorList errs = session.UpdateManager.ErrorList;
                if (errs != null)
                {
                    for (int i = 0; i < errs.Length; i++)
                    {
                        ErrorInfo info = errs.GetErrorInfo(i);
                        Log("UPDATE_FAIL code=" + info.ErrorCode
                            + " obj=[" + info.ErrorObjectDescription + "]"
                            + " desc=" + info.Description);
                    }
                }
            }
            catch (Exception) { }
            Log("SUMMARY updated=" + updated + " failed=" + failed);
            Log("FAILED");
            return;
        }

        try { session.DeleteUndoMark(markId, "Update expression data"); }
        catch (Exception) { }

        PartSaveStatus saveStatus;
@@SAVE@@
        Log("SUMMARY updated=" + updated + " failed=" + failed);
        Log("DONE");
    }
}
'''


def generate_expression_journal(params: dict) -> str:
    """生成「打开已有部件 → 批量更新表达式 → 更新 → 保存」的 C# Journal。

    params:
        part_path    (str): 要修改的 .prt 绝对路径
        expressions  (list): [{"name": "d1", "value": 100.0}, ...]
                       value 可以是数字，也可以是公式字符串（如 "d1*2"）。
        output_path  (str): 可选。给了就 SaveAs 到该路径（不动原部件）；
                       留空则原地保存。
        report_path  (str): 可选。日志同时写入该文件，便于脱离 stdout 核对。

    Returns:
        str: 完整的 C# Journal 源码
    """
    expressions = list(params["expressions"])
    if not expressions:
        raise ValueError("expressions 不能为空")

    calls = []
    for exp in expressions:
        name = _cs_quoted(exp["name"])
        rhs = _cs_quoted(format_expression_rhs(exp["value"]))
        calls.append(f'        EditExpr(workPart, "{name}", "{rhs}");')

    output_path = params.get("output_path", "")
    if output_path:
        save_block = (
            f'        saveStatus = workPart.SaveAs(@"{_cs_verbatim(output_path)}");\n'
            '        Log("SAVED_AS " + workPart.FullPath'
            ' + " unsaved_parts=" + saveStatus.NumberUnsavedParts);'
        )
    else:
        save_block = (
            "        saveStatus = workPart.Save(BasePart.SaveComponents.True,"
            " BasePart.CloseAfterSave.False);\n"
            '        Log("SAVED " + workPart.FullPath'
            ' + " unsaved_parts=" + saveStatus.NumberUnsavedParts);'
        )

    replacements = {
        "@@REPORT@@": _cs_verbatim(params.get("report_path", "")),
        "@@PART@@": _cs_verbatim(params["part_path"]),
        "@@COUNT@@": str(len(expressions)),
        "@@CALLS@@": "\n".join(calls),
        "@@SAVE@@": save_block,
    }

    code = _EXPRESSION_JOURNAL_TEMPLATE
    for token, value in replacements.items():
        code = code.replace(token, value)

    if "@@" in code:
        raise ValueError("表达式 Journal 模板仍有未替换的占位符")
    return code


# ═══════════════════════════════════════════════════════════════════════
# 拍平 Journal（装配体 → 单一部件）
#
# 目标：把一个装配体变成"一个 .prt 装下所有几何"，不再有装配树。
#
# 为什么用 PartImporter（= 菜单里的「文件 → 导入 → 部件」）：
#   NX 11 没有 ExtractGeometryBuilder，Component 也不暴露自己的 occurrence 几何，
#   把"原型部件的 Body"直接喂给 WorkPart 的提取构建器会 NullReferenceException
#   （跨部件不成立）。PartImporter 是 NX 11 里唯一能"按坐标系把另一个 .prt 的
#   几何搬进当前工作部件"的公开 API，而且搬进来的是真特征，不是引用。
#
# 变换：component.GetPosition() 给的是相对父组件的位姿，嵌套装配必须逐层累乘：
#   R_abs = R_parent * R_local
#   t_abs = R_parent * t_local + t_parent
#   （PartImporter.DestinationCoordinateSystem 只吃 NXMatrix，即只有姿态；
#     平移由 DestinationPoint 承担。）
#
# 顺序：先导入全部几何，再移除组件。移除后 RootComponent 会变成 null，
#       所以移除之前先把组件名抄下来，之后不要再碰 Component 对象
#       （否则 "Attempt to use an object that is not alive"）。
#
# 全有或全无：任何一次导入失败就整篇不保存，绝不留下"拍平了一半"的部件。
# ═══════════════════════════════════════════════════════════════════════

_FLATTEN_JOURNAL_TEMPLATE = r'''using System;
using System.IO;
using System.Collections.Generic;
using NXOpen;
using NXOpen.Assemblies;

// Generated by backend/journal/generator.py
// Flow: open assembly -> import every component's part at its absolute
//       transform -> remove all components -> save a single flat part
public class NXJournal
{
    static string reportPath = @"@@REPORT@@";
    static int imported = 0;
    static int failed = 0;

    static void Log(string msg)
    {
        Console.WriteLine("### " + msg);
        if (reportPath.Length > 0)
        {
            try { File.AppendAllText(reportPath, msg + Environment.NewLine); }
            catch (Exception) { }
        }
    }

    static Matrix3x3 Ident()
    {
        Matrix3x3 m = new Matrix3x3();
        m.Xx = 1; m.Xy = 0; m.Xz = 0;
        m.Yx = 0; m.Yy = 1; m.Yz = 0;
        m.Zx = 0; m.Zy = 0; m.Zz = 1;
        return m;
    }

    // matrix product; each Matrix3x3 is treated as columns X|Y|Z
    static Matrix3x3 Mul(Matrix3x3 a, Matrix3x3 b)
    {
        Matrix3x3 r = new Matrix3x3();
        r.Xx = a.Xx * b.Xx + a.Yx * b.Xy + a.Zx * b.Xz;
        r.Xy = a.Xy * b.Xx + a.Yy * b.Xy + a.Zy * b.Xz;
        r.Xz = a.Xz * b.Xx + a.Yz * b.Xy + a.Zz * b.Xz;
        r.Yx = a.Xx * b.Yx + a.Yx * b.Yy + a.Zx * b.Yz;
        r.Yy = a.Xy * b.Yx + a.Yy * b.Yy + a.Zy * b.Yz;
        r.Yz = a.Xz * b.Yx + a.Yz * b.Yy + a.Zz * b.Yz;
        r.Zx = a.Xx * b.Zx + a.Yx * b.Zy + a.Zx * b.Zz;
        r.Zy = a.Xy * b.Zx + a.Yy * b.Zy + a.Zy * b.Zz;
        r.Zz = a.Xz * b.Zx + a.Yz * b.Zy + a.Zz * b.Zz;
        return r;
    }

    static Point3d Apply(Matrix3x3 r, Point3d t, Point3d p)
    {
        return new Point3d(
            r.Xx * p.X + r.Yx * p.Y + r.Zx * p.Z + t.X,
            r.Xy * p.X + r.Yy * p.Y + r.Zy * p.Z + t.Y,
            r.Xz * p.X + r.Yz * p.Y + r.Zz * p.Z + t.Z);
    }

    static string Num(double v)
    {
        return v.ToString("0.######", System.Globalization.CultureInfo.InvariantCulture);
    }

    static void Collect(Component[] comps, Point3d parentT, Matrix3x3 parentR,
                        List<string> paths, List<Point3d> poss, List<Matrix3x3> oris,
                        List<string> unresolved, List<string> nested)
    {
        foreach (Component c in comps)
        {
            Point3d lp; Matrix3x3 lr;
            c.GetPosition(out lp, out lr);

            Point3d absT = Apply(parentR, parentT, lp);
            Matrix3x3 absR = Mul(parentR, lr);

            string dispName = "?";
            try { dispName = c.DisplayName; } catch (Exception) { }

            Part proto = c.Prototype as Part;
            if (proto != null)
            {
                // 记录"组件部件自己也是个装配体"的情况。PartImporter 无法导入一个
                // 已经加载、且自身含组件的部件（会抛 "Update undo happened"），
                // 所以这种情况要提前认出来，好在失败时给出可操作的原因。
                bool protoIsAssembly = false;
                try { protoIsAssembly = (proto.ComponentAssembly.RootComponent != null); }
                catch (Exception) { }
                if (protoIsAssembly) { nested.Add(dispName); Log("NESTED_SUBASSEMBLY " + dispName); }

                paths.Add(proto.FullPath);
                poss.Add(absT);
                oris.Add(absR);
            }
            else
            {
                // 组件部件没解析出来（未加载 / 找不到文件）：它的几何无法导入。
                // 这里必须算失败，绝不能"跳过导入却照样删组件"——那等于静默丢几何。
                unresolved.Add(dispName);
                Log("UNRESOLVED " + dispName + " (component part not loaded)");
            }

            Collect(c.GetChildren(), absT, absR, paths, poss, oris, unresolved, nested);
        }
    }

    static bool SaveFlat(Part root, string outputPath)
    {
        try
        {
            if (outputPath.Length > 0)
            {
                PartSaveStatus s = root.SaveAs(outputPath);
                Log("SAVED_AS " + root.FullPath + " unsaved_parts=" + s.NumberUnsavedParts);
            }
            else
            {
                PartSaveStatus s = root.Save(BasePart.SaveComponents.True, BasePart.CloseAfterSave.False);
                Log("SAVED " + root.FullPath + " unsaved_parts=" + s.NumberUnsavedParts);
            }
            return true;
        }
        catch (Exception ex)
        {
            Log("SAVE_ERR " + ex.Message);
            return false;
        }
    }

    public static void Main(string[] args)
    {
        Session session = Session.GetSession();
        try { session.ListingWindow.Open(); } catch (Exception) { }

        string partPath = @"@@PART@@";
        string outputPath = @"@@OUTPUT@@";
        string[] searchDirs = new string[] { @@SEARCH_DIRS@@ };

        if (searchDirs.Length > 0)
        {
            bool[] searchSubDirs = new bool[searchDirs.Length];
            for (int i = 0; i < searchSubDirs.Length; i++) { searchSubDirs[i] = false; }
            try
            {
                session.Parts.LoadOptions.SetSearchDirectories(searchDirs, searchSubDirs);
                Log("SEARCH_DIRS " + searchDirs.Length);
            }
            catch (Exception ex) { Log("WARN SetSearchDirectories failed: " + ex.Message); }
        }

        Log("OPEN " + partPath);
        // 全量加载：组件部件若是"部分加载/轻量化"，component.Prototype 就不是 Part，
        // 拿不到几何。拍平必须先把整棵装配树真正读进来。
        try
        {
            session.Parts.LoadOptions.UsePartialLoading = false;
            session.Parts.LoadOptions.UseLightweightRepresentations = false;
            session.Parts.LoadOptions.ComponentsToLoad = LoadOptions.LoadComponents.All;
            // 组件默认按"保存时的目录"解析；副本/移动过的场景下必须改成按搜索目录解析，
            // 否则 component.Prototype 只是占位符，拿不到几何。
            session.Parts.LoadOptions.ComponentLoadMethod = LoadOptions.LoadMethod.SearchDirectories;
            Log("LOAD_OPTIONS full+searchdirs");
        }
        catch (Exception ex) { Log("WARN SetLoadOptions failed: " + ex.Message); }

        PartLoadStatus loadStatus;
        Part root = session.Parts.OpenDisplay(partPath, out loadStatus);
        try { session.Parts.SetWork(root); } catch (Exception ex) { Log("WARN SetWork failed: " + ex.Message); }

        int bodiesBefore = root.Bodies.ToArray().Length;
        Log("BODIES_BEFORE " + bodiesBefore);

        Component rootComp = null;
        try { rootComp = root.ComponentAssembly.RootComponent; }
        catch (Exception ex) { Log("WARN RootComponent failed: " + ex.Message); }

        if (rootComp == null)
        {
            Log("NO_COMPONENTS already a flat part; nothing to merge");
            if (!SaveFlat(root, outputPath)) { Log("FAILED"); return; }
            Log("SUMMARY imported=0 failed=0");
            Log("DONE");
            return;
        }

        Component[] top = rootComp.GetChildren();
        Log("TOP_COMPONENTS " + top.Length);
        if (top.Length == 0)
        {
            Log("NO_COMPONENTS already a flat part; nothing to merge");
            if (!SaveFlat(root, outputPath)) { Log("FAILED"); return; }
            Log("SUMMARY imported=0 failed=0");
            Log("DONE");
            return;
        }

        // 注意：这里刻意不调用 ComponentAssembly.OpenComponents()。
        // 靠 LoadOptions（全量加载 + 按搜索目录解析）已经足够把组件解析成真正的 Part。

        List<string> paths = new List<string>();
        List<Point3d> poss = new List<Point3d>();
        List<Matrix3x3> oris = new List<Matrix3x3>();
        List<string> unresolved = new List<string>();
        List<string> nested = new List<string>();
        Collect(top, new Point3d(0, 0, 0), Ident(), paths, poss, oris, unresolved, nested);
        Log("TO_IMPORT " + paths.Count);

        // 有任何一个组件的部件没解析出来就整体放弃：宁可什么都不做，
        // 也不能交出一个"组件删了、几何没了"的空壳部件。
        if (unresolved.Count > 0)
        {
            Log("SUMMARY unresolved=" + unresolved.Count
                + " [" + string.Join("; ", unresolved.ToArray()) + "]");
            Log("FAILED");
            return;
        }

        // 先移除组件、再导入几何。
        // 为什么顺序是这个：如果一个部件此刻正作为本装配体的组件处于加载状态，
        // 而它自己也是个装配体，那么对它做 PartImporter 会触发 NX 的
        // "Update undo happened"（导入的更新周期与既存 occurrence 冲突）。
        // 先把组件摘掉，这些部件就退回成"磁盘上的一个普通部件"，导入即可正常完成。
        // 路径与位姿在 Collect 阶段已经抄好，移除组件不会影响后续导入。
        // RemoveComponent 会销毁 Component 对象，所以先抄名字、之后不再触碰。
        List<string> names = new List<string>();
        foreach (Component c in top) names.Add(c.DisplayName);
        for (int i = 0; i < top.Length; i++)
        {
            try
            {
                root.ComponentAssembly.RemoveComponent(top[i]);
                Log("REMOVED " + names[i]);
            }
            catch (Exception ex) { Log("REMOVE_ERR " + names[i] + " : " + ex.Message); }
        }

        Component after = null;
        try { after = root.ComponentAssembly.RootComponent; } catch (Exception) { }
        Log("TOP_COMPONENTS_AFTER " + (after == null ? 0 : after.GetChildren().Length));

        ImportManager im = root.ImportManager;
        for (int i = 0; i < paths.Count; i++)
        {
            try
            {
                PartImporter pi = im.CreatePartImporter();
                pi.FileName = paths[i];
                pi.LayerOption = PartImporter.LayerOptionType.Original;
                pi.DestinationCoordinateSystem = root.NXMatrices.Create(oris[i]);
                pi.DestinationPoint = poss[i];
                pi.DestinationCoordinateSystemSpecification =
                    PartImporter.DestinationCoordinateSystemSpecificationType.Specified;
                pi.Commit();
                pi.Destroy();
                imported = imported + 1;
                Log("IMPORTED " + paths[i]
                    + " at " + Num(poss[i].X) + "," + Num(poss[i].Y) + "," + Num(poss[i].Z));
            }
            catch (Exception ex)
            {
                failed = failed + 1;
                Log("IMPORT_ERR " + paths[i] + " : " + ex.Message);
            }
        }

        // All-or-nothing: a partially imported assembly is worse than none.
        // 这里不保存，磁盘上的原文件保持不动（只是内存里的会话被改脏了）。
        if (failed > 0)
        {
            Log("SUMMARY imported=" + imported + " failed=" + failed);
            Log("FAILED");
            return;
        }

        Log("BODIES_AFTER " + root.Bodies.ToArray().Length);

        if (!SaveFlat(root, outputPath)) { Log("FAILED"); return; }

        Log("SUMMARY imported=" + imported + " failed=" + failed);
        Log("DONE");
    }
}
'''


def generate_flatten_journal(params: dict) -> str:
    """生成「打开装配体 → 逐个导入组件几何 → 移除组件 → 保存为单一部件」的 Journal。

    params:
        part_path   (str): 要拍平的装配体 .prt 绝对路径
        output_path (str): 可选。给了就另存为该路径；留空则原地保存。
        search_dirs (list[str]): 额外的部件搜索目录（副本场景下补原目录）。
        report_path (str): 可选。日志同时写入该文件。

    Returns:
        str: 完整的 C# Journal 源码
    """
    # 按搜索目录解析组件时，被打开部件自己所在目录必须在内，
    # 否则"兄弟部件就在旁边"这种最常见的情况反而找不到。
    search_dirs = [d for d in (params.get("search_dirs") or []) if d]
    part_dir = os.path.dirname(params["part_path"])
    if part_dir and part_dir not in search_dirs:
        search_dirs.insert(0, part_dir)
    search_dirs_cs = ", ".join(f'@"{_cs_verbatim(d)}"' for d in search_dirs)

    replacements = {
        "@@REPORT@@": _cs_verbatim(params.get("report_path", "")),
        "@@PART@@": _cs_verbatim(params["part_path"]),
        "@@OUTPUT@@": _cs_verbatim(params.get("output_path", "")),
        "@@SEARCH_DIRS@@": search_dirs_cs,
    }

    code = _FLATTEN_JOURNAL_TEMPLATE
    for token, value in replacements.items():
        code = code.replace(token, value)

    if "@@" in code:
        raise ValueError("拍平 Journal 模板仍有未替换的占位符")
    return code

