"""知识库批量导入 API — PDF 上传 → LLM 提取 → 预览 → 确认入库。"""

import io
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.auth import GitHubUser, require_contributor
from app.config import get_settings
from app.services.kb_extractor import KBExtractor

logger = logging.getLogger(__name__)

import_router = APIRouter(prefix="/knowledge/import", tags=["knowledge-import"])

# 上传文件大小限制: 20MB
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


class ConfirmRequest(BaseModel):
    """确认入库请求 — 前端审核后发回已编辑的 YAML 数据。"""
    type: str  # "paper" | "method"
    data: dict  # 完整 YAML 结构
    embed: bool = True  # 是否立即向量化


# ── 论文导入 ───────────────────────────────────────────────

@import_router.post("/paper")
async def import_paper(
    file: UploadFile = File(...),
    user: GitHubUser = Depends(require_contributor),
):
    """上传 PDF/文本文件，LLM 提取论文结构化信息，返回预览。

    不直接写入 YAML — 用户在前端审核后调用 /confirm 入库。
    """
    if not file.filename:
        raise HTTPException(400, "文件名为空")

    suffix = (file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "")
    if suffix not in ("pdf", "txt", "md"):
        raise HTTPException(400, "仅支持 PDF/TXT/MD 文件")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, f"文件超过 {MAX_UPLOAD_BYTES // 1024 // 1024}MB 限制")

    extractor = KBExtractor()

    # 提取文本
    if suffix == "pdf":
        text = extractor.extract_pdf_text(data)
    else:
        text = data.decode("utf-8", errors="replace")

    if not text.strip():
        raise HTTPException(400, "无法从文件中提取文本")

    # LLM 结构化提取
    result = extractor.extract_paper(text, file.filename)

    if result["status"] == "error":
        raise HTTPException(422, f"提取失败: {result['error']}")

    return {
        "status": "preview",
        "type": "paper",
        "data": result["data"],
        "paper_id": result.get("paper_id"),
        "text_preview": text[:1000],
    }


# ── 方法卡片导入 ───────────────────────────────────────────

@import_router.post("/method")
async def import_method(
    file: UploadFile = File(...),
    user: GitHubUser = Depends(require_contributor),
):
    """上传文本文件，LLM 提取方法卡片结构化信息，返回预览。"""
    if not file.filename:
        raise HTTPException(400, "文件名为空")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, f"文件超过 {MAX_UPLOAD_BYTES // 1024 // 1024}MB 限制")

    text = data.decode("utf-8", errors="replace")
    if not text.strip():
        raise HTTPException(400, "无法从文件中提取文本")

    extractor = KBExtractor()
    result = extractor.extract_method(text, file.filename)

    if result["status"] == "error":
        raise HTTPException(422, f"提取失败: {result['error']}")

    return {
        "status": "preview",
        "type": "method",
        "data": result["data"],
        "method_id": result.get("method_id"),
        "text_preview": text[:1000],
    }


# ── 确认入库 ───────────────────────────────────────────────

@import_router.post("/confirm")
async def confirm_import(
    req: ConfirmRequest,
    user: GitHubUser = Depends(require_contributor),
):
    """审核通过，写入 YAML 并可选立即向量化。

    前端可在预览阶段编辑 LLM 提取结果后再提交。
    """
    if req.type not in ("paper", "method"):
        raise HTTPException(400, "type 必须为 paper 或 method")

    extractor = KBExtractor()

    try:
        if req.type == "paper":
            path = extractor.write_paper(req.data)
        else:
            path = extractor.write_method(req.data)

        doc_count = 0
        embed_error = None
        if req.embed:
            try:
                doc_count = extractor.embed_new(path)
            except Exception as e:
                embed_error = str(e)
                logger.warning("向量化失败: %s", e)

        return {
            "status": "ok",
            "type": req.type,
            "path": str(path),
            "embedded": req.embed and embed_error is None,
            "doc_count": doc_count,
            "embed_error": embed_error,
        }

    except Exception as e:
        logger.exception("入库失败")
        raise HTTPException(500, f"写入失败: {e}")


# ── 文本直接提取（无文件）────────────────────────────────

@import_router.post("/extract-text")
async def extract_from_text(
    text: str = Form(...),
    extract_type: str = Form("paper"),
    user: GitHubUser = Depends(require_contributor),
):
    """粘贴纯文本直接提取（不经过文件上传）。"""
    if not text.strip():
        raise HTTPException(400, "文本为空")

    extractor = KBExtractor()

    if extract_type == "paper":
        result = extractor.extract_paper(text)
    elif extract_type == "method":
        result = extractor.extract_method(text)
    else:
        raise HTTPException(400, "type 必须为 paper 或 method")

    if result["status"] == "error":
        raise HTTPException(422, f"提取失败: {result['error']}")

    return {
        "status": "preview",
        "type": extract_type,
        "data": result["data"],
        "paper_id": result.get("paper_id"),
        "method_id": result.get("method_id"),
    }
