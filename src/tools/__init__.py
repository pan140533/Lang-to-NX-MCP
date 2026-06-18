"""NX 建模工具库 — 所有工具函数通过 NXSession 操作 NX。

与 CATIA 版本的核心区别：
  - NX 有原生 NXOpen Python API，无需 COM（可选的 Journal 模式也不需 COM）
  - NXOpen API 类型明确、文档完善，不会像 CATIA COM 那样乱码报错
  - 支持两种模式：
      1. 直连模式：外部 Python 配置好 NXOpen 库，直接 import NXOpen 调用
      2. Journal 模式：生成 .py 脚本供 NX 内部执行（零配置，推荐起步）
  - 因为 NXOpen 是原生 Python API，AI 可以直接生成 NXOpen 代码，
    不需要 JSON 序列化层作为"安全垫"

用法：
    session = NXSession()           # 自动选择可用模式
    session.new_document()
    sketch = create_sketch_on_plane(session, "XY")
    open_sketch(session, sketch)
    draw_closed_circle(session, sketch, 0, 0, 15)
    close_sketch(session, sketch)
    extrude(session, sketch, 30)
    save_model(session, "C:/model.prt")
"""
from .nx_session import NXSession, NXOpen

from . import sketch
from . import features
from . import io
from . import planes
from . import selection
