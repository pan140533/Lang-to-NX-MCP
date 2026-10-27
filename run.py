"""Lang-to-NX-MCP — 一键启动"""
import subprocess, os, sys, time, signal

ROOT = os.path.dirname(os.path.abspath(__file__))
procs = []

def cleanup(signum=None, frame=None):
    print("\n⏹️  停止服务...")
    for p in procs:
        try: p.terminate()
        except: pass
    print("✅ 已停止")
    sys.exit(0)

def main():
    print("╔══════════════════════════════════════╗")
    print("║   Lang-to-NX-MCP — 自然语言CAD建模   ║")
    print("╚══════════════════════════════════════╝\n")

    # 检查 .env（必须由用户手动创建并填写 NX 安装路径）
    if not os.path.exists(os.path.join(ROOT, ".env")):
        print("⚠️  没有找到 .env —— 必须先手动配置，程序不会自动去找 NX。")
        print("   1) 复制 .env.example 为 .env")
        print("   2) 打开 .env，把 NX_ROOT 改成你自己的 NX 安装目录")
        print("      （该目录下应有 NXBIN\\run_journal.exe，填写时不要带 \\NXBIN）\n")

    # 检查前端依赖
    if not os.path.exists(os.path.join(ROOT, "frontend", "node_modules")):
        print("📦 安装前端依赖...")
        subprocess.run("npm install", shell=True, cwd=os.path.join(ROOT, "frontend"))

    # 启动后端（设置 PYTHONPATH 让 backend/ 可导入）
    print("🚀 后端 → http://localhost:8000")
    env = os.environ.copy()
    backend_dir = os.path.join(ROOT, "backend")
    env["PYTHONPATH"] = ROOT + os.pathsep + backend_dir + os.pathsep + env.get("PYTHONPATH", "")
    p = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api:app", "--port", "8000"],
        cwd=ROOT, env=env
    )
    procs.append(p)
    time.sleep(1.5)

    # 启动前端
    print("🚀 前端 → http://localhost:3000")
    p = subprocess.Popen(
        "npx next dev", shell=True,
        cwd=os.path.join(ROOT, "frontend")
    )
    procs.append(p)

    signal.signal(signal.SIGINT, cleanup)
    print("\n按 Ctrl+C 停止所有服务\n")

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
