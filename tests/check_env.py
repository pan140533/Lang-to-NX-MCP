"""NX 环境检测脚本

检查当前系统能否运行 C# Journal + NX 建模流程。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

print("=" * 55)
print("  Lang-to-NX-MCP 环境检测")
print("=" * 55)

# 1. 检查 Python 版本
print(f"\n[1/5] Python 版本: {sys.version}")

# 2. 检查依赖
print(f"\n[2/5] 检查依赖...")
for mod_name in ["flask", "httpx", "dotenv"]:
    try:
        __import__(mod_name)
        print(f"      ✅ {mod_name}")
    except ImportError:
        print(f"      ❌ {mod_name}")

# 3. 检查 NXOpen
print(f"\n[3/5] 检查 NXOpen...")
try:
    import NXOpen
    print(f"      ✅ NXOpen 可用 (版本: {getattr(NXOpen, '__version__', 'unknown')})")
    print(f"      📍 路径: {NXOpen.__file__}")
except ImportError:
    print(f"      ⚠️  NXOpen 未安装（Journal 模式仍可工作）")
    print(f"      如需直连模式，请配置环境变量：")
    print(f"        UGII_BASE_DIR")
    print(f"        UGII_PYTHON_LIBRARY_DIR")
    print(f"        UGII_PYTHONPATH")

# 4. 检查 NX 安装路径
print(f"\n[4/5] 检查 NX 安装路径...")
import os
nx_dir = os.environ.get("UGII_BASE_DIR", r"C:\Program Files\Siemens\NX 1980")
nx_exe = os.path.join(nx_dir, "UGII", "nx.exe")
if os.path.exists(nx_exe):
    print(f"      ✅ NX 可执行文件: {nx_exe}")
else:
    print(f"      ⚠️  未找到 NX（默认路径: {nx_exe}）")
    print(f"      可以在 .env 文件中设置 UGII_BASE_DIR")

# 5. 检查工具库结构
print(f"\n[5/5] 检查项目结构...")
backend_dir = Path(__file__).parent.parent / "backend"
journal_dir = backend_dir / "journal"
files = [
    backend_dir / "api.py",
    backend_dir / "log_system.py",
    backend_dir / "llm_parser.py",
    journal_dir / "generator.py",
    journal_dir / "nx_modeler.cs",
    journal_dir / "tools.json",
]
all_ok = True
for f in files:
    if f.exists():
        print(f"      ✅ {f.name}")
    else:
        print(f"      ❌ {f.name} (缺失)")
        all_ok = False

print(f"\n{'='*55}")
if all_ok:
    print("  ✅ 项目结构完整，已准备就绪！")
    print(f"\n  启动方式:")
    print(f"    python run.py")
    print(f"\n  打开浏览器:")
    print(f"    http://127.0.0.1:8000")
else:
    print("  ❌ 项目结构不完整，请检查缺失文件")
print(f"{'='*55}")
