"""API key 验证 base_url 的 SSRF 校验测试（审计发现 #7）。

运行: 在 backend/ 目录下 `python -m pytest tests/test_apikeys_ssrf.py -q`
      或直接 `python tests/test_apikeys_ssrf.py`。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import HTTPException  # noqa: E402

from app.api.apikeys import _validate_custom_base_url  # noqa: E402


def _expect_reject(url: str):
    try:
        _validate_custom_base_url(url)
    except HTTPException:
        return
    raise AssertionError(f"base_url {url!r} 应被拒绝")


def test_http_scheme_rejected():
    _expect_reject("http://api.deepseek.com")
    _expect_reject("http://example.com/v1")


def test_private_and_loopback_rejected():
    _expect_reject("https://127.0.0.1")
    _expect_reject("https://10.0.0.5/v1")
    _expect_reject("https://192.168.1.1")
    _expect_reject("https://169.254.169.254/latest/meta-data")  # 云元数据地址
    _expect_reject("https://[::1]")


def test_public_https_accepted():
    assert (
        _validate_custom_base_url("https://api.deepseek.com").rstrip("/")
        == "https://api.deepseek.com"
    )
    assert (
        _validate_custom_base_url("https://dashscope.aliyuncs.com/compatible-mode")
        == "https://dashscope.aliyuncs.com/compatible-mode"
    )


def test_empty_accepted():
    assert _validate_custom_base_url("") == ""


if __name__ == "__main__":
    test_http_scheme_rejected()
    test_private_and_loopback_rejected()
    test_public_https_accepted()
    test_empty_accepted()
    print("ALL TESTS PASSED")
