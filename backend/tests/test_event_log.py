"""协议 v2.1 事件持久化与回放 — node_helpers._log_event / read_task_events 单测。

覆盖:
  - 事件按顺序追加到 JSONL，可完整回放
  - after/limit 切片增量回放
  - 不存在的任务返回空列表
  - tool_call_id 在 tool_call/tool_result 事件对中保持一致（前端精确配对的前提）
"""

from __future__ import annotations

import threading

from app.core import node_helpers
from app.core.node_helpers import _log_event, read_task_events


def test_event_log_roundtrip(tmp_path, monkeypatch):
    """事件写入后可按序回放，字段完整。"""
    monkeypatch.setattr(node_helpers, "_event_log_path", lambda tid: tmp_path / f"{tid}.jsonl")

    _log_event("t1", "node_start", "classify_problem", {"step": 1})
    _log_event("t1", "plan", "plan_execution", {"plan": ["analysis", "solving"]})
    _log_event("t1", "tool_call", "solving_agent", {"tool_call_id": "call-1", "status": "running"})
    _log_event("t1", "tool_result", "solving_agent", {"tool_call_id": "call-1", "ok": True})

    events, total = read_task_events("t1")
    assert total == 4
    assert [e["event"] for e in events] == ["node_start", "plan", "tool_call", "tool_result"]
    assert events[1]["data"]["plan"] == ["analysis", "solving"]
    # 事件对 id 一致：前端按 tool_call_id 精确配对
    assert events[2]["data"]["tool_call_id"] == events[3]["data"]["tool_call_id"] == "call-1"
    assert events[2]["task_id"] == "t1"


def test_event_log_slice(tmp_path, monkeypatch):
    """after/limit 增量回放：只返回新事件并给出总数。"""
    monkeypatch.setattr(node_helpers, "_event_log_path", lambda tid: tmp_path / f"{tid}.jsonl")

    for i in range(10):
        _log_event("t2", "node_end", "analysis_agent", {"step": i})

    events, total = read_task_events("t2", after=7, limit=100)
    assert total == 10
    assert len(events) == 3
    assert events[0]["data"]["step"] == 7


def test_event_log_missing_task(tmp_path, monkeypatch):
    """不存在的任务回放为空。"""
    monkeypatch.setattr(node_helpers, "_event_log_path", lambda tid: tmp_path / f"{tid}.jsonl")
    events, total = read_task_events("nope")
    assert events == []
    assert total == 0


def test_event_log_publish_sidecar(tmp_path, monkeypatch):
    """_pub_event 在 Redis 之外旁路落盘（fakeredis 不可用时也不阻塞）。"""
    monkeypatch.setattr(node_helpers, "_event_log_path", lambda tid: tmp_path / f"{tid}.jsonl")

    # _pub_event 内部 get_publisher 可能连真实 Redis，这里 monkeypatch 成 no-op
    monkeypatch.setattr(node_helpers, "get_publisher", lambda: _NoopPublisher())

    _pub_event = node_helpers._pub_event
    _pub_event("t3", "tool_call", "solving_agent", {"tool_call_id": "c-9"})

    events, total = read_task_events("t3")
    assert total == 1
    assert events[0]["event"] == "tool_call"
    assert events[0]["data"]["tool_call_id"] == "c-9"


class _NoopPublisher:
    def publish(self, *a, **k):
        return 0


def test_event_log_path_isolated_per_task(tmp_path, monkeypatch):
    """不同任务的事件互不串扰。"""
    monkeypatch.setattr(node_helpers, "_event_log_path", lambda tid: tmp_path / f"{tid}.jsonl")

    _log_event("a", "node_start", "classify_problem")
    _log_event("b", "node_start", "classify_problem")

    events_a, _ = read_task_events("a")
    events_b, _ = read_task_events("b")
    assert len(events_a) == 1
    assert len(events_b) == 1
    assert events_a[0]["task_id"] == "a"
    assert events_b[0]["task_id"] == "b"


def test_tool_call_id_helper():
    """tool_call_id：优先 LLM id，缺失时稳定生成本地 id。"""
    assert node_helpers.tool_call_id({"id": "llm-1"}, "run_code") == "llm-1"
    assert node_helpers.tool_call_id({"tool_call_id": "tc-2"}, "run_code") == "tc-2"
    local = node_helpers.tool_call_id({}, "run_code")
    assert local.startswith("run_code-")
    # 无状态输入 → 两次生成不同 id（保证同一轮内多个同名工具可区分）
    assert local != node_helpers.tool_call_id({}, "run_code")


def test_cancel_event_helper():
    """get_cancel_event 返回可置位的 threading.Event。"""
    ev = node_helpers.get_cancel_event("test-cancel-1")
    if ev is not None:  # session manager 可用时
        assert isinstance(ev, threading.Event)
        ev.set()
        assert ev.is_set()
