# -*- coding: utf-8 -*-
"""MathModelAgent 一键安装脚本（由 install.bat 调用）。

为什么安装逻辑放在本文件而不是 install.bat：
cmd.exe 逐字节读批处理，多字节中文可能被它的读缓冲区从中间劈开，
被劈开的碎片会被当成命令执行（曾随机报
"'xxx' is not recognized as an internal or external command"）。
所以 install.bat 保持纯 ASCII 只做入口，全部业务与中文输出放在这里，
编码完全由 Python 掌控，不受 cmd 解析影响。
"""
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

# 控制台已由 install.bat chcp 65001；输出重定向到文件时同样写 UTF-8，
# 保证两种情况下日志都可读、不因系统默认编码缺字而崩掉
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"
USE_DOCKER = "--docker" in sys.argv[1:]


def log(msg: str) -> None:
    print(msg, flush=True)


def run(args, error_msg, cwd=None):
    """运行外部命令，失败时打印 error_msg 并退出 1。"""
    log("  > " + " ".join(str(a) for a in args))
    try:
        result = subprocess.run(args, cwd=str(cwd) if cwd else str(ROOT))
    except OSError as exc:
        log("[错误] %s：%s" % (error_msg, exc))
        sys.exit(1)
    if result.returncode != 0:
        log("[错误] %s（退出码 %d）" % (error_msg, result.returncode))
        sys.exit(1)


def main() -> None:
    log("=" * 46)
    log("  Math Model Agent — 一键安装")
    log("=" * 46)

    # ── 1. 环境检查 ──
    if sys.version_info < (3, 11):
        log("[错误] Python 版本过低,需要 3.11+,当前为 %s" % sys.version.split()[0])
        log("        https://www.python.org/downloads/")
        sys.exit(1)
    log("[1/5] Python 版本: %s" % sys.version.split()[0])

    pnpm = shutil.which("pnpm")
    if pnpm is None:
        log("[错误] 未找到 pnpm。请先安装:")
        log("        npm i -g pnpm")
        log("     或: corepack enable")
        sys.exit(1)
    log("[1/5] pnpm 已就绪")

    # ── 2. 后端: 虚拟环境 ──
    if VENV_PY.exists():
        log("[2/5] 虚拟环境 .venv 已存在, 跳过")
    else:
        log("[2/5] 创建后端虚拟环境 .venv ...")
        run([sys.executable, "-m", "venv", str(ROOT / ".venv")], "创建虚拟环境失败")

    # ── 3. 后端依赖 ──
    log("[3/5] 安装后端依赖(首次约 3-8 分钟,取决于网络)...")
    # 升级 pip 失败不致命,静默忽略(与旧版 install.bat 行为一致)
    subprocess.run(
        [str(VENV_PY), "-m", "pip", "install", "--upgrade", "pip"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    run([str(VENV_PY), "-m", "pip", "install", "-e", "backend"],
        "后端依赖安装失败,请检查网络后重试")

    # ── 4. 生成 .env ──
    env_file = ROOT / "backend" / ".env"
    if env_file.exists():
        log("[4/5] backend.env 已存在, 跳过")
    else:
        log("[4/5] 生成 backend.env 并注入随机 JWT_SECRET")
        example = ROOT / "backend" / ".env.example"
        if not example.exists():
            log("[错误] 未找到 backend/.env.example,仓库文件不完整,请重新下载解压")
            sys.exit(1)
        text = example.read_text(encoding="utf-8")
        text = text.replace(
            "JWT_SECRET=change-me-to-a-random-string",
            "JWT_SECRET=" + secrets.token_hex(32),
        )
        env_file.write_text(text, encoding="utf-8")

    # ── 5. 前端依赖 ──
    frontend = ROOT / "frontend"
    log("[5/5] 安装前端依赖 pnpm install(首次约 2-5 分钟)...")
    if not (frontend / "package.json").exists():
        log("[错误] 未找到 frontend/package.json,仓库文件不完整,请重新下载解压")
        sys.exit(1)
    # 用 cwd 而不是 --dir:进程级锁定工作目录,与调用方当前目录完全无关
    run([pnpm, "install"], "前端依赖安装失败", cwd=frontend)

    # ── 可选: Docker 沙箱镜像 ──
    if USE_DOCKER:
        docker = shutil.which("docker")
        if docker is None:
            log("[警告] 未检测到 docker,继续使用 subprocess 模式(功能不受影响)")
        else:
            log("[可选] 构建沙箱镜像 mathmodel-sandbox ...")
            try:
                result = subprocess.run(
                    [docker, "build", "-t", "mathmodel-sandbox",
                     "-f", "backend/Dockerfile.sandbox", "backend"],
                    cwd=str(ROOT),
                )
            except OSError:
                result = None
            if result is None or result.returncode != 0:
                log("[警告] 沙箱镜像构建失败,继续使用 subprocess 模式(功能不受影响)")
            else:
                if env_file.exists():
                    text = env_file.read_text(encoding="utf-8")
                    text = text.replace(
                        "SANDBOX_BACKEND=subprocess", "SANDBOX_BACKEND=docker"
                    )
                    env_file.write_text(text, encoding="utf-8")
                log("[可选] 已启用 docker 硬隔离沙箱")

    log("")
    log("=" * 46)
    log("  安装完成!")
    log("")
    log("  启动:  start.bat   (Windows 一键启动前后端)")
    log("  前端:  http://localhost:5174")
    log("  后端:  http://127.0.0.1:8002/docs")
    log("")
    log("  配置 API Key: 打开首页,在「API Key」输入框粘贴你的")
    log("  DeepSeek/OpenAI 兼容 Key 即可(仅保存在本机 backend\\data)。")
    log("  也可以编辑 backend\\.env 填 OPENAI_API_KEY。")
    log("=" * 46)

    try:
        import msvcrt
        log("")
        log("按任意键退出...")
        msvcrt.getch()
    except (ImportError, OSError, EOFError):
        pass


if __name__ == "__main__":
    main()
