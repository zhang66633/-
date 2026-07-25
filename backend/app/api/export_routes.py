"""导出接口 — Markdown → DOCX。"""

import io
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

export_router = APIRouter()


class ExportDocxRequest(BaseModel):
    markdown: str
    title: str = "对话记录"


@export_router.post("/export/docx")
async def export_docx(req: ExportDocxRequest):
    """将 Markdown 文本转为 .docx 文件下载。"""
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        raise HTTPException(status_code=500, detail="python-docx 未安装")

    doc = Document()

    # 标题
    heading = doc.add_heading(req.title, level=0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 简易 Markdown → docx 逐行解析
    lines = req.markdown.split("\n")
    i = 0
    in_code_block = False
    code_lines: list[str] = []

    while i < len(lines):
        line = lines[i]

        # 代码块
        if line.strip().startswith("```"):
            if in_code_block:
                # 结束代码块
                code_text = "\n".join(code_lines)
                p = doc.add_paragraph()
                run = p.add_run(code_text)
                run.font.name = "Consolas"
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # 标题
        if line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
        elif line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
        # 分隔线
        elif line.strip() in ("---", "***", "___"):
            doc.add_paragraph("─" * 40)
        # 引用
        elif line.startswith("> "):
            p = doc.add_paragraph(line[2:].strip())
            p.paragraph_format.left_indent = Pt(24)
            for run in p.runs:
                run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
        # 空行
        elif not line.strip():
            pass
        # 普通段落（去除 Markdown 格式标记）
        else:
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
            text = re.sub(r"\*(.+?)\*", r"\1", text)
            text = re.sub(r"`(.+?)`", r"\1", text)
            text = re.sub(r"\$(.+?)\$", r"[\1]", text)  # 公式占位
            doc.add_paragraph(text)

        i += 1

    # 输出为流
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    filename = f"{req.title}.docx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
