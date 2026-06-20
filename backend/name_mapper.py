"""
名称映射数据库 — 解决 run_journal.exe 中文路径编码问题

ASCII 文件名 ↔ 中文项目名 的双向映射
数据存储在 output/name_mapping.db (SQLite)
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "output" / "name_mapping.db"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS name_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            output_name TEXT NOT NULL UNIQUE,
            project_name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_output_name ON name_map(output_name)
    """)
    conn.commit()
    return conn


def save_mapping(output_name: str, project_name: str, description: str = ""):
    """保存文件名映射"""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO name_map (output_name, project_name, description, created_at) VALUES (?, ?, ?, ?)",
            (output_name, project_name, description, datetime.now().isoformat())
        )
        conn.commit()
    finally:
        conn.close()


def get_project_name(output_name: str) -> Optional[str]:
    """通过 ASCII 文件名查中文项目名"""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT project_name FROM name_map WHERE output_name = ?", (output_name,)
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def get_mapping(output_name: str) -> Optional[dict]:
    """获取完整映射记录"""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT output_name, project_name, description, created_at FROM name_map WHERE output_name = ?",
            (output_name,)
        ).fetchone()
        if row:
            return {
                "output_name": row[0],
                "project_name": row[1],
                "description": row[2],
                "created_at": row[3],
            }
        return None
    finally:
        conn.close()


def list_mappings(limit: int = 50) -> list[dict]:
    """列出最近的历史映射"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT output_name, project_name, description, created_at FROM name_map ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [
            {"output_name": r[0], "project_name": r[1], "description": r[2], "created_at": r[3]}
            for r in rows
        ]
    finally:
        conn.close()


def search_by_project(keyword: str) -> list[dict]:
    """按项目名关键词搜索"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT output_name, project_name, description, created_at FROM name_map WHERE project_name LIKE ? ORDER BY id DESC",
            (f"%{keyword}%",)
        ).fetchall()
        return [
            {"output_name": r[0], "project_name": r[1], "description": r[2], "created_at": r[3]}
            for r in rows
        ]
    finally:
        conn.close()
