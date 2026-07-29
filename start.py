"""MathModelAgent 一键启动脚本 (Python)
用法: python start.py
"""

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
BACKEND_PORT = "8002"


def check_env() -> bool:
    """检查 .env 是否已配置"""
    env_file = BACKEND_DIR / ".env"
    if not env_file.exists():
        print("[ERROR] backend/.env 不存在!")
        print("  请: cp backend/.env.example backend/.env")
        print("  然后编辑 backend/.env 填入 API Key")
        return False
    content = env_file.read_text(encoding="utf-8")
    if "OPENAI_API_KEY=sk-xxx" in content or "OPENAI_API_KEY=" in content and "sk-3" not in content:
        print("[WARN] backend/.env 可能未配置 API Key，请检查")
    return True


def check_port(port: str) -> bool:
    """检查端口是否已被占用"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", int(port)))
        s.close()
        return True
    except Exception:
        return False


def start_process(name: str, cwd: Path, cmd: str) -> subprocess.Popen | None:
    """在新终端窗口中启动进程"""
    try:
        if sys.platform == "win32":
            return subprocess.Popen(
                f'start "{name}" cmd /k "cd /d {cwd} && {cmd}"',
                shell=True,
                cwd=str(cwd),
            )
        else:
            # Linux/Mac: use xterm or gnome-terminal
            return subprocess.Popen(
                f'xterm -T "{name}" -e "cd {cwd} && {cmd}; read"',
                shell=True,
            )
    except Exception as e:
        print(f"[ERROR] {name} 启动失败: {e}")
        return None


def main():
    print("=" * 50)
    print("  MathModelAgent - One-Click Start")
    print("=" * 50)
    print()

    # 1. Check .env
    if not check_env():
        input("\n按任意键退出...")
        return

    # 2. Check backend port
    if check_port(BACKEND_PORT):
        print(f"[skip] backend already running on port {BACKEND_PORT}")
    else:
        print(f"[start] backend on http://127.0.0.1:{BACKEND_PORT}")
        start_process(
            "backend",
            BACKEND_DIR,
            f"uvicorn app.main:app --host 127.0.0.1 --port {BACKEND_PORT} --workers 1 --limit-concurrency 4 --timeout-keep-alive 30",
        )
        print("  等待后端就绪...")
        for _ in range(10):
            time.sleep(2)
            if check_port(BACKEND_PORT):
                print("  [ ok ] backend ready")
                break
        else:
            print("  [warn] 后端可能还在启动中（首次需重建向量索引）")

    # 3. Check frontend port
    if check_port("5174"):
        print("[skip] frontend already running on port 5174")
    else:
        print("[start] frontend on http://localhost:5174")
        start_process("frontend", FRONTEND_DIR, "pnpm dev")

    print()
    print("=" * 50)
    print("  Frontend : http://localhost:5174")
    print(f"  API docs : http://127.0.0.1:{BACKEND_PORT}/docs")
    print("=" * 50)
    print()
    print("[tip] Docker 服务: docker compose up -d chromadb redis")
    input("按任意键关闭此窗口...")


if __name__ == "__main__":
    main()
