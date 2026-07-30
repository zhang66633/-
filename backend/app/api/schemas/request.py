"""REST API 请求模型。"""

from typing import Literal, Optional
from pydantic import BaseModel


class ChatFileRef(BaseModel):
    """附件引用（已上传到 /files/upload 的文件）。"""
    file_id: str
    filename: str


class CreateTaskRequest(BaseModel):
    """创建建模任务请求。"""
    problem: str
    mode: Literal["teach", "execute"] = "execute"
    # 附件引用（已上传到 /files/upload 的文件），内容会被提取进问题上下文
    files: list[ChatFileRef] = []


class CancelTaskRequest(BaseModel):
    """取消任务请求。"""
    task_id: str


# ── Chat (自由问答) ─────────────────────────────────────────────

class ChatMessage(BaseModel):
    """单条对话消息。"""
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    """自由问答请求。无状态：前端携带完整历史，后端滑动窗口截断。"""
    messages: list[ChatMessage]
    use_rag: bool = False  # 预留：后续挂知识库检索
    # 对话模式：chat=自由问答（直接给结论），teach=教学模式（苏格拉底式引导），learning=学习中心（单元感知）
    mode: Literal["chat", "teach", "learning"] = "chat"
    # 本轮附带的文件（已上传），LLM 可在 run_code 中引用
    files: list[ChatFileRef] = []
    # 学习模式专用：当前学习单元的上下文信息
    unit_context: dict | None = None


class ApiKeyCreate(BaseModel):
    """添加 API Key 请求。"""
    name: str
    key: str
    provider: str = "deepseek"
    model_name: str = "deepseek-chat"
    base_url: str = ""           # 留空则按 provider 预设推断
    purpose: str = "chat"        # chat=对话/流水线 | embedding=知识库向量


class ApiKeyQuickCreate(BaseModel):
    """快速添加 API Key — 粘贴 key，按 provider 预设自动补全。"""
    key: str
    name: str = ""
    provider: str = "deepseek"
    model_name: str = ""
    base_url: str = ""
    purpose: str = "chat"


class FileUploadRequest(BaseModel):
    """文件上传请求。"""
    filename: Optional[str] = None


# ── Knowledge Base ──────────────────────────────────────────────

class KnowledgeUploadRequest(BaseModel):
    """知识上传 + LLM 提取请求。"""
    text: str
    kb_type: Literal["method", "paper", "template"]
    name: str = ""


class KnowledgeCreateRequest(BaseModel):
    """手动创建知识条目请求。"""
    kb_type: Literal["method", "paper", "template"]
    data: dict  # 根据 type 不同，字段不同


class KnowledgeUpdateRequest(BaseModel):
    """更新知识条目请求。"""
    kb_type: Literal["method", "paper", "template"]
    data: dict
