"""知识库手工 CRUD 路由（god-files 拆分 #31：从 knowledge_routes.py 拆出）。"""

"""Knowledge base management API — browse, search, reindex, upload, and CRUD."""

import re
import uuid

import yaml
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from ..config import get_settings
from ..auth.dependencies import require_contributor
from ..auth.schemas import GitHubUser


from .knowledge_shared import *  # noqa: F403
from .knowledge_shared import (  # noqa: F401
    _get_embedder, _find_yaml_file, _next_id,
)

knowledge_router = APIRouter()


# ── CRUD: methods ────────────────────────────────────────────────


@knowledge_router.post("/methods", response_model=KnowledgeCrudResponse)
async def create_method(data: dict, user: GitHubUser = Depends(require_contributor)):
    """手动创建方法卡片（不经过 LLM）。"""
    try:
        entry_id = _next_id("method")
        data["id"] = entry_id
        from ..knowledge.schemas import MethodCard
        validated = MethodCard(**data)

        yaml_str = yaml.dump(
            {"method_card": validated.model_dump()},
            allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2,
        )
        settings = get_settings()
        cat = (data.get("category") or ["other"])[0]
        safe_name = (data.get("name") or entry_id).replace(" ", "_")
        out_dir = settings.kb_root / "methods" / cat
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{safe_name}.yaml"
        out_path.write_text(yaml_str, encoding="utf-8")

        embedder = _get_embedder()
        embedder.add_document(out_path)

        return KnowledgeCrudResponse(success=True, entry_id=entry_id, message="方法卡片已创建")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建失败: {e}")


@knowledge_router.put("/methods/{card_id}", response_model=KnowledgeCrudResponse)
async def update_method(card_id: str, data: dict, user: GitHubUser = Depends(require_contributor)):
    """更新方法卡片。"""
    try:
        yf = _find_yaml_file("method", card_id)
        if not yf:
            raise HTTPException(status_code=404, detail=f"方法卡片 {card_id} 不存在")

        data["id"] = card_id
        from ..knowledge.schemas import MethodCard
        validated = MethodCard(**data)

        yaml_str = yaml.dump(
            {"method_card": validated.model_dump()},
            allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2,
        )
        yf.write_text(yaml_str, encoding="utf-8")

        embedder = _get_embedder()
        embedder.remove_document(card_id)
        embedder.add_document(yf)

        return KnowledgeCrudResponse(success=True, entry_id=card_id, message="方法卡片已更新")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新失败: {e}")


@knowledge_router.delete("/methods/{card_id}", response_model=KnowledgeCrudResponse)
async def delete_method(card_id: str, user: GitHubUser = Depends(require_contributor)):
    """删除方法卡片：移除 YAML 文件 + 从 ChromaDB 摘除。"""
    try:
        yf = _find_yaml_file("method", card_id)
        if not yf:
            raise HTTPException(status_code=404, detail=f"方法卡片 {card_id} 不存在")

        embedder = _get_embedder()
        embedder.remove_document(card_id)
        yf.unlink()
        # Clean up raw text if exists
        raw_path = yf.with_suffix(".raw.txt")
        if raw_path.exists():
            raw_path.unlink()

        return KnowledgeCrudResponse(success=True, entry_id=card_id, message="方法卡片已删除")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")


# ── CRUD: papers ──────────────────────────────────────────────────


@knowledge_router.post("/papers", response_model=KnowledgeCrudResponse)
async def create_paper(data: dict, user: GitHubUser = Depends(require_contributor)):
    """手动创建论文条目。"""
    try:
        entry_id = _next_id("paper")
        data["id"] = entry_id
        from ..knowledge.schemas import Paper
        validated = Paper(**data)

        yaml_str = yaml.dump(
            {"paper": validated.model_dump()},
            allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2,
        )
        settings = get_settings()
        comp = (data.get("competition") or "other")
        year = data.get("year", 2025)
        pid = data.get("problem_id", "X")
        safe_name = f"{year}{comp}{pid}"
        out_dir = settings.kb_root / "papers" / comp
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{safe_name}.yaml"
        out_path.write_text(yaml_str, encoding="utf-8")

        embedder = _get_embedder()
        embedder.add_document(out_path)

        return KnowledgeCrudResponse(success=True, entry_id=entry_id, message="论文已创建")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建失败: {e}")


@knowledge_router.put("/papers/{paper_id}", response_model=KnowledgeCrudResponse)
async def update_paper(paper_id: str, data: dict, user: GitHubUser = Depends(require_contributor)):
    """更新论文条目。"""
    try:
        yf = _find_yaml_file("paper", paper_id)
        if not yf:
            raise HTTPException(status_code=404, detail=f"论文 {paper_id} 不存在")

        data["id"] = paper_id
        from ..knowledge.schemas import Paper
        validated = Paper(**data)

        yaml_str = yaml.dump(
            {"paper": validated.model_dump()},
            allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2,
        )
        yf.write_text(yaml_str, encoding="utf-8")

        embedder = _get_embedder()
        embedder.remove_document(paper_id)
        embedder.add_document(yf)

        return KnowledgeCrudResponse(success=True, entry_id=paper_id, message="论文已更新")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新失败: {e}")


@knowledge_router.delete("/papers/{paper_id}", response_model=KnowledgeCrudResponse)
async def delete_paper(paper_id: str, user: GitHubUser = Depends(require_contributor)):
    """删除论文条目。"""
    try:
        yf = _find_yaml_file("paper", paper_id)
        if not yf:
            raise HTTPException(status_code=404, detail=f"论文 {paper_id} 不存在")

        embedder = _get_embedder()
        embedder.remove_document(paper_id)
        yf.unlink()
        raw_path = yf.with_suffix(".raw.txt")
        if raw_path.exists():
            raw_path.unlink()

        return KnowledgeCrudResponse(success=True, entry_id=paper_id, message="论文已删除")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")


# ── CRUD: templates ───────────────────────────────────────────────


@knowledge_router.post("/templates", response_model=KnowledgeCrudResponse)
async def create_template(data: dict, user: GitHubUser = Depends(require_contributor)):
    """手动创建分析框架模板。"""
    try:
        entry_id = _next_id("template")
        data["id"] = entry_id
        from ..knowledge.schemas import Template
        validated = Template(**data)

        yaml_str = yaml.dump(
            {"template": validated.model_dump()},
            allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2,
        )
        settings = get_settings()
        safe_name = (data.get("name") or entry_id).replace(" ", "_")
        out_dir = settings.kb_root / "templates"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{safe_name}.yaml"
        out_path.write_text(yaml_str, encoding="utf-8")

        embedder = _get_embedder()
        embedder.add_document(out_path)

        return KnowledgeCrudResponse(success=True, entry_id=entry_id, message="模板已创建")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建失败: {e}")


@knowledge_router.put("/templates/{tpl_id}", response_model=KnowledgeCrudResponse)
async def update_template(tpl_id: str, data: dict, user: GitHubUser = Depends(require_contributor)):
    """更新模板条目。"""
    try:
        yf = _find_yaml_file("template", tpl_id)
        if not yf:
            raise HTTPException(status_code=404, detail=f"模板 {tpl_id} 不存在")

        data["id"] = tpl_id
        from ..knowledge.schemas import Template
        validated = Template(**data)

        yaml_str = yaml.dump(
            {"template": validated.model_dump()},
            allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2,
        )
        yf.write_text(yaml_str, encoding="utf-8")

        embedder = _get_embedder()
        embedder.remove_document(tpl_id)
        embedder.add_document(yf)

        return KnowledgeCrudResponse(success=True, entry_id=tpl_id, message="模板已更新")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新失败: {e}")


@knowledge_router.delete("/templates/{tpl_id}", response_model=KnowledgeCrudResponse)
async def delete_template(tpl_id: str, user: GitHubUser = Depends(require_contributor)):
    """删除模板条目。"""
    try:
        yf = _find_yaml_file("template", tpl_id)
        if not yf:
            raise HTTPException(status_code=404, detail=f"模板 {tpl_id} 不存在")

        embedder = _get_embedder()
        embedder.remove_document(tpl_id)
        yf.unlink()
        raw_path = yf.with_suffix(".raw.txt")
        if raw_path.exists():
            raw_path.unlink()

        return KnowledgeCrudResponse(success=True, entry_id=tpl_id, message="模板已删除")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")


# ── CRUD: problems ───────────────────────────────────────────────


@knowledge_router.post("/problems", response_model=KnowledgeCrudResponse)
async def create_problem(data: dict, user: GitHubUser = Depends(require_contributor)):
    """手动创建竞赛题目。"""
    try:
        entry_id = _next_id("problem")
        data["id"] = entry_id
        from ..knowledge.schemas import Problem
        validated = Problem(**data)

        yaml_str = yaml.dump(
            {"problem": validated.model_dump()},
            allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2,
        )
        settings = get_settings()
        comp = (data.get("competition") or "other")
        year = data.get("year", 2025)
        pid = data.get("problem_id", "X")
        safe_name = f"{year}{pid}"
        out_dir = settings.kb_root / "problems" / comp
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{safe_name}.yaml"
        out_path.write_text(yaml_str, encoding="utf-8")

        embedder = _get_embedder()
        embedder.add_document(out_path)

        return KnowledgeCrudResponse(success=True, entry_id=entry_id, message="题目已创建")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建失败: {e}")


@knowledge_router.put("/problems/{problem_id}", response_model=KnowledgeCrudResponse)
async def update_problem(problem_id: str, data: dict, user: GitHubUser = Depends(require_contributor)):
    """更新竞赛题目。"""
    try:
        yf = _find_yaml_file("problem", problem_id)
        if not yf:
            raise HTTPException(status_code=404, detail=f"题目 {problem_id} 不存在")

        data["id"] = problem_id
        from ..knowledge.schemas import Problem
        validated = Problem(**data)

        yaml_str = yaml.dump(
            {"problem": validated.model_dump()},
            allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2,
        )
        yf.write_text(yaml_str, encoding="utf-8")

        embedder = _get_embedder()
        embedder.remove_document(problem_id)
        embedder.add_document(yf)

        return KnowledgeCrudResponse(success=True, entry_id=problem_id, message="题目已更新")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新失败: {e}")


@knowledge_router.delete("/problems/{problem_id}", response_model=KnowledgeCrudResponse)
async def delete_problem(problem_id: str, user: GitHubUser = Depends(require_contributor)):
    """删除竞赛题目。"""
    try:
        yf = _find_yaml_file("problem", problem_id)
        if not yf:
            raise HTTPException(status_code=404, detail=f"题目 {problem_id} 不存在")

        embedder = _get_embedder()
        embedder.remove_document(problem_id)
        yf.unlink()
        raw_path = yf.with_suffix(".raw.txt")
        if raw_path.exists():
            raw_path.unlink()

        return KnowledgeCrudResponse(success=True, entry_id=problem_id, message="题目已删除")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")

