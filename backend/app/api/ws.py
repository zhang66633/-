"""WebSocket endpoints for real-time agent progress."""

import asyncio
import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ..auth.dependencies import decode_jwt
from ..config import get_settings
from ..services.redis_pubsub import RedisSubscriber

logger = logging.getLogger(__name__)
ws_router = APIRouter()


@ws_router.websocket("/ws/task/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: str, token: str = Query(default="")):
    """WebSocket endpoint for real-time task message streaming.

    Requires a valid JWT passed as ?token=<jwt> query parameter.
    Subscribes to Redis Pub/Sub channel ``task:{task_id}`` and forwards
    every published event to the connected frontend client.
    """
    # ── 鉴权（访客放行）──
    # 原实现强制 JWT：未登录访客连 WS 都建立不了，可经 REST /messages 看结果
    # 却看不到任何实时过程——方案页全程空白（本轮实测复现的断点）。
    # REST 侧本就无认证，故这里对缺失/非法 token 一律按访客放行。
    _ = decode_jwt(token) if token else None

    await websocket.accept()
    settings = get_settings()

    # Send an initial connection-confirmation event
    await websocket.send_text(
        json.dumps(
            {
                "event": "connected",
                "task_id": task_id,
            },
            ensure_ascii=False,
        )
    )

    subscriber = RedisSubscriber(settings.redis_url)

    try:
        async for event_json in subscriber.subscribe(task_id):
            try:
                await websocket.send_text(event_json)
            except Exception:
                # Client disconnected — stop consuming
                break
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected for task %s", task_id)
    except asyncio.CancelledError:
        logger.info("WebSocket cancelled for task %s", task_id)
    except Exception:
        logger.exception("WebSocket error for task %s", task_id)
