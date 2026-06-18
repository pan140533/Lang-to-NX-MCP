"""参考平面工具函数 — NXOpen 实现

NX 路径：workPart.Datums.CreateDatumPlaneBuilder
NX 的 DatumPlane 通过 Builder 模式创建，支持偏移、角度等多种类型。
"""
from __future__ import annotations

from .nx_session import NXSession, NXOpen


def _get_datum_plane(session: NXSession, plane_id: str):
    """获取基准平面对象"""
    if session.is_direct_mode:
        work_part = session.work_part
        plane_map = {
            "XY": work_part.Datums.FindObject("XY"),
            "YZ": work_part.Datums.FindObject("YZ"),
            "ZX": work_part.Datums.FindObject("ZX"),
            "XC": work_part.Datums.FindObject("XC"),
            "YC": work_part.Datums.FindObject("YC"),
            "ZC": work_part.Datums.FindObject("ZC"),
        }
        plane = plane_map.get(plane_id)
        if plane is None:
            raise ValueError(f"不支持的平面: {plane_id}，可选: XY, YZ, ZX")
        return plane
    return plane_id


def offset_plane(session: NXSession,
                 plane_id: str = "XY",
                 distance: float = 10.0,
                 reverse: bool = False):
    """偏移参考平面。

    NX 路径：DatumPlaneBuilder 设置 Offset 类型和距离

    Args:
        session: NX 会话
        plane_id: 参考平面标识 "XY"/"YZ"/"ZX"
        distance: 偏移距离 (mm)
        reverse: 是否反向偏移

    Returns:
        新平面对象
    """
    if session.is_direct_mode:
        work_part = session.work_part
        ref_plane = _get_datum_plane(session, plane_id)

        # 创建 DatumPlaneBuilder
        plane_builder = work_part.Datums.CreateDatumPlaneBuilder(
            NXOpen.Datums.DatumPlane.Null
        )
        plane_builder.PlaneType = (
            NXOpen.Datums.DatumPlaneBuilder.PlaneTypes.Offset
        )
        plane_builder.PlaneOffset.Plane = ref_plane
        plane_builder.PlaneOffset.Distance.Value = distance

        if reverse:
            plane_builder.PlaneOffset.ReverseSide = True

        plane = plane_builder.Commit()
        NXOpen.NXObject.Destroy(plane_builder)
        session.update()
        return plane
    else:
        var = "_offset_plane"
        rev_str = "True" if reverse else "False"
        session._add_journal_line(
            f'{var} = workPart.Datums.CreateDatumPlaneBuilder('
            f'NXOpen.Datums.DatumPlane.Null)'
        )
        session._add_journal_line(
            f'{var}.PlaneType = NXOpen.Datums.DatumPlaneBuilder.PlaneTypes.Offset'
        )
        session._add_journal_line(
            f'{var}.PlaneOffset.Plane = workPart.Datums.FindObject("{plane_id}")'
        )
        session._add_journal_line(f'{var}.PlaneOffset.Distance.Value = {distance}')
        if reverse:
            session._add_journal_line(f'{var}.PlaneOffset.ReverseSide = True')
        session._add_journal_line(f'offsetPlane = {var}.Commit()')
        return f"[ref:{var}]"
