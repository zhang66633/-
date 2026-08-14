"""沙箱 daemon 探测与自动回退测试（013 重点①）。

运行: 在 backend/ 目录下 `python -m pytest tests/test_sandbox_status.py -q`
      或直接 `python tests/test_sandbox_status.py`。
"""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.sandbox.executor as executor  # noqa: E402


def _reset_probe():
    executor._daemon_probe["ok"] = None
    executor._daemon_probe["ts"] = 0.0


class _Proc:
    def __init__(self, returncode: int, stdout: str):
        self.returncode = returncode
        self.stdout = stdout


def test_docker_binary_missing():
    _reset_probe()
    with patch.object(executor.subprocess, "run", side_effect=FileNotFoundError):
        assert executor.docker_daemon_up() is False


def test_daemon_down():
    _reset_probe()
    with patch.object(executor.subprocess, "run",
                      return_value=_Proc(1, "Cannot connect to the Docker daemon")):
        assert executor.docker_daemon_up() is False


def test_daemon_up():
    _reset_probe()
    with patch.object(executor.subprocess, "run", return_value=_Proc(0, "29.4.3")):
        assert executor.docker_daemon_up() is True


def test_probe_result_cached_60s():
    _reset_probe()
    calls = []

    def _fake(*a, **k):
        calls.append(1)
        return _Proc(0, "29.4.3")

    with patch.object(executor.subprocess, "run", side_effect=_fake):
        assert executor.docker_daemon_up() is True
        assert executor.docker_daemon_up() is True
    assert len(calls) == 1, "60 秒内应命中缓存，不重复探测"


def test_run_falls_back_to_subprocess_when_daemon_down():
    """配置 docker 但 daemon 不可用 → run() 走 subprocess 路径（真实执行 print(1+1)）。"""
    _reset_probe()
    with patch.object(executor.subprocess, "run", side_effect=FileNotFoundError):
        assert executor.docker_daemon_up() is False
    ex = executor.SandboxExecutor(timeout=30)
    ex.backend = "docker"
    result = ex.run("print(1+1)")
    assert result["success"] is True, f"回退 subprocess 应执行成功: {result.get('stderr')}"
    assert "2" in result["stdout"]


if __name__ == "__main__":
    test_docker_binary_missing()
    test_daemon_down()
    test_daemon_up()
    test_probe_result_cached_60s()
    test_run_falls_back_to_subprocess_when_daemon_down()
    print("ALL TESTS PASSED")
