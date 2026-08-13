"""代码沙箱 — subprocess 或 Docker 安全执行 Python 代码。

安全措施:
  - subprocess 模式: 内存/CPU/文件大小限制 (Unix resource.setrlimit) + socket monkey-patch
  - Docker 模式: --network=none --memory=512m 硬隔离（跨平台，推荐）
  - 环境变量清洗 (不泄露父进程 API key)
  - 执行超时
"""

import json
import subprocess
import sys
import tempfile
import os
import uuid
import logging
from pathlib import Path
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

# ── Docker 沙箱镜像名 ──────────────────────────────────────────────

SANDBOX_IMAGE = "mathmodel-sandbox"


def _make_preexec_fn(max_memory_mb: int, timeout: int):
    """创建 Unix preexec_fn 设置资源限制。Windows 下返回 None。"""
    try:
        import resource
    except ImportError:
        return None

    def _set_limits():
        mem_bytes = max_memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
        file_limit = 50 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))
        resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))

    return _set_limits


def _clean_env() -> dict:
    """构建清洗后的子进程环境变量，仅保留 Python 运行必需项。"""
    safe_keys = {"PATH", "PYTHONPATH", "PYTHONIOENCODING", "TEMP", "TMP", "TMPDIR",
                 "HOME", "USERPROFILE", "SYSTEMROOT", "COMSPEC", "APPDATA", "LOCALAPPDATA"}
    env = {k: v for k, v in os.environ.items() if k.upper() in safe_keys}
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("HTTP_PROXY", None)
    env.pop("HTTPS_PROXY", None)
    env.pop("http_proxy", None)
    env.pop("https_proxy", None)
    return env


class SandboxExecutor:
    """在受限子进程或 Docker 容器中执行 Python 代码。

    模式选择:
      - SANDBOX_BACKEND=subprocess (默认): 用 subprocess 在本机执行
      - SANDBOX_BACKEND=docker: 用 docker run --rm 隔离执行（需先构建镜像）
    """

    def __init__(self, timeout: Optional[int] = None):
        settings = get_settings()
        self.timeout = timeout or settings.sandbox_timeout
        self.max_memory_mb = settings.sandbox_max_memory_mb
        self.backend = settings.sandbox_backend
        self.output_dir = Path(tempfile.gettempdir()) / "mathmodel_outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── public API ────────────────────────────────────────────────

    def run(self, code: str, extra_files: list[str] | None = None) -> dict:
        """执行代码，返回 stdout、stderr、图片路径列表。

        extra_files: 可选，需要复制到沙箱工作目录的文件绝对路径列表。
        """
        run_id = str(uuid.uuid4())[:8]
        output_subdir = self.output_dir / run_id
        output_subdir.mkdir(parents=True, exist_ok=True)

        # 复制额外文件到沙箱工作目录
        if extra_files:
            import shutil as _shutil
            for fpath in extra_files:
                try:
                    _shutil.copy2(fpath, str(output_subdir / Path(fpath).name))
                except Exception as e:
                    logger.warning("复制文件到沙箱失败 %s: %s", fpath, e)

        if self.backend == "docker":
            return self._run_docker(code, output_subdir, run_id)
        else:
            return self._run_subprocess(code, output_subdir, run_id)

    # ── subprocess 模式 ──────────────────────────────────────────

    def _run_subprocess(self, code: str, output_subdir: Path, run_id: str) -> dict:
        """在本机子进程中执行（原有逻辑）。"""
        wrapped_code = self._wrap_code(code, str(output_subdir))

        try:
            result = subprocess.run(
                [sys.executable, "-c", wrapped_code],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(output_subdir),
                encoding="utf-8",
                errors="replace",
                env=_clean_env(),
                preexec_fn=_make_preexec_fn(self.max_memory_mb, self.timeout),
            )

            images = sorted(output_subdir.glob("*.png"))
            xlsx_files = sorted(output_subdir.glob("*.xlsx"))
            csv_files = sorted(output_subdir.glob("*.csv"))
            html_files = sorted(output_subdir.glob("*.html"))
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:2000],
                "returncode": result.returncode,
                "images": [str(img) for img in images],
                "xlsx_files": [str(f) for f in xlsx_files],
                "csv_files": [str(f) for f in csv_files],
                "html_files": [str(f) for f in html_files],
                "run_id": run_id,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False, "stdout": "", "stderr": f"执行超时 ({self.timeout}秒)",
                "returncode": -1, "images": [], "xlsx_files": [], "csv_files": [], "html_files": [], "run_id": run_id,
            }
        except Exception as e:
            return {
                "success": False, "stdout": "", "stderr": str(e),
                "returncode": -1, "images": [], "xlsx_files": [], "csv_files": [], "html_files": [], "run_id": run_id,
            }

    # ── Docker 模式 ──────────────────────────────────────────────

    def _run_docker(self, code: str, output_subdir: Path, run_id: str) -> dict:
        """在 Docker 容器中隔离执行。

        安全: --network=none 阻断网络, --memory 硬限制内存,
              --rm 执行完自动销毁, 不残留文件系统状态。
        """
        # 将代码写入临时文件，挂载进容器
        code_file = output_subdir / "_code.py"
        code_file.write_text(code, encoding="utf-8")

        # 容器内输出目录
        container_output = "/output"

        cmd = [
            "docker", "run", "--rm",
            "--network=none",
            f"--memory={self.max_memory_mb}m",
            f"--memory-swap={self.max_memory_mb}m",  # 禁用 swap
            "-v", f"{output_subdir}:{container_output}",
            SANDBOX_IMAGE,
            f"{container_output}/_code.py",
            container_output,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 10,  # Docker 启动需要额外时间
                encoding="utf-8",
                errors="replace",
            )

            images = sorted(
                p for p in output_subdir.glob("*.png")
                if p.name != "_code.py"
            )
            xlsx_files = sorted(
                p for p in output_subdir.glob("*.xlsx")
                if p.name != "_code.py"
            )
            csv_files = sorted(
                p for p in output_subdir.glob("*.csv")
                if p.name != "_code.py"
            )
            html_files = sorted(
                p for p in output_subdir.glob("*.html")
                if p.name != "_code.py"
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:2000],
                "returncode": result.returncode,
                "images": [str(img) for img in images],
                "xlsx_files": [str(f) for f in xlsx_files],
                "csv_files": [str(f) for f in csv_files],
                "html_files": [str(f) for f in html_files],
                "run_id": run_id,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False, "stdout": "", "stderr": f"执行超时 ({self.timeout}秒)",
                "returncode": -1, "images": [], "xlsx_files": [], "csv_files": [], "html_files": [], "run_id": run_id,
            }
        except FileNotFoundError:
            return {
                "success": False, "stdout": "",
                "stderr": (
                    "Docker 未安装或未在 PATH 中。请安装 Docker Desktop，"
                    "然后执行: docker build -t mathmodel-sandbox -f Dockerfile.sandbox ."
                ),
                "returncode": -1, "images": [], "xlsx_files": [], "csv_files": [], "html_files": [], "run_id": run_id,
            }
        except Exception as e:
            return {
                "success": False, "stdout": "", "stderr": str(e),
                "returncode": -1, "images": [], "xlsx_files": [], "csv_files": [], "html_files": [], "run_id": run_id,
            }

    def _wrap_code(self, code: str, output_dir: str) -> str:
        """包装用户代码：阻断网络 + 按需导入 + 自动捕获 matplotlib 输出。

        不再预导入 numpy/scipy/pandas —— LLM 生成的代码自带 import，预导入浪费
        200-500MB 内存每个沙箱进程。matplotlib 仅设置 backend（轻量），pyplot 按需导入。
        """
        return f'''
# ── 网络阻断：禁止任何 socket 连接 ──
import socket as _socket
_original_connect = _socket.socket.connect
def _blocked_connect(self, *args, **kwargs):
    raise OSError("网络访问已被沙箱禁止")
_socket.socket.connect = _blocked_connect
del _socket, _original_connect

import sys as _sys
import os as _os

# 必须在任何 pyplot import 之前设置 Agg backend（仅配置，不加载 pyplot）
import matplotlib as _mpl
_mpl.use("Agg")

_os.chdir({json.dumps(output_dir)})

# ── 用户代码（LLM 自行 import 所需库）──
{code}

# ── 自动保存 matplotlib 图表（仅当用户代码用到了 pyplot）──
if "matplotlib.pyplot" in _sys.modules:
    import matplotlib.pyplot as _plt
    for i in _plt.get_fignums():
        fig = _plt.figure(i)
        fig.savefig(_os.path.join({json.dumps(output_dir)}, f"figure_{{i}}.png"),
                    dpi=150, bbox_inches="tight")
    _plt.close("all")
'''
