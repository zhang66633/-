"""REST API 响应模型。"""

from typing import Any, List, Optional
from pydantic import BaseModel


class TaskArtifact(BaseModel):
    """任务文件区的一条文件记录。"""
    type: str  # "uploaded" | "figure" | "result"
    name: str
    url: str
    size: Optional[int] = None


class TaskResponse(BaseModel):
    """任务响应。"""
    task_id: str
    status: str  # "running" | "completed" | "error"
    problem: str
    mode: str
    final_response: Optional[str] = None
    writing_output: Optional[str] = None
    analysis_output: Optional[str] = None
    model_output: Optional[str] = None
    solving_output: Optional[str] = None
    verification_output: Optional[str] = None
    artifacts: list[TaskArtifact] = []


class MessageResponse(BaseModel):
    """单条消息响应。"""
    id: str
    msg_type: str
    content: Optional[str] = None
    agent_type: Optional[str] = None
    created_at: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应。"""
    status: str
    service: str
    version: str


class ApiKeyResponse(BaseModel):
    """API Key 响应。"""
    id: str
    name: str
    provider: str
    model_name: str = "deepseek-chat"
    masked_key: str
    is_default: bool = False
    base_url: str = ""
    purpose: str = "chat"
