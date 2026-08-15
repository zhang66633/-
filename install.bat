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
if not exist "backend\.env" (
  echo [4/5] 生成 backend\.env(含随机 JWT_SECRET)...
  copy /y "backend\.env.example" "backend\.env" >nul
  REM 生成随机 JWT_SECRET 并写入
  for /f "delims=" %%t in ('".venv\Scripts\python.exe" -c "import secrets;print(secrets.token_hex(32))"') do set NEWSECRET=%%t
  ".venv\Scripts\python.exe" -c "import io;p=r'backend\.env';s=io.open(p,encoding='utf-8').read().replace('JWT_SECRET=change-me-to-a-random-string','JWT_SECRET=%NEWSECRET%');io.open(p,'w',encoding='utf-8').write(s)"
  REM 端口统一 8002(与 start.py 一致);沙箱默认 subprocess(Docker 可选)
  ".venv\Scripts\python.exe" -c "import io;p=r'backend\.env';s=io.open(p,encoding='utf-8').read();s=s.replace('PORT=8000','PORT=8002').replace('SANDBOX_BACKEND=docker','SANDBOX_BACKEND=subprocess');io.open(p,'w',encoding='utf-8').write(s)"
) else (
  echo [4/5] backend\.env 已存在,跳过
)

REM ── 4. 前端依赖 ─────────────────────────────────
echo [5/5] 安装前端依赖 pnpm install(首次约 2-5 分钟)...
pushd frontend
pnpm install
if errorlevel 1 ( echo [错误] 前端依赖安装失败 & popd & pause & exit /b 1 )
popd

REM ── 5. 可选: Docker 沙箱镜像 ─────────────────────
if "%~1"=="--docker" (
  echo [可选] 构建沙箱镜像 mathmodel-sandbox ...
  docker build -t mathmodel-sandbox -f backend\Dockerfile.sandbox backend
  if errorlevel 1 (
    echo [警告] 沙箱镜像构建失败,继续使用 subprocess 模式(功能不受影响)
  ) else (
    ".venv\Scripts\python.exe" -c "import io;p=r'backend\.env';s=io.open(p,encoding='utf-8').read().replace('SANDBOX_BACKEND=subprocess','SANDBOX_BACKEND=docker');io.open(p,'w',encoding='utf-8').write(s)"
    echo [可选] 已启用 docker 硬隔离沙箱
  )
)

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
