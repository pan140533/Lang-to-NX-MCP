"""草图工具函数 — NXOpen 实现

NX 与 CATIA 的核心区别：
  - CATIA: sketch.OpenEdition() / CloseEdition() 管理草图编辑状态
  - NX:    草图通过 Builder 模式创建，无需手动开关编辑
  - CATIA: Factory2D 负责画图
  - NX:    workPart.Curves / Sketch.SketchCurves 负责画图

注意：NXOpen 的 API 使用 Builder 模式，必须先创建 Builder，
      设置参数后调用 Commit() 完成操作。
"""
from __future__ import annotations

from typing import Optional
from .nx_session import NXSession, NXOpen


def create_sketch_on_plane(session: NXSession,
                           plane_id: str = "XY",
                           sketch_name: str = "",
                           plane=None):
    """在指定平面上创建草图。

    NX 路径：workPart.Sketches.CreateSketch(plane, ...)

    Args:
        session: NX 会话
        plane_id: 平面标识 "XY"/"YZ"/"ZX"
        sketch_name: 草图名称（可选）
        plane: 平面 COM/对象（替代 plane_id）

    Returns:
        草图对象
    """
    if session.is_direct_mode:
        work_part = session.work_part

        if plane is not None:
            plane_ref = plane
        else:
            plane_map = {
                "XY": work_part.Datums.FindObject("XY"),
                "YZ": work_part.Datums.FindObject("YZ"),
                "ZX": work_part.Datums.FindObject("ZX"),
            }
            plane_ref = plane_map.get(plane_id)
            if plane_ref is None:
                raise ValueError(f"不支持的平面: {plane_id}，可选: XY, YZ, ZX")

        # NX 草图通过 SketchInPlaceBuilder 创建
        sketch_builder = work_part.Sketches.CreateSketch(plane_ref)
        sketch = sketch_builder.Commit()
        NXOpen.NXObject.Destroy(sketch_builder)

        if sketch_name:
            sketch.Name = sketch_name
        return sketch
    else:
        # Journal 模式
        var = f"_sketch_{len(session._journal_vars)}"
        session._journal_vars["sketch"] = var
        plane_ref_str = plane_id if plane is None else "[plane_object]"

        session._add_journal_line(
            f'{var} = workPart.Sketches.CreateSketch('
            f'workPart.Datums.FindObject("{plane_ref_str}"))'
        )
        if sketch_name:
            session._add_journal_line(f'{var}.Name = "{sketch_name}"')
        return f"[ref:{var}]"


def open_sketch(session: NXSession, sketch) -> None:
    """打开草图编辑模式（CATIA 兼容方法，NX 中草图创建后即可编辑）

    NX 的 Builder 模式在 CreateSketch 时已进入编辑状态，
    此函数保留仅为保持接口一致。

    Args:
        session: NX 会话
        sketch: 草图对象
    """
    # NX 中草图创建后自动进入编辑态，无需手动 OpenEdition
    pass


def close_sketch(session: NXSession, sketch) -> None:
    """关闭草图编辑模式并更新。

    NX 路径：激活草图后通过 Deactivate 或 Update 完成。

    Args:
        session: NX 会话
        sketch: 草图对象
    """
    if session.is_direct_mode:
        try:
            # 退出草图编辑
            session.work_part.Sketches.Deactivate()
        except Exception:
            pass
        session.update()
    else:
        session._add_journal_line(
            "workPart.Sketches.Deactivate()"
        )
        session._add_journal_line(
            "workPart.ModelingViews.WorkView.Regenerate()"
        )


def draw_closed_circle(session: NXSession, sketch,
                       x: float, y: float, radius: float) -> str:
    """在草图中画封闭圆。

    NX 路径：CreateCircle(center, normal, radius) 在激活的草图内

    Args:
        session: NX 会话
        sketch: 草图对象
        x: 圆心 X 坐标 (mm)
        y: 圆心 Y 坐标 (mm)
        radius: 半径 (mm)

    Returns:
        几何元素 ID/引用
    """
    if session.is_direct_mode:
        center = NXOpen.Point3D(x, y, 0.0)
        normal = NXOpen.Vector3d(0.0, 0.0, 1.0)
        circle = session.work_part.Curves.CreateCircle(center, normal, radius)
        return str(circle.Tag)
    else:
        var = "_circle"
        session._add_journal_line(
            f'{var} = workPart.Curves.CreateCircle('
            f'NXOpen.Point3D({x}, {y}, 0.0), '
            f'NXOpen.Vector3d(0.0, 0.0, 1.0), {radius})'
        )
        return f"[ref:{var}]"


def draw_rectangle(session: NXSession, sketch,
                   x: float, y: float, width: float, height: float) -> list[str]:
    """在草图中画矩形（用 4 条线闭合）。

    NX 路径：CreateLine 连接 4 个角点

    Args:
        session: NX 会话
        sketch: 草图对象
        x: 左下角 X 坐标 (mm)
        y: 左下角 Y 坐标 (mm)
        width: 宽度 (mm)
        height: 高度 (mm)

    Returns:
        4 条线的 ID 列表
    """
    ids = []
    pts = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]

    if session.is_direct_mode:
        for i in range(4):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % 4]
            start = NXOpen.Point3D(x1, y1, 0.0)
            end = NXOpen.Point3D(x2, y2, 0.0)
            line = session.work_part.Curves.CreateLine(start, end)
            ids.append(str(line.Tag))
    else:
        for i in range(4):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % 4]
            var = f"_line_{i}"
            session._add_journal_line(
                f'{var} = workPart.Curves.CreateLine('
                f'NXOpen.Point3D({x1}, {y1}, 0.0), '
                f'NXOpen.Point3D({x2}, {y2}, 0.0))'
            )
            ids.append(f"[ref:{var}]")

    return ids


def draw_line(session: NXSession, sketch,
              x1: float, y1: float, x2: float, y2: float) -> str:
    """在草图中画直线。

    Args:
        session: NX 会话
        sketch: 草图对象
        x1, y1: 起点坐标 (mm)
        x2, y2: 终点坐标 (mm)

    Returns:
        直线元素 ID
    """
    if session.is_direct_mode:
        start = NXOpen.Point3D(x1, y1, 0.0)
        end = NXOpen.Point3D(x2, y2, 0.0)
        line = session.work_part.Curves.CreateLine(start, end)
        return str(line.Tag)
    else:
        var = "_line"
        session._add_journal_line(
            f'{var} = workPart.Curves.CreateLine('
            f'NXOpen.Point3D({x1}, {y1}, 0.0), '
            f'NXOpen.Point3D({x2}, {y2}, 0.0))'
        )
        return f"[ref:{var}]"
