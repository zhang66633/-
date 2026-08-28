"""Redis Pub/Sub service — decouples agent execution from WebSocket message delivery.

Architecture:
  Agent nodes (synchronous)  ──publish──▶  Redis channel  ──subscribe──▶  WebSocket endpoint

This keeps the LangGraph StateGraph nodes lightweight (fire-and-forget publish)
while the async WebSocket endpoint consumes events streamingly.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import redis as sync_redis
import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)

# ── FakeRedis fallback (when Redis server is not available) ──────────
_FAKEREDIS_AVAILABLE = False
_fake_server = None

try:
    import fakeredis
    import fakeredis.aioredis as fake_aioredis

    _FAKEREDIS_AVAILABLE = True
except ImportError:
    pass


def _get_fake_server():
    """Get or create a shared FakeServer so pub/sub works across clients."""
    global _fake_server
    if _fake_server is None and _FAKEREDIS_AVAILABLE:
        _fake_server = fakeredis.FakeServer()
    return _fake_server


def _create_sync_client(redis_url: str):
    """Create a sync Redis client, falling back to fakeredis if needed."""
    try:
        client = sync_redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        logger.info("Connected to real Redis at %s", redis_url)
        return client
    except Exception:
        if _FAKEREDIS_AVAILABLE:
            logger.info("Redis unavailable — using fakeredis (in-memory)")
            return fakeredis.FakeRedis(server=_get_fake_server(), decode_responses=True)
        raise


async def _create_async_client(redis_url: str):
    """Create an async Redis client, falling back to fakeredis if needed."""
    try:
        client = aioredis.Redis.from_url(redis_url, decode_responses=True)
        await client.ping()
        logger.info("Connected to real Redis (async) at %s", redis_url)
        return client
    except Exception:
        if _FAKEREDIS_AVAILABLE:
            logger.info("Redis unavailable — using fakeredis (in-memory, async)")
            return fake_aioredis.FakeRedis(server=_get_fake_server(), decode_responses=True)
        raise


# ── Event types ──────────────────────────────────────────────────────


class ProgressEvent:
    """Standard event envelope sent over Redis."""

    NODE_START = "node_start"
    NODE_END = "node_end"
    PROGRESS = "progress"
    ERROR = "error"
    TASK_END = "task_end"

    def __init__(
        self,
        event: str,
        node: str,
        task_id: str,
        data: dict | None = None,
        seq: int | None = None,
    ):
        self.event = event
        self.node = node
        self.task_id = task_id
        self.timestamp = datetime.now(UTC).isoformat()
        self.data = data or {}
        # 事件序号（每任务单调递增，与 JSONL 行号对齐）：前端据此对
        # WS 实时事件 vs REST 回放做幂等去重与断线增量补拉（协议 v2.2）
        self.seq = seq

    def to_json(self) -> str:
        payload: dict = {
            "event": self.event,
            "node": self.node,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }
        if self.seq is not None:
            payload["seq"] = self.seq
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def channel_for(task_id: str) -> str:
        return f"task:{task_id}"


# ── Synchronous publisher (called from LangGraph nodes) ──────────────


class RedisPublisher:
    """Synchronous Redis publisher for use inside LangGraph nodes.

    Nodes run in a thread-pool (via asyncio.to_thread), so a sync client is
    cleaner than mixing asyncio loops.
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: sync_redis.Redis | None = None

    @property
    def client(self) -> sync_redis.Redis:
        if self._client is None:
            self._client = _create_sync_client(self.redis_url)
        return self._client

    def publish(
        self,
        task_id: str,
        event: str,
        node: str,
        data: dict | None = None,
        seq: int | None = None,
    ) -> int:
        """Publish an event to the task's channel.

        seq: 事件序号（可选），透传进事件信封供前端幂等去重。

        Returns the number of subscribers that received the message.
        """
        msg = ProgressEvent(event=event, node=node, task_id=task_id, data=data, seq=seq)
        channel = ProgressEvent.channel_for(task_id)
        try:
            return self.client.publish(channel, msg.to_json())
        except Exception:
            logger.warning("Failed to publish event to channel %s", channel, exc_info=True)
            return 0

    def node_start(self, task_id: str, node: str, data: dict | None = None) -> int:
        """Shorthand for publishing a node_start event."""
        return self.publish(task_id, ProgressEvent.NODE_START, node, data)

    def node_end(self, task_id: str, node: str, data: dict | None = None) -> int:
        """Shorthand for publishing a node_end event."""
        return self.publish(task_id, ProgressEvent.NODE_END, node, data)

    def progress(self, task_id: str, node: str, data: dict | None = None) -> int:
        """Shorthand for publishing a progress event."""
        return self.publish(task_id, ProgressEvent.PROGRESS, node, data)

    def error(self, task_id: str, node: str, error_msg: str) -> int:
        """Shorthand for publishing an error event."""
        return self.publish(task_id, ProgressEvent.ERROR, node, {"message": error_msg})

    def task_end(self, task_id: str, node: str, status: str, data: dict | None = None) -> int:
        """Shorthand for publishing a task_end (completion) event."""
        payload = {"status": status}
        if data:
            payload.update(data)
        return self.publish(task_id, ProgressEvent.TASK_END, node, payload)

    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ── Asynchronous subscriber (consumed by WebSocket) ──────────────────


class RedisSubscriber:
    """Async Redis subscriber that yields events as an async generator.

    Usage in a WebSocket endpoint:

        subscriber = RedisSubscriber(redis_url)
        async for event_json in subscriber.subscribe(task_id):
            await websocket.send_text(event_json)
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url

    async def subscribe(self, task_id: str) -> AsyncGenerator[str, None]:
        """Subscribe to a task channel and yield event JSON strings."""
        try:
            client = await _create_async_client(self.redis_url)
            pubsub = client.pubsub()
            channel = ProgressEvent.channel_for(task_id)

            await pubsub.subscribe(channel)
            logger.info("Subscribed to Redis channel: %s", channel)

            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        yield message["data"]
            finally:
                await pubsub.unsubscribe(channel)
                await client.aclose()
        except Exception:
            logger.warning("Redis subscriber for task %s disconnected", task_id, exc_info=True)
            # Yield nothing on connection failure — WebSocket will close cleanly


# ── Module-level publisher singleton ─────────────────────────────────

_publisher: RedisPublisher | None = None


def get_publisher() -> RedisPublisher:
    """Get or create the global sync Redis publisher."""
    global _publisher
    if _publisher is None:
        settings = get_settings()
        _publisher = RedisPublisher(settings.redis_url)
    return _publisher


def shutdown_publisher():
    """Close the global publisher (call on app shutdown)."""
    global _publisher
    if _publisher:
        _publisher.close()
        _publisher = None
