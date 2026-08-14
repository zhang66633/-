"""LLMFactory — 按 agent 角色创建不同的 LLM 实例。

Uses the provider abstraction layer for clean separation of
API-specific instantiation logic.
"""

from langchain_core.language_models import BaseChatModel

from app.config import get_settings

from .providers import get_provider


def get_active_api_key() -> dict | None:
    """获取当前活动的 API Key（优先默认 key，否则返回第一个）。"""
    try:
        from app.api.apikeys import get_active_api_key as _get_key

        return _get_key()
    except Exception:
        return None


class LLMFactory:
    """为每个 agent 角色创建独立配置的 LLM 实例。"""

    @staticmethod
    def create(agent_role: str, api_key_config: dict | None = None) -> BaseChatModel:
        settings = get_settings()

        llm_config = settings.get_llm_config(agent_role)

        active_key = api_key_config or get_active_api_key()

        if active_key:
            key = active_key.get("key", "")
            if key:  # 不覆盖为空字符串的 key（防止 apikeys 空条目覆盖 .env 有效 key）
                llm_config.api_key = key
            llm_config.model = active_key.get("model_name", llm_config.model)
            llm_config.provider = active_key.get("provider", llm_config.provider)
            # 优先使用 Key 记录里的 base_url（支持任意 OpenAI 兼容服务商）
            key_base_url = active_key.get("base_url")
            if key_base_url:
                llm_config.base_url = key_base_url
            elif active_key.get("provider") == "deepseek":
                llm_config.base_url = getattr(
                    settings, "deepseek_base_url", "https://api.deepseek.com"
                )

        provider = get_provider(llm_config.model)
        return provider.create(
            model=llm_config.model,
            api_key=llm_config.api_key,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens,
            base_url=llm_config.base_url,
        )


def get_llm(agent_role: str, api_key_config: dict | None = None) -> BaseChatModel:
    """快捷获取 LLM 实例。"""
    return LLMFactory.create(agent_role, api_key_config)
