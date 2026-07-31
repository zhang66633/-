"""会话管理 REST API — 对话列表、消息同步、删除。

依赖于 SqliteSessionStore 进行持久化。
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..services.sqlite_session_store import get_sqlite_store

logger = logging.getLogger(__name__)

session_router = APIRouter(prefix="/conversations", tags=["Conversations"])

# ── 请求/响应模型 ─────────────────────────────────────

class CreateConversationRequest(BaseModel):
    mode: str = "chat"          # chat | qa | practice | solution | learning
    title: str = "新对话"


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None


class MessagePayload(BaseModel):
    id: str
    msg_type: str
    content: Optional[str] = None
    tool_name: Optional[str] = None
    input: Optional[dict] = None
    output: Optional[list] = None
    status: Optional[str] = None
    thinking: Optional[str] = None
    agent_type: Optional[str] = None
    answered: Optional[bool] = None
    streaming: Optional[bool] = None
    created_at: Optional[str] = None


class SyncMessagesRequest(BaseModel):
    messages: list[MessagePayload]


# ── 路由 ─────────────────────────────────────────────

@session_router.get("")
async def list_conversations(
    mode: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """列出当前用户的会话列表，按更新时间倒序。"""
    store = get_sqlite_store()
    convs = store.list_conversations(mode=mode, limit=limit, offset=offset)
    return {
        "conversations": convs,
        "total": store.count_conversations(),
    }


@session_router.post("")
async def create_conversation(req: CreateConversationRequest):
    """创建新会话。"""
    store = get_sqlite_store()
    conv = store.create_conversation(mode=req.mode, title=req.title)
    return {"conversation": conv}


@session_router.get("/{conv_id}")
async def get_conversation(conv_id: str):
    """获取单个会话详情。"""
    store = get_sqlite_store()
    conv = store.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"conversation": conv}


@session_router.patch("/{conv_id}")
async def update_conversation(conv_id: str, req: UpdateConversationRequest):
    """更新会话标题。"""
    store = get_sqlite_store()
    updates = {}
    if req.title is not None:
        updates["title"] = req.title
    conv = store.update_conversation(conv_id, **updates)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"conversation": conv}


@session_router.delete("/{conv_id}")
async def delete_conversation(conv_id: str):
    """删除会话及其所有消息。"""
    store = get_sqlite_store()
    ok = store.delete_conversation(conv_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"status": "ok"}


# ── 消息路由 ─────────────────────────────────────────

@session_router.get("/{conv_id}/messages")
async def get_messages(
    conv_id: str,
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
):
    """获取会话消息列表。"""
    store = get_sqlite_store()
    conv = store.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    msgs = store.get_messages(conv_id, limit=limit, offset=offset)
    return {
        "messages": msgs,
        "total": store.count_messages(conv_id),
    }


@session_router.post("/{conv_id}/messages")
async def add_message(conv_id: str, msg: MessagePayload):
    """追加一条消息到会话。"""
    store = get_sqlite_store()
    conv = store.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    result = store.add_message(conv_id, msg.model_dump(exclude_none=True))
    if result is None:
        raise HTTPException(status_code=409, detail="消息 ID 重复")
    return {"message": result}


@session_router.post("/{conv_id}/sync")
async def sync_messages(conv_id: str, req: SyncMessagesRequest):
    """批量同步消息（用于前端 localStorage → 后端首次迁移）。"""
    store = get_sqlite_store()
    conv = store.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    count = store.add_messages_batch(
        conv_id,
        [m.model_dump(exclude_none=True) for m in req.messages],
    )
    return {"synced": count}