"""选择工具函数 — NXOpen 实现

用于在模型中选面、选边、选特征，是二次操作的基础。

NX 与 CATIA 的区别：
  - CATIA: 需要用 CreateReferenceFromObject 获取 Reference
  - NX:    NXOpen 对象直接支持 FindObject, 边/面通过拓扑查询
  - NX 的边/面选择 API 更稳定，不像 CATIA 当前版本无法获取边引用
"""
from __future__ import annotations

from .nx_session import NXSession, NXOpen


def select_by_name(session: NXSession, name: str):
    """按名称查找对象。

    Args:
        session: NX 会话
        name: 对象名称，如 "Extrude(1)", "Sketch(1)"

    Returns:
        对象引用，未找到返回 None
    """
    if session.is_direct_mode:
        try:
            return session.work_part.FindObject(name)
        except Exception:
            return None
    else:
        session._add_journal_line(
            f'obj = workPart.FindObject("{name}")'
        )
        return f"[ref:obj]"


def get_all_faces(session: NXSession, feature) -> list:
    """获取特征的所有面。

    Args:
        session: NX 会话
        feature: 特征对象

    Returns:
        面列表
    """
    if session.is_direct_mode:
        try:
            bodies = feature.GetEntities()
            faces = []
            for body in bodies:
                for face in body.Faces:
                    faces.append(face)
            return faces
        except Exception:
            return []
    else:
        session._add_journal_line(f"# get_all_faces for {feature}")
        return []


def get_all_edges(session: NXSession, feature) -> list:
    """获取特征的所有边。

    Args:
        session: NX 会话
        feature: 特征对象

    Returns:
        边列表
    """
    if session.is_direct_mode:
        try:
            bodies = feature.GetEntities()
            edges = []
            for body in bodies:
                for edge in body.Edges:
                    edges.append(edge)
            return edges
        except Exception:
            return []
    else:
        session._add_journal_line(f"# get_all_edges for {feature}")
        return []


def get_face_by_index(session: NXSession, feature, index: int):
    """按索引获取面（从 1 开始）。

    Args:
        session: NX 会话
        feature: 特征对象
        index: 面索引（1-based）

    Returns:
        面对象
    """
    faces = get_all_faces(session, feature)
    if 0 < index <= len(faces):
        return faces[index - 1]
    return None


def get_edge_by_index(session: NXSession, feature, index: int):
    """按索引获取边（从 1 开始）。

    Args:
        session: NX 会话
        feature: 特征对象
        index: 边索引（1-based）

    Returns:
        边对象，未找到返回 None
    """
    edges = get_all_edges(session, feature)
    if 0 < index <= len(edges):
        return edges[index - 1]
    return None
