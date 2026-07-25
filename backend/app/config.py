"""Application configuration loaded from environment variables."""

from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """Configuration for a single LLM instance."""

    provider: Literal["anthropic", "openai"] = "openai"
    model: str = "deepseek-chat"
    api_key: str = ""
    base_url: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 8192


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- Server ----
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # ---- LLM API Keys ----
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # ---- Embedding（知识库向量索引）----
    # provider: openai_compatible（默认，任何 OpenAI 兼容 embedding 服务）| huggingface（本地模型）
    kb_embedding_provider: str = "openai_compatible"
    kb_embedding_model: str = "BAAI/bge-large-zh-v1.5"
    kb_embedding_base_url: str = "https://api.siliconflow.cn/v1"
    kb_embedding_api_key: str = ""

    # ---- LLM Models (per agent role) ----
    classifier_model: str = "deepseek-chat"
    planner_model: str = "deepseek-chat"
    analysis_model: str = "deepseek-chat"
    modeling_model: str = "deepseek-chat"
    solving_model: str = "deepseek-chat"
    verification_model: str = "deepseek-chat"
    writing_model: str = "deepseek-chat"
    # 自由问答（纯对话，不走 LangGraph 流水线）
    chat_model: str = "deepseek-chat"

    # ---- LLM Defaults ----
    default_temperature: float = 0.3
    default_max_tokens: int = 16384
    # 写作阶段需生成完整 LaTeX 论文（国赛~1万字 / 美赛25页，含公式+TikZ+表格开销，
    # 实际约 2-4 万 tokens）。DeepSeek V4 Pro 最大输出 393216，给足余量避免截断。
    writing_max_tokens: int = 65536

    # ---- DeepSeek Proxy ----
    deepseek_base_url: str = "https://api.deepseek.com"

    # ---- Redis ----
    redis_url: str = "redis://localhost:6379/0"

    # ---- ChromaDB ----
    chroma_persist_dir: str = "./data/chroma_db"

    # ---- Knowledge Base ----
    kb_root_dir: str = "./knowledge_base"

    # ---- Sandbox ----
    sandbox_timeout: int = 60
    sandbox_max_memory_mb: int = 512

    # ---- GitHub OAuth ----
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:5173/auth/callback"

    # ---- JWT ----
    jwt_secret: str = "set-in-env-file"

    # ---- Project Root ----
    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent

    @property
    def kb_root(self) -> Path:
        return self.project_root / self.kb_root_dir

    @property
    def chroma_dir(self) -> Path:
        return self.project_root / self.chroma_persist_dir

    def get_llm_config(self, agent_role: str) -> LLMConfig:
        """Get LLM configuration for a specific agent role."""
        model_attr = f"{agent_role}_model"
        model = getattr(self, model_attr, self.analysis_model)

        provider: Literal["anthropic", "openai"] = "openai"
        api_key = self.openai_api_key
        base_url: Optional[str] = None

        if "claude" in model.lower():
            provider = "anthropic"
            api_key = self.anthropic_api_key
        elif "deepseek" in model.lower():
            provider = "openai"
            api_key = self.openai_api_key
            base_url = getattr(self, "deepseek_base_url", "https://api.deepseek.com")
        elif "gpt" in model.lower() or "o1" in model.lower() or "o3" in model.lower():
            provider = "openai"
            api_key = self.openai_api_key

        # 按角色选择 max_tokens：写作阶段需更长输出
        max_tokens = self.writing_max_tokens if agent_role == "writing" else self.default_max_tokens

        return LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=self.default_temperature,
            max_tokens=max_tokens,
        )


settings = Settings()


def get_settings() -> Settings:
    return settings
