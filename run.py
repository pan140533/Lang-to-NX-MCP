"""Lang-to-NX — 一键启动"""
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
    print("║     Lang-to-NX — 自然语言CAD建模     ║")
    print("╚══════════════════════════════════════╝\n")

    # 检查 .env
    if not os.path.exists(os.path.join(ROOT, ".env")):
        print("⚠️  未配置 .env，复制 .env.example 并填入 API Key\n")

    # 检查前端依赖
    if not os.path.exists(os.path.join(ROOT, "frontend", "node_modules")):
        print("📦 安装前端依赖...")
        subprocess.run("npm install", shell=True, cwd=os.path.join(ROOT, "frontend"))

    # 启动后端（设置 PYTHONPATH 让 src/ 可导入）
    print("🚀 后端 → http://localhost:8000")
    env = os.environ.copy()
    src_dir = os.path.join(ROOT, "src")
    env["PYTHONPATH"] = ROOT + os.pathsep + src_dir + os.pathsep + env.get("PYTHONPATH", "")
    p = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.fastapi_app:app", "--port", "8000"],
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
