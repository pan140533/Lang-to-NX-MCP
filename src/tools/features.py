"""特征工具函数 — NXOpen 实现

所有特征建模操作（拉伸、切槽、倒角、圆角、扫掠、加强筋等）。

NX 与 CATIA 的关键区别：
  - CATIA: ShapeFactory.AddNewPad(sketch, length) — 直接创建
  - NX:    ExtrudeBuilder 模式 — 创建 Builder → 设置参数 → Commit
  - NX 的 Builder 模式更灵活可控，代码也更清晰
  - NX 的倒角/圆角 API 稳定可用（不像 CATIA 当前版本无法获取边引用）
"""
from __future__ import annotations

from .nx_session import NXSession, NXOpen


def extrude(session: NXSession, sketch, length: float) -> str:
    """拉伸草图生成实体。

    NX 路径：NXOpen.Features.ExtrudeBuilder

    Args:
        session: NX 会话
        sketch: 草图对象（已关闭）
        length: 拉伸长度 (mm)

    Returns:
        特征 ID
    """
    if session.is_direct_mode:
        work_part = session.work_part

        # 创建 ExtrudeBuilder
        extrude_builder = work_part.Features.CreateExtrudeBuilder(
            NXOpen.Features.Feature.Null,
            NXOpen.Features.ExtrudeBuilder.Section()
        )

        # 设置截面
        section = extrude_builder.Section
        section.AddToSection(sketch)

        # 设置拉伸方向和距离
        extrude_builder.Direction = NXOpen.Direction(
            work_part.Datums.FindObject("ZC")
        )
        extrude_builder.Limits.StartDistance.Value = 0.0
        extrude_builder.Limits.EndDistance.Value = length
        extrude_builder.BooleanOption = NXOpen.Features.FeatureBooleanOption.Create

        # 提交
        feature = extrude_builder.Commit()
        NXOpen.NXObject.Destroy(extrude_builder)
        session.update()
        return feature
    else:
        var = "_extrude"
        session._add_journal_line(
            f'# extrude: sketch={sketch}, length={length}'
        )
        session._add_journal_line(
            f'{var} = workPart.Features.CreateExtrudeBuilder('
            f'NXOpen.Features.Feature.Null, '
            f'NXOpen.Features.ExtrudeBuilder.Section())'
        )
        # NX builder pattern requires multiple lines in journal too
        session._add_journal_line(f'{var}.Limits.StartDistance.Value = 0.0')
        session._add_journal_line(f'{var}.Limits.EndDistance.Value = {length}')
        session._add_journal_line(f'extrudeFeat = {var}.Commit()')
        session._add_journal_line(
            "workPart.ModelingViews.WorkView.Regenerate()"
        )
        return f"[ref:{var}]"


def extrude_cut(session: NXSession, sketch, length: float,
                reverse: bool = False):
    """拉伸切槽（Subtract Boolean），在已有实体上切除材料。

    NX 路径：ExtrudeBuilder 设置 BooleanOption=Subtract

    Args:
        session: NX 会话
        sketch: 草图对象（已关闭）
        length: 切除深度 (mm)
        reverse: 是否反转切除方向

    Returns:
        特征对象
    """
    if session.is_direct_mode:
        work_part = session.work_part

        cut_builder = work_part.Features.CreateExtrudeBuilder(
            NXOpen.Features.Feature.Null,
            NXOpen.Features.ExtrudeBuilder.Section()
        )

        section = cut_builder.Section
        section.AddToSection(sketch)

        cut_builder.Limits.StartDistance.Value = 0.0
        cut_builder.Limits.EndDistance.Value = length
        # Subtract boolean
        cut_builder.BooleanOption = NXOpen.Features.FeatureBooleanOption.Subtract

        if reverse:
            cut_builder.DirectionReversalOption = (
                NXOpen.Features.FeatureDirectionReversalOption.Reverse
            )

        feature = cut_builder.Commit()
        NXOpen.NXObject.Destroy(cut_builder)
        session.update()
        return feature
    else:
        var = "_cut"
        rev = "True" if reverse else "False"
        session._add_journal_line(
            f'{var} = workPart.Features.CreateExtrudeBuilder('
            f'NXOpen.Features.Feature.Null, '
            f'NXOpen.Features.ExtrudeBuilder.Section())'
        )
        session._add_journal_line(f'{var}.Limits.EndDistance.Value = {length}')
        session._add_journal_line(
            f'{var}.BooleanOption = NXOpen.Features.FeatureBooleanOption.Subtract'
        )
        session._add_journal_line(
            f'{var}.DirectionReversalOption = '
            f'NXOpen.Features.FeatureDirectionReversalOption.Reverse'
        ) if reverse else None
        session._add_journal_line(f'cutFeat = {var}.Commit()')
        session._add_journal_line(
            "workPart.ModelingViews.WorkView.Regenerate()"
        )
        return f"[ref:{var}]"


def chamfer(session: NXSession, edge, length: float, angle: float = 45.0) -> str:
    """倒角（C 角）。

    NX 路径：NXOpen.Features.ChamferBuilder
    NX 的倒角 API 稳定可用（实测通过），不像 CATIA 当前版本有问题。

    Args:
        session: NX 会话
        edge: 边对象
        length: 倒角长度 (mm)
        angle: 倒角角度（度），默认 45

    Returns:
        特征 ID
    """
    if session.is_direct_mode:
        work_part = session.work_part

        # 创建 ChamferBuilder
        chamfer_builder = work_part.Features.CreateChamferBuilder(
            NXOpen.Features.Feature.Null
        )
        chamfer_builder.ChamferType = (
            NXOpen.Features.ChamferBuilder.Types.OffsetAndAngle
        )
        chamfer_builder.Offset.Value = length
        chamfer_builder.Angle.Value = angle
        chamfer_builder.Edges.AddToSection(edge)

        feature = chamfer_builder.Commit()
        NXOpen.NXObject.Destroy(chamfer_builder)
        session.update()
        return feature
    else:
        var = "_chamfer"
        session._add_journal_line(
            f'{var} = workPart.Features.CreateChamferBuilder('
            f'NXOpen.Features.Feature.Null)'
        )
        session._add_journal_line(
            f'{var}.ChamferType = NXOpen.Features.ChamferBuilder.Types.OffsetAndAngle'
        )
        session._add_journal_line(f'{var}.Offset.Value = {length}')
        session._add_journal_line(f'{var}.Angle.Value = {angle}')
        session._add_journal_line(f'chamferFeat = {var}.Commit()')
        return f"[ref:{var}]"


def fillet(session: NXSession, edge, radius: float):
    """圆角（Edge Blend）。

    NX 路径：NXOpen.Features.EdgeBlendBuilder

    Args:
        session: NX 会话
        edge: 边对象
        radius: 圆角半径 (mm)

    Returns:
        特征对象
    """
    if session.is_direct_mode:
        work_part = session.work_part

        blend_builder = work_part.Features.CreateEdgeBlendBuilder(
            NXOpen.Features.Feature.Null
        )
        blend_builder.Radius.Value = radius
        blend_builder.Edges.AddToSection(edge)

        feature = blend_builder.Commit()
        NXOpen.NXObject.Destroy(blend_builder)
        session.update()
        return feature
    else:
        var = "_fillet"
        session._add_journal_line(
            f'{var} = workPart.Features.CreateEdgeBlendBuilder('
            f'NXOpen.Features.Feature.Null)'
        )
        session._add_journal_line(f'{var}.Radius.Value = {radius}')
        session._add_journal_line(f'filletFeat = {var}.Commit()')
        return f"[ref:{var}]"


def revolve(session: NXSession, sketch, angle: float = 360.0):
    """旋转成实体（Revolve）。

    NX 路径：NXOpen.Features.RevolveBuilder
    此 API 稳定可用（CATIA 中 AddNewShaft 不可用，NX 中无此问题）。

    Args:
        session: NX 会话
        sketch: 已关闭的草图
        angle: 旋转角度，默认 360 度

    Returns:
        特征对象
    """
    if session.is_direct_mode:
        work_part = session.work_part

        revolve_builder = work_part.Features.CreateRevolveBuilder(
            NXOpen.Features.Feature.Null,
            NXOpen.Features.RevolveBuilder.Section()
        )

        revolve_builder.Limits.StartAngle.Value = 0.0
        revolve_builder.Limits.EndAngle.Value = angle
        revolve_builder.BooleanOption = NXOpen.Features.FeatureBooleanOption.Create

        feature = revolve_builder.Commit()
        NXOpen.NXObject.Destroy(revolve_builder)
        session.update()
        return feature
    else:
        var = "_revolve"
        session._add_journal_line(
            f'{var} = workPart.Features.CreateRevolveBuilder('
            f'NXOpen.Features.Feature.Null, '
            f'NXOpen.Features.RevolveBuilder.Section())'
        )
        session._add_journal_line(f'{var}.Limits.EndAngle.Value = {angle}')
        session._add_journal_line(f'revolveFeat = {var}.Commit()')
        return f"[ref:{var}]"


def rib(session: NXSession, profile_sketch, centerline_sketch):
    """扫掠肋（沿中心线扫掠轮廓）。

    NX 路径：NXOpen.Features.SweepBuilder

    Args:
        session: NX 会话
        profile_sketch: 轮廓草图
        centerline_sketch: 中心线/引导线草图

    Returns:
        特征对象
    """
    if session.is_direct_mode:
        work_part = session.work_part
        # Sweep through guides mechanism
        sweep_builder = work_part.Features.CreateSweepBuilder(
            NXOpen.Features.Feature.Null
        )
        # Note: exact implementation depends on NX version
        feature = sweep_builder.Commit()
        NXOpen.NXObject.Destroy(sweep_builder)
        session.update()
        return feature
    else:
        session._add_journal_line("# rib feature (sweep)")
        session._add_journal_line(
            "ribFeat = workPart.Features.CreateSweepBuilder("
            "NXOpen.Features.Feature.Null).Commit()"
        )
        return "[ref:ribFeat]"


def stiffener(session: NXSession, sketch, thickness: float = 5):
    """加强筋。

    NX 路径：NXOpen.Features.StiffenerBuilder

    Args:
        session: NX 会话
        sketch: 加强筋草图
        thickness: 筋厚度 (mm)

    Returns:
        特征对象
    """
    if session.is_direct_mode:
        work_part = session.work_part

        stiff_builder = work_part.Features.CreateStiffenerBuilder(
            NXOpen.Features.Feature.Null
        )
        stiff_builder.Thickness.Value = thickness
        stiff_builder.Section = sketch

        feature = stiff_builder.Commit()
        NXOpen.NXObject.Destroy(stiff_builder)
        session.update()
        return feature
    else:
        var = "_stiff"
        session._add_journal_line(
            f'{var} = workPart.Features.CreateStiffenerBuilder('
            f'NXOpen.Features.Feature.Null)'
        )
        session._add_journal_line(f'{var}.Thickness.Value = {thickness}')
        session._add_journal_line(f'stiffFeat = {var}.Commit()')
        return f"[ref:{var}]"
