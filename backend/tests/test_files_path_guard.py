"""路径守卫与 containment 修复的表征测试（审计发现 #1）。

运行: 在 backend/ 目录下 `python -m pytest tests/test_files_path_guard.py -q`
      或直接 `python tests/test_files_path_guard.py`（无 pytest 时）。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import HTTPException  # noqa: E402

from app.api.files import _validate_path_segment  # noqa: E402


def test_dot_and_dotdot_rejected():
    for bad in ("..", ".", "...", "....."):
        try:
            _validate_path_segment(bad, "task_id")
        except HTTPException:
            continue
        raise AssertionError(f"路径段 {bad!r} 应被拒绝")


def test_normal_segments_accepted():
    assert _validate_path_segment("abc123", "x") == "abc123"
    assert _validate_path_segment("figure_1.png", "x") == "figure_1.png"
    assert _validate_path_segment("a.b-c_d", "x") == "a.b-c_d"


def test_slash_and_percent_rejected():
    for bad in ("a/b", "..%2F..", "a\\b"):
        try:
            _validate_path_segment(bad, "x")
        except HTTPException:
            continue
        raise AssertionError(f"路径段 {bad!r} 应被拒绝")


if __name__ == "__main__":
    test_dot_and_dotdot_rejected()
    test_normal_segments_accepted()
    test_slash_and_percent_rejected()
    print("ALL TESTS PASSED")
