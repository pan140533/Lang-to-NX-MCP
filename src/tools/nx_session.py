"""NX 会话管理

管理 NX 应用程序的连接、文档、Part 等对象引用。

NX 与 CATIA 的核心区别：
  - CATIA V5 只有 COM 自动化一种外部接口
  - NX 有原生 NXOpen Python API，可以：
    (a) 直接在 NX 内部运行（Journal 模式）
    (b) 外部 Python 配置后 import NXOpen 直连
    (c) 通过 COM 桥接访问（不推荐，但兼容老版本 NX）

本模块优先尝试直连模式（需要正确配置 NX 外部 Python 环境），
如果不可用则降级为 Journal 模式（生成 .py 文件由 NX 执行）。
"""
from __future__ import annotations

import os
import sys
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional, TYPE_CHECKING

# 尝试导入 NXOpen（外部 Python 直连模式需要正确配置环境变量）
NXOPEN_AVAILABLE = False
NXOPEN_VERSION = ""
try:
    import NXOpen as _nx
    NXOpen = _nx  # 让 IDE 能补全
    NXOPEN_AVAILABLE = True
    NXOPEN_VERSION = getattr(_nx, "__version__", "unknown")
except ImportError:
    NXOpen = None  # type: ignore

# NX 安装路径（从环境变量读取，或常用默认路径）
NX_INSTALL_DIR = os.environ.get(
    "UGII_BASE_DIR",
    r"C:\Program Files\Siemens\NX 1980"
)
NX_EXE = os.path.join(NX_INSTALL_DIR, "UGII", "nx.exe")


class NXSession:
    """NX 会话上下文

    自动选择可用模式：
      1. 直连模式 — 外部 Python 配置好 NXOpen 后 direct import
      2. Journal 模式 — 生成 journal 文件，启动 NX 进程执行

    用法：
        session = NXSession()
        session.new_document()          # 创建新 Part
        session.save("C:/model.prt")    # 保存
        session.update()                # 刷新视图
    """

    def __init__(self, mode: str = "auto", visible: bool = True):
        """初始化 NX 会话

        Args:
            mode: 连接模式
                - "auto": 自动选择（优先直连，失败则 Journal）
                - "direct": 强制直连（需要 NXOpen 环境）
                - "journal": 强制 Journal 模式
            visible: 是否显示 NX 窗口（Journal 模式）
        """
        self.mode = mode
        self.visible = visible
        self.nx_session: Optional["NXOpen.Session"] = None
        self.work_part: Optional["NXOpen.Part"] = None
        self.display_part: Optional["NXOpen.Part"] = None

        # Journal 模式状态
        self._journal_lines: list[str] = []
        self._journal_imports: set[str] = set()
        self._journal_vars: dict[str, str] = {}
        self._journal_path: Optional[Path] = None
        self._connected = False
        self._is_direct = False

        if mode == "auto":
            if NXOPEN_AVAILABLE:
                self._connect_direct()
            else:
                self._init_journal()
        elif mode == "direct":
            if not NXOPEN_AVAILABLE:
                raise ImportError(
                    "直连模式需要 NXOpen Python 环境。\n"
                    "请设置环境变量:\n"
                    "  UGII_BASE_DIR=C:\\Program Files\\Siemens\\NX 1980\n"
                    "  UGII_PYTHON_LIBRARY_DIR=%UGII_BASE_DIR%\\UGII\\python\n"
                    "并在 NX 安装时勾选 'Programming Tools'\n"
                    "或使用 Journal 模式 (mode='journal')"
                )
            self._connect_direct()
        else:  # journal
            self._init_journal()

    # ── 直连模式 ──

    def _connect_direct(self):
        """直连到正在运行的 NX 实例"""
        self.nx_session = NXOpen.Session.GetSession()
        if self.nx_session:
            self.work_part = self.nx_session.Parts.Work
            self.display_part = self.nx_session.Parts.Display
            self._connected = True
            self._is_direct = True
        else:
            raise RuntimeError("无法获取 NX Session（NX 未运行？）")

    # ── Journal 模式 ──

    def _init_journal(self):
        """初始化 Journal 模式：准备 Python 脚本"""
        self._journal_lines = []
        self._add_journal_import("NXOpen")
        self._journal_lines.append("")
        # 常用变量
        self._journal_lines.append("theSession = NXOpen.Session.GetSession()")
        self._journal_lines.append("workPart = theSession.Parts.Work")
        self._journal_lines.append("displayPart = theSession.Parts.Display")
        self._journal_lines.append("")
        self._connected = True
        self._is_direct = False

    def _add_journal_import(self, module: str):
        """添加 import 语句（自动去重）"""
        if module not in self._journal_imports:
            self._journal_imports.add(module)
            self._journal_lines.insert(0, f"import {module}")

    def _add_journal_line(self, line: str):
        """添加一行 Journal 代码"""
        self._journal_lines.append(line)

    def get_journal_script(self) -> str:
        """获取当前 Journal 脚本内容"""
        return "\n".join(self._journal_lines)

    def write_journal(self, output_dir: Optional[str] = None) -> Path:
        """将 Journal 脚本写入文件

        Args:
            output_dir: 输出目录，默认 output/scripts/

        Returns:
            脚本文件路径
        """
        if output_dir:
            path = Path(output_dir) / f"nx_journal_{uuid.uuid4().hex[:12]}.py"
        else:
            path = Path(tempfile.gettempdir()) / f"nx_journal_{uuid.uuid4().hex[:12]}.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.get_journal_script(), encoding="utf-8")
        self._journal_path = path
        return path

    def execute_journal(self, journal_path: Optional[Path] = None,
                        wait: bool = True, timeout: int = 300) -> subprocess.CompletedProcess:
        """执行 Journal 脚本（启动 NX 进程运行）

        Args:
            journal_path: 脚本路径，None 则使用当前缓存的脚本
            wait: 是否等待执行完成
            timeout: 超时秒数

        Returns:
            subprocess.CompletedProcess
        """
        path = journal_path or self._journal_path
        if path is None:
            path = self.write_journal()

        cmd = [NX_EXE, "-journal", str(path)]
        if not self.visible:
            cmd.insert(1, "-quiet")

        if wait:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        else:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return proc

    # ── 文档操作 ──

    def new_document(self, template: str = "") -> str:
        """创建新 Part 文档

        Args:
            template: 模板文件路径，空则用默认 mm 模板

        Returns:
            Part 文件全路径
        """
        if self._is_direct:
            if not template:
                template = os.path.join(
                    NX_INSTALL_DIR, "UGII", "templates",
                    "model-plain-1-mm-template.prt"
                )
            # NXOpen.Parts.New(template, parent, partName)
            self.work_part = self.nx_session.Parts.New(template, None, "")
            return self.work_part.FullPath
        else:
            if not template:
                template = (
                    'os.path.join(os.environ["UGII_BASE_DIR"], '
                    '"UGII", "templates", "model-plain-1-mm-template.prt")'
                )
            var = "_part"
            self._add_journal_line(
                f'{var} = workPart.Parts.New({template}, None, "")'
            )
            self._add_journal_line(f"workPart = {var}")
            self._add_journal_line("displayPart = theSession.Parts.Display")
            return f"[journal] new_part"

    def save(self, path: str) -> None:
        """保存文档

        Args:
            path: 保存路径，如 r"C:\\model.prt"
        """
        norm_path = os.path.normpath(path)
        if self._is_direct:
            self.work_part.SaveAs(norm_path)
        else:
            self._add_journal_line(f'workPart.SaveAs(r"{norm_path}")')

    def save_as_stp(self, path: str) -> None:
        """导出为 STEP 格式

        Args:
            path: 导出路径，如 r"C:\\model.stp"
        """
        norm_path = os.path.normpath(path)
        if self._is_direct:
            # NXOpen 导出 STEP
            export_options = NXOpen.ExportStepOptions()
            export_options.File = norm_path
            self.nx_session.ExportStep(export_options)
        else:
            self._add_journal_import("NXOpen.ExportStepOptions")
            self._add_journal_line(
                'expOpts = NXOpen.ExportStepOptions()'
            )
            self._add_journal_line(f'expOpts.File = r"{norm_path}"')
            self._add_journal_line("theSession.ExportStep(expOpts)")

    def update(self) -> None:
        """更新 Part 显示"""
        if self._is_direct:
            try:
                self.work_part.ModelingViews.WorkView.Regenerate()
            except Exception:
                pass
        else:
            self._add_journal_line(
                "workPart.ModelingViews.WorkView.Regenerate()"
            )

    def close(self):
        """释放资源"""
        if self._is_direct and self.work_part:
            try:
                self.work_part.Close(NXOpen.BasePart.CloseRejectSave)
            except Exception:
                pass
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def is_direct_mode(self) -> bool:
        return self._is_direct
