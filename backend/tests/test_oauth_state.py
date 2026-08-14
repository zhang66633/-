"""OAuth login CSRF state 校验测试（审计发现 #6）。

运行: 在 backend/ 目录下 `python -m pytest tests/test_oauth_state.py -q`
      或直接 `python tests/test_oauth_state.py`。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import HTTPException  # noqa: E402

from app.api.router import github_callback, OAUTH_STATE_COOKIE  # noqa: E402


class _FakeRequest:
    def __init__(self, cookies: dict):
        self.cookies = cookies


class _FakeResponse:
    def __init__(self):
        self.deleted = []

    def delete_cookie(self, name: str):
        self.deleted.append(name)


def _expect_400(code: str, state: str, cookies: dict):
    try:
        import asyncio
        asyncio.run(github_callback(
            code=code, state=state,
            request=_FakeRequest(cookies), response=_FakeResponse(),
        ))
    except HTTPException as e:
        assert e.status_code == 400, f"期望 400，实际 {e.status_code}"
        return
    raise AssertionError("缺少 state/state 不匹配时应拒绝")


def test_missing_state_rejected():
    _expect_400(code="abc", state="", cookies={OAUTH_STATE_COOKIE: "s1"})


def test_missing_cookie_rejected():
    _expect_400(code="abc", state="s1", cookies={})


def test_mismatched_state_rejected():
    _expect_400(code="abc", state="s1", cookies={OAUTH_STATE_COOKIE: "s2"})


def test_matched_state_deletes_cookie_and_proceeds():
    # 匹配时进入 GitHub 交换流程（会发起网络请求），此处只验证不因 state 被拒：
    # 网络类异常（无网环境）视为已通过 state 关；仅 state 相关的 400 视为失败。
    import asyncio

    resp = _FakeResponse()
    try:
        asyncio.run(github_callback(
            code="abc", state="s1",
            request=_FakeRequest({OAUTH_STATE_COOKIE: "s1"}), response=resp,
        ))
    except HTTPException as e:
        # 下游 GitHub 交换对伪造 code 也会 400（"无法获取 GitHub access token"），
        # 只要不是 state 相关的 400（"OAuth state 校验失败"）即视为通过 state 关。
        assert "state" not in e.detail.lower(), f"state 匹配时不应被 state 校验拒绝: {e.detail}"
    except Exception:
        pass  # 网络不可用等后续流程错误，与本测试无关
    assert OAUTH_STATE_COOKIE in resp.deleted, "校验通过后应清除 state cookie"


if __name__ == "__main__":
    test_missing_state_rejected()
    test_missing_cookie_rejected()
    test_mismatched_state_rejected()
    test_matched_state_deletes_cookie_and_proceeds()
    print("ALL TESTS PASSED")
