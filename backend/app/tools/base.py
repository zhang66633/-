"""工具基类工厂 — 借鉴 cc-haha 的 buildTool + TOOL_DEFAULTS 模式。

为所有工具提供统一的安全默认值、结果截断、并发安全标记。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, ClassVar, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ── 工具安全默认值 ──────────────────────────────────────────────────
# 借鉴 cc-haha TOOL_DEFAULTS: 安全第一，fail-closed。

TOOL_DEFAULTS: dict[str, Any] = {
    "is_concurrency_safe": False,   # 默认不可并发（有副作用）
    "is_read_only": False,          # 默认可能有修改
    "is_destructive": False,        # 默认非破坏性
    "max_result_chars": 3000,       # 工具结果超过此值则截断 + 写磁盘
    "result_persist_dir": None,     # 结果持久化目录（运行时设置）
}


class BuiltTool(BaseTool):
    """带安全默认值的工具基类。

    新增属性（借鉴 cc-haha Tool 接口）：
    - is_concurrency_safe: 是否可并发执行（默认 False）
    - is_read_only: 是否只读操作（默认 False）
    - is_destructive: 是否破坏性操作（默认 False）
    - max_result_chars: 单次结果最大字符数（超限则截断+写磁盘）
    - result_persist_dir: 完整结果持久化目录
    """

    is_concurrency_safe: bool = False
    is_read_only: bool = False
    is_destructive: bool = False
    max_result_chars: int = 3000
    result_persist_dir: Optional[Path] = None

    def _truncate_result(self, result_text: str, tool_name: str | None = None) -> str:
        """截断超长结果，将完整内容写入磁盘。"""
        if len(result_text) <= self.max_result_chars:
            return result_text

        name = tool_name or self.name
        persist_dir = self.result_persist_dir
        if persist_dir is None:
            # 默认写入临时目录
            import tempfile
            persist_dir = Path(tempfile.gettempdir()) / "tool_results"
        persist_dir.mkdir(parents=True, exist_ok=True)

        import uuid
        persist_path = persist_dir / f"_tool_{name}_{uuid.uuid4().hex[:8]}.txt"
        try:
            persist_path.write_text(result_text, encoding="utf-8")
            logger.info("工具 %s 结果超长 (%d chars)，完整结果已保存至 %s",
                        name, len(result_text), persist_path)
        except Exception as e:
            logger.warning("工具结果持久化失败: %s", e)

        truncated = result_text[:self.max_result_chars]
        return (
            f"{truncated}\n\n…（结果已截断，共 {len(result_text)} 字符。"
            f"完整结果已保存至 {persist_path}）"
        )


def build_tool(
    tool_cls: Type[BaseTool],
    **overrides,
) -> Type[BaseTool]:
    """工厂函数：为工具类注入安全默认值。

    借鉴 cc-haha buildTool: 展开 TOOL_DEFAULTS 到类定义，再覆盖用户指定的值。

    用法:
        MyTool = build_tool(MyToolDef, is_read_only=True, max_result_chars=5000)
        tool_instance = MyTool()

    Args:
        tool_cls: 原始工具类（应继承 BaseTool）
        **overrides: 覆盖默认值的键值对

    Returns:
        注入了默认值的工具类（原地修改 + 返回）
    """
    for key, default_val in TOOL_DEFAULTS.items():
        if not hasattr(tool_cls, key):
            setattr(tool_cls, key, default_val)

    for key, val in overrides.items():
        if key in TOOL_DEFAULTS:
            setattr(tool_cls, key, val)
        else:
            logger.warning("build_tool: 未知覆盖项 %s=%s（不在 TOOL_DEFAULTS 中）", key, val)

    return tool_cls


def create_tool_defaults(**overrides) -> dict[str, Any]:
    """创建一组带自定义覆盖的默认值，用于批量创建工具。

    用法:
        defaults = create_tool_defaults(
            result_persist_dir=Path("/tmp/results"),
            max_result_chars=5000,
        )
        ToolA = build_tool(ToolADef, **defaults)
        ToolB = build_tool(ToolBDef, **defaults)
    """
    merged = {**TOOL_DEFAULTS, **overrides}
    return merged