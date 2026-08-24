"""Application configuration loaded from environment variables."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """Configuration for a single LLM instance."""

    provider: Literal["anthropic", "openai"] = "openai"
    model: str = "deepseek-v4-flash"
    api_key: str = ""
    base_url: str | None = None
    temperature: float = 0.3
    max_tokens: int = 8192


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- Server ----
    host: str = "127.0.0.1"  # 默认仅本机监听；如需局域网访问在 .env 显式改为 0.0.0.0
    port: int = 8000
    debug: bool = False

    # ---- LLM API Keys ----
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    # DEEPSEEK_API_KEY 作为 openai_api_key 的别名（云部署模板使用此名，见 .env.production.example）
    deepseek_api_key: str = ""

    # ---- Embedding（知识库向量索引）----
    # provider: openai_compatible（默认，任何 OpenAI 兼容 embedding 服务）| huggingface（本地模型）
    kb_embedding_provider: str = "openai_compatible"
    kb_embedding_model: str = "BAAI/bge-large-zh-v1.5"
    kb_embedding_base_url: str = "https://api.siliconflow.cn/v1"
    kb_embedding_api_key: str = ""

    # ---- LLM Models (per agent role) ----
    classifier_model: str = "deepseek-v4-flash"
    planner_model: str = "deepseek-v4-flash"
    analysis_model: str = "deepseek-v4-flash"
    modeling_model: str = "deepseek-v4-flash"
    solving_model: str = "deepseek-v4-flash"
    verification_model: str = "deepseek-v4-flash"
    writing_model: str = "deepseek-v4-flash"
    # 自由问答（纯对话，不走 LangGraph 流水线）
    chat_model: str = "deepseek-v4-flash"

    # ---- LLM Defaults ----
    default_temperature: float = 0.3
    default_max_tokens: int = 32768
    # DeepSeek V4 Pro 最大输出 393216 tokens (384K)，按实际 token 计费，拉满无额外成本。
    # 写作阶段需生成完整 LaTeX 论文（国赛~1万字 / 美赛25页，含公式+TikZ+表格开销）。
    writing_max_tokens: int = 393216
    # 求解阶段含代码+推导+图表说明，多轮tool loop每轮都可能产生大量输出。
    solving_max_tokens: int = 393216

    # 写作阶段并行生成章节的并发路数（竞赛演示加速：串行 15+ 次调用 → 并行）
    writing_parallelism: int = 3

    # ---- DeepSeek Proxy ----
    deepseek_base_url: str = "https://api.deepseek.com"

    # ---- Redis ----
    redis_url: str = "redis://localhost:6379/0"

    # ---- ChromaDB ----
    chroma_persist_dir: str = "./data/chroma_db"
    chroma_http_url: str = ""  # 独立容器模式: "http://localhost:8001" 或 "http://chromadb:8000"

    # ---- Knowledge Base ----
    kb_root_dir: str = "./knowledge_base"
    # 知识库导入提取时的视觉模型(可选)。不填: 图片/扫描 PDF 降级为纯文本路径;
    # 填写支持视觉的模型名(如 qwen-vl-plus、gpt-4o)后启用图片识别。
    # 该模型使用 .env 的 OPENAI_API_KEY / ANTHROPIC_API_KEY,不受「活动 API Key」记录覆盖。
    kb_vision_model: str = ""

    # ---- Sandbox ----
    sandbox_timeout: int = 60
    sandbox_max_memory_mb: int = 512
    # 默认 docker（硬隔离）；docker 不可用时自动回退 subprocess 并告警（见 sandbox/executor.py）
    sandbox_backend: str = "docker"  # "docker" | "subprocess"

    # ---- GitHub OAuth ----
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:5174/auth/callback"

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
        from app.core.llm.providers import classify_provider

        model_attr = f"{agent_role}_model"
        model = getattr(self, model_attr, self.analysis_model)

        # 供应商归类单一真源在 core/llm/providers.classify_provider；这里只做 key/base_url 解析
        provider = classify_provider(model)
        if provider == "anthropic":
            api_key = self.anthropic_api_key
            base_url: str | None = None
        else:
            # DEEPSEEK_API_KEY 优先（云部署模板），OPENAI_API_KEY 兜底
            api_key = self.deepseek_api_key or self.openai_api_key
            base_url = (
                getattr(self, "deepseek_base_url", "https://api.deepseek.com")
                if "deepseek" in model.lower()
                else None
            )

        # 按角色选择 max_tokens：写作/求解阶段需更长输出
        if agent_role == "writing":
            max_tokens = self.writing_max_tokens
        elif agent_role == "solving":
            max_tokens = self.solving_max_tokens
        else:
            max_tokens = self.default_max_tokens

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
