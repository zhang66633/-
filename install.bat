@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==============================================
echo  Math Model Agent — 一键安装
echo ==============================================

REM ── 1. 环境检查 ────────────────────────────────
where python >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 Python。请安装 Python 3.11+ 并勾选 "Add to PATH":
  echo        https://www.python.org/downloads/
  pause & exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [1/5] Python 版本: !PYVER!

where pnpm >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 pnpm。请先安装:
  echo        npm i -g pnpm
  echo     或: corepack enable
  pause & exit /b 1
)
echo [1/5] pnpm 已就绪

REM ── 2. 后端: 虚拟环境 + 依赖 ────────────────────
echo [2/5] 创建后端虚拟环境 .venv ...
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 ( echo [错误] 创建虚拟环境失败 & pause & exit /b 1 )
)
echo [3/5] 安装后端依赖(首次约 3-8 分钟,取决于网络)...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>nul
".venv\Scripts\python.exe" -m pip install -e backend
if errorlevel 1 ( echo [错误] 后端依赖安装失败,请检查网络后重试 & pause & exit /b 1 )

REM ── 3. 生成 .env ────────────────────────────────
REM 坑实录：括号块内 echo 文案带中文括号会让整块解析崩溃；for /f 捕获带引号
REM 命令输出会被拆坏引号——两者叠加导致新用户安装必卡死在本步。故改为：
REM 单条 python 内联完成 复制模板+注入随机 JWT_SECRET，batch 不捕获任何变量，
REM 且块内 echo 文案绝不带括号。
if exist "backend\.env" (
  echo [4/5] backend.env 已存在, 跳过
) else (
  echo [4/5] 生成 backend.env 并注入随机 JWT_SECRET
  ".venv\Scripts\python.exe" -c "import io,pathlib,secrets;s=io.open('backend/.env.example',encoding='utf-8').read();io.open(pathlib.Path('backend/.env'),'w',encoding='utf-8').write(s.replace('JWT_SECRET=change-me-to-a-random-string','JWT_SECRET='+secrets.token_hex(32)))"
)

REM ── 4. 前端依赖 ─────────────────────────────────
echo [5/5] 安装前端依赖 pnpm install(首次约 2-5 分钟)...
REM call 必须写：pnpm 本体是 pnpm.cmd 批处理，批处理调批处理不写 call 会直接
REM 终止本脚本（横幅与错误处理都不执行，exit code 还是 0，最难排查的一种死法）。
REM --dir 显式指定目录，本步与「当前目录」完全无关（pushd 失败时 cmd 不会中止）。
if not exist "frontend\package.json" ( echo [错误] 未找到 frontend\package.json,仓库文件不完整,请重新下载解压 & pause & exit /b 1 )
call pnpm install --dir "%~dp0frontend"
if errorlevel 1 ( echo [错误] 前端依赖安装失败 & pause & exit /b 1 )

REM ── 5. 可选: Docker 沙箱镜像 ─────────────────────
REM 坑实录：多行括号块被跳过时，cmd 按括号扫描找块尾，echo 文案里的括号会
REM 让它提前"找到"块尾，把块内命令当普通行执行（幽灵分支）。本段一律用
REM goto 线性流程，不存在可被跳过的括号块。
if not "%~1"=="--docker" goto docker_done
echo [可选] 构建沙箱镜像 mathmodel-sandbox ...
docker build -t mathmodel-sandbox -f backend\Dockerfile.sandbox backend
if errorlevel 1 goto docker_failed
".venv\Scripts\python.exe" -c "import io;p=r'backend\.env';s=io.open(p,encoding='utf-8').read().replace('SANDBOX_BACKEND=subprocess','SANDBOX_BACKEND=docker');io.open(p,'w',encoding='utf-8').write(s)"
echo [可选] 已启用 docker 硬隔离沙箱
goto docker_done
:docker_failed
echo [警告] 沙箱镜像构建失败,继续使用 subprocess 模式(功能不受影响)
:docker_done

echo.
echo ==============================================
echo  安装完成!
echo.
echo  启动:  start.bat   (Windows 一键启动前后端)
echo  前端:  http://localhost:5174
echo  后端:  http://127.0.0.1:8002/docs
echo.
echo  配置 API Key: 打开首页,在「API Key」输入框粘贴你的
echo  DeepSeek/OpenAI 兼容 Key 即可(仅保存在本机 backend\data)。
echo  也可以编辑 backend\.env 填 OPENAI_API_KEY。
echo ==============================================
pause
