"""SQLite 会话存储：用户隔离（发现 #4）+ 连接复用（发现 #23）测试。

运行: 在 backend/ 目录下 `python -m pytest tests/test_sqlite_store.py -q`
      或直接 `python tests/test_sqlite_store.py`。

注: 使用 `:memory:` 数据库——DSH 沙箱环境对 sqlite 原生文件创建有限制，
内存库覆盖全部 SQL 语义（隔离/过滤/复用），文件持久化语义由真实运行验证。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.sqlite_session_store import SqliteSessionStore  # noqa: E402


def _new_store() -> SqliteSessionStore:
    return SqliteSessionStore(Path(":memory:"))


def test_user_isolation():
    store = _new_store()
    try:
        a = store.create_conversation(user_id="alice", title="A de hui hua")
        b = store.create_conversation(user_id="bob", title="B de hui hua")

        # 列表隔离
        assert [c["id"] for c in store.list_conversations(user_id="alice")] == [a["id"]]
        assert [c["id"] for c in store.list_conversations(user_id="bob")] == [b["id"]]

        # 属主校验：bob 看不到 alice 的会话（视为不存在）
        assert store.get_conversation(a["id"], user_id="bob") is None
        assert store.get_conversation(a["id"], user_id="alice") is not None

        # 删除也按属主隔离
        assert store.delete_conversation(a["id"], user_id="bob") is False
        assert store.delete_conversation(b["id"], user_id="bob") is True
        assert store.get_conversation(b["id"], user_id="bob") is None
    finally:
        store.close()


def test_connection_reuse():
    store = _new_store()
    try:
        assert store._get_conn() is store._get_conn(), "同线程应复用同一连接"
    finally:
        store.close()


def test_crud_roundtrip():
    store = _new_store()
    try:
        conv = store.create_conversation(user_id="guest", mode="chat", title="test")
        store.add_message(conv["id"], {"id": "m1", "msg_type": "user", "content": "hello"})
        msgs = store.get_messages(conv["id"])
        assert len(msgs) == 1 and msgs[0]["content"] == "hello"
    finally:
        store.close()


if __name__ == "__main__":
    test_user_isolation()
    test_connection_reuse()
    test_crud_roundtrip()
    print("ALL TESTS PASSED")
