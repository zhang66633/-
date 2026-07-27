"""LLM provider abstraction layer.

Each provider encapsulates model instantiation logic for a specific
API backend (DeepSeek, Anthropic, OpenAI).  The LLMFactory in
`app.core.llm.factory` delegates to these providers.
"""

from __future__ import annotations

from typing import Optional

from langchain_core.language_models import BaseChatModel


class BaseProvider:
    """Abstract base for LLM providers."""

    def create(
        self,
        model: str,
        api_key: str,
        temperature: float = 0.3,
        max_tokens: int = 8192,
        base_url: Optional[str] = None,
    ) -> BaseChatModel:
        raise NotImplementedError


class OpenaiCompatibleProvider(BaseProvider):
    """Provider for OpenAI-compatible APIs (DeepSeek, open-source models, etc.)."""

    def __init__(self, default_base_url: str | None = None):
        self.default_base_url = default_base_url

    def create(
        self,
        model: str,
        api_key: str,
        temperature: float = 0.3,
        max_tokens: int = 8192,
        base_url: Optional[str] = None,
    ) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        # DeepSeek 推理模型 (reasoner) 要求 temperature=0
        is_reasoner = "reasoner" in model.lower() or "r1" in model.lower()
        effective_temp = 0.0 if is_reasoner else temperature

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url or self.default_base_url,
            temperature=effective_temp,
            max_tokens=max_tokens,
            request_timeout=300,
            max_retries=2,
        )


class DeepSeekProvider(OpenaiCompatibleProvider):
    """DeepSeek API provider (OpenAI-compatible)."""

    def __init__(self):
        super().__init__(default_base_url="https://api.deepseek.com")


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider."""

    def create(
        self,
        model: str,
        api_key: str,
        temperature: float = 0.3,
        max_tokens: int = 8192,
        base_url: Optional[str] = None,
    ) -> BaseChatModel:
        from langchain_anthropic import ChatAnthropic

        kwargs = {
            "model": model,
            "api_key": api_key,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "request_timeout": 300,
            "max_retries": 2,
        }
        if base_url:
            kwargs["base_url"] = base_url

        return ChatAnthropic(**kwargs)


# ── provider resolver ──────────────────────────────────────────────

def get_provider(model: str) -> BaseProvider:
    """Return the appropriate provider for a given model name."""
    if "deepseek" in model.lower():
        return DeepSeekProvider()
    if "claude" in model.lower():
        return AnthropicProvider()
    return OpenaiCompatibleProvider()
