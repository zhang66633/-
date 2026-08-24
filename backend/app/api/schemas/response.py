"""REST API 响应模型。"""

from pydantic import BaseModel


class TaskArtifact(BaseModel):
    """任务文件区的一条文件记录。"""

    type: str  # "uploaded" | "figure" | "result"
    name: str
    url: str
    size: int | None = None


class TaskResponse(BaseModel):
    """任务响应。"""

    task_id: str
    status: str  # "running" | "completed" | "error"
    problem: str
    mode: str
    final_response: str | None = None
    writing_output: str | None = None
    analysis_output: str | None = None
    model_output: str | None = None
    solving_output: str | None = None
    verification_output: str | None = None
    artifacts: list[TaskArtifact] = []


class MessageResponse(BaseModel):
    """单条消息响应。"""

    id: str
    msg_type: str
    content: str | None = None
    agent_type: str | None = None
    created_at: str | None = None


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
    model_name: str = "deepseek-v4-flash"
    masked_key: str
    is_default: bool = False
    base_url: str = ""
    purpose: str = "chat"
