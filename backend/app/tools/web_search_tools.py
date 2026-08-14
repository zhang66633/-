"""Web 搜索工具 — 使用 DuckDuckGo 免费搜索。

供 chat/teach agent 在需要最新信息、真实案例、论文引用时调用。
无需 API Key，直接通过 duckduckgo-search 包查询。
"""

from __future__ import annotations

import logging
from typing import ClassVar

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WebSearchInput(BaseModel):
    query: str = Field(
        description=(
            "搜索关键词。尽量具体，如'粒子群算法 数学建模 应用案例'、"
            "'2024 美赛 O 题 优秀论文'、'Python 时间序列预测 ARIMA 教程'。"
            "中英文均可。"
        )
    )
    max_results: int = Field(
        default=5,
        description="返回结果数量（1-10），默认 5。",
        ge=1,
        le=10,
    )


class WebSearchTool(BaseTool):
    """搜索互联网获取最新信息、案例、论文和教程。"""

    name: ClassVar[str] = "web_search"
    description: ClassVar[str] = (
        "搜索互联网获取最新信息。适用场景：\n"
        "- 查找数学建模竞赛真题、优秀论文、获奖作品\n"
        "- 查找算法/方法的最新应用案例和教程\n"
        "- 查找特定数据集、开源工具、Python 库用法\n"
        "- 验证某个方法或公式的正确性\n"
        "返回标题、摘要和链接。注意：搜索结果可能包含过时或不准确信息，需甄别。"
    )
    args_schema: type[BaseModel] = WebSearchInput

    def _run(
        self,
        query: str,
        max_results: int = 5,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return "错误: duckduckgo-search 未安装。请运行 `pip install duckduckgo-search`"

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return f"搜索 '{query}' 未找到结果。请尝试更换关键词。"

            parts = [f"搜索 '{query}' 找到 {len(results)} 条结果：\n"]
            for i, r in enumerate(results, 1):
                title = r.get("title", "无标题")
                body = r.get("body", "无摘要")
                href = r.get("href", "")
                parts.append(f"{i}. **{title}**\n   {body}\n   链接: {href}")

            return "\n\n".join(parts)

        except Exception as e:  # noqa: BLE001
            logger.exception("web_search failed")
            return f"搜索失败: {type(e).__name__}: {e}"


def create_web_search_tools() -> list:
    """创建 Web 搜索工具列表。"""
    return [WebSearchTool()]
