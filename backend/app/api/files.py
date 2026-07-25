"""文件上传/下载 + 图片服务。"""

import re
import shutil
import tempfile
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from ..config import get_settings

files_router = APIRouter()

# 路径参数只允许字母、数字、点、下划线、短横线
_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9._-]+$")


def _validate_path_segment(value: str, label: str) -> str:
    """校验路径片段合法性，防止路径穿越。"""
    if not _SAFE_NAME_RE.match(value):
        raise HTTPException(status_code=400, detail=f"非法{label}: {value}")
    return value


# ── File upload / download ───────────────────────────────────────

def _get_uploads_dir() -> Path:
    settings = get_settings()
    uploads = settings.project_root / "data" / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    return uploads


@files_router.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件到 data/uploads/ 目录。"""
    uploads_dir = _get_uploads_dir()
    file_id = str(uuid.uuid4())[:8]
    # Keep original extension
    suffix = Path(file.filename or "upload").suffix
    stored_name = f"{file_id}{suffix}"
    stored_path = uploads_dir / stored_name

    try:
        with stored_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")

    return {
        "file_id": file_id,
        "filename": file.filename,
        "stored_name": stored_name,
        "size": stored_path.stat().st_size,
        "url": f"/api/files/{file_id}",
    }


@files_router.get("/files/{file_id}")
async def download_file(file_id: str):
    """下载已上传的文件。"""
    _validate_path_segment(file_id, "file_id")
    uploads_dir = _get_uploads_dir()
    # Find the file with this id regardless of extension
    matches = list(uploads_dir.glob(f"{file_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="文件不存在")
    stored_path = matches[0]
    return FileResponse(str(stored_path), media_type="application/octet-stream", filename=stored_path.name)


# ── Image serving ─────────────────────────────────────────────────


@files_router.get("/images/{run_id}/{filename}")
async def get_image(run_id: str, filename: str):
    """获取求解 Agent 生成的图表。"""
    _validate_path_segment(run_id, "run_id")
    _validate_path_segment(filename, "filename")
    img_dir = Path(tempfile.gettempdir()) / "mathmodel_outputs" / run_id
    img_path = (img_dir / filename).resolve()
    # 二次确认：resolve 后必须仍在 img_dir 内
    if not str(img_path).startswith(str(img_dir.resolve())):
        raise HTTPException(status_code=400, detail="非法路径")
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    return FileResponse(str(img_path), media_type="image/png")

