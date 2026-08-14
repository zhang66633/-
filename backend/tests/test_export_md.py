"""DOCX 导出 markdown 行内解析测试（审计发现 #32 后半）。

运行: 在 backend/ 目录下 `python -m pytest tests/test_export_md.py -q`
      或直接 `python tests/test_export_md.py`。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api.export_routes import (  # noqa: E402
    _parse_inline,
    _is_table_separator,
)


def test_inline_bold_italic_strike():
    assert _parse_inline("**加粗** 和 *斜体* 和 ~~删除~~") == "加粗 和 斜体 和 删除"
    assert _parse_inline("__下划线加粗__") == "下划线加粗"


def test_inline_code_and_escapes():
    assert _parse_inline("用 `np.array()` 计算") == "用 np.array() 计算"
    assert _parse_inline(r"\*不是斜体\*") == "*不是斜体*"


def test_inline_links_and_images():
    assert _parse_inline("[文档](https://a.b/c)") == "文档（https://a.b/c）"
    assert _parse_inline("![图](x.png)") == "图（图片: x.png）"


def test_inline_math():
    assert _parse_inline("$x^2$ 与 $$y=ax+b$$") == "[x^2] 与 [公式: y=ax+b]"


def test_table_separator():
    assert _is_table_separator("| --- | --- |")
    assert _is_table_separator("|:--|--:|")
    assert not _is_table_separator("| 数据 | 值 |")


if __name__ == "__main__":
    test_inline_bold_italic_strike()
    test_inline_code_and_escapes()
    test_inline_links_and_images()
    test_inline_math()
    test_table_separator()
    print("ALL TESTS PASSED")
