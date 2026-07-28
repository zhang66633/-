"""代码沙箱 — subprocess 安全执行 Python 代码。

安全措施:
  - 内存/CPU/文件大小限制 (Unix resource.setrlimit)
  - 网络访问阻断 (socket monkey-patch)
  - 环境变量清洗 (不泄露父进程 API key)
  - 执行超时 (subprocess timeout)
"""

import json
import subprocess
import sys
import tempfile
import os
import uuid
from pathlib import Path
from typing import Optional

from app.config import get_settings


def _make_preexec_fn(max_memory_mb: int, timeout: int):
    """创建 Unix preexec_fn 设置资源限制。Windows 下返回 None。"""
    try:
        import resource
    except ImportError:
        # Windows 无 resource 模块
        return None

    def _set_limits():
        mem_bytes = max_memory_mb * 1024 * 1024
        # 限制虚拟内存
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        # 限制 CPU 时间（秒）
        resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
        # 限制单个文件大小 50MB
        file_limit = 50 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))
        # 禁止 fork 子进程
        resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))

    return _set_limits


def _clean_env() -> dict:
    """构建清洗后的子进程环境变量，仅保留 Python 运行必需项。"""
    # APPDATA / LOCALAPPDATA 必须保留：Windows 用户级 site-packages 位于
    # %APPDATA%\Python\PythonXYZ\site-packages，pip 安装的 numpy/matplotlib/scipy
    # 等都在此，清掉会导致沙箱内所有第三方科学计算包 import 失败。
    safe_keys = {"PATH", "PYTHONPATH", "PYTHONIOENCODING", "TEMP", "TMP", "TMPDIR",
                 "HOME", "USERPROFILE", "SYSTEMROOT", "COMSPEC", "APPDATA", "LOCALAPPDATA"}
    env = {k: v for k, v in os.environ.items() if k.upper() in safe_keys}
    env["PYTHONIOENCODING"] = "utf-8"
    # 显式阻断代理，防止通过 proxy 绕过网络限制
    env.pop("HTTP_PROXY", None)
    env.pop("HTTPS_PROXY", None)
    env.pop("http_proxy", None)
    env.pop("https_proxy", None)
    return env


class SandboxExecutor:
    """在受限子进程中执行 Python 代码。"""

    def __init__(self, timeout: Optional[int] = None):
        settings = get_settings()
        self.timeout = timeout or settings.sandbox_timeout
        self.max_memory_mb = settings.sandbox_max_memory_mb
        self.output_dir = Path(tempfile.gettempdir()) / "mathmodel_outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
                    import logging
                    logging.getLogger(__name__).warning("复制文件到沙箱失败 %s: %s", fpath, e)

        # 包装代码：阻断网络 + 自动保存 matplotlib 图表
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

            # 收集生成的图片
            images = sorted(output_subdir.glob("*.png"))

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:2000],
                "returncode": result.returncode,
                "images": [str(img) for img in images],
                "run_id": run_id,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行超时 ({self.timeout}秒)",
                "returncode": -1,
                "images": [],
                "run_id": run_id,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "images": [],
                "run_id": run_id,
            }

    def _wrap_code(self, code: str, output_dir: str) -> str:
        """包装用户代码：阻断网络 + 自动捕获 matplotlib 输出。"""
        return f'''
# ── 网络阻断：禁止任何 socket 连接 ──
import socket as _socket
_original_connect = _socket.socket.connect
def _blocked_connect(self, *args, **kwargs):
    raise OSError("网络访问已被沙箱禁止")
_socket.socket.connect = _blocked_connect
del _socket, _original_connect

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy
import pandas as pd
import sys
import os

os.chdir({json.dumps(output_dir)})

# 用户代码
{code}

# 自动保存所有打开的图表
for i in plt.get_fignums():
    fig = plt.figure(i)
    fig.savefig(os.path.join({json.dumps(output_dir)}, f"figure_{{i}}.png"),
                dpi=150, bbox_inches="tight")
plt.close("all")
'''
