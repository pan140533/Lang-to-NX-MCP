"""文件操作工具函数 — NXOpen 实现"""
from __future__ import annotations

from .nx_session import NXSession, NXOpen


def save_model(session: NXSession, path: str) -> None:
    """保存模型到指定路径。

    NX 路径：workPart.SaveAs(path)

    Args:
        session: NX 会话
        path: 保存路径，如 r"C:\model.prt"
    """
    session.save(path)


def save_as_step(session: NXSession, path: str) -> None:
    """导出 STEP 格式。

    NX 路径：session.ExportStep

    Args:
        session: NX 会话
        path: 导出路径，如 r"C:\model.stp"
    """
    session.save_as_stp(path)


def new_document(session: NXSession) -> None:
    """创建新 Part 文档"""
    session.new_document()
