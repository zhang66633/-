"""沙箱图片去重单测 — 用户手动 savefig 与自动保存重复时只留一张。"""

from __future__ import annotations

from app.sandbox.executor import _dedupe_image_paths


def _write_png(path, content: bytes):
    path.write_bytes(content)


def test_dedupe_identical_content_keeps_manual_name(tmp_path):
    """内容相同的两张图（手动命名 + figure_N 自动保存）→ 只留手动命名。"""
    manual = tmp_path / "tornado_chart.png"
    auto = tmp_path / "figure_1.png"
    _write_png(manual, b"same-png-bytes")
    _write_png(auto, b"same-png-bytes")

    result = _dedupe_image_paths(sorted(tmp_path.glob("*.png")))
    assert [p.name for p in result] == ["tornado_chart.png"]


def test_dedupe_keeps_distinct_images(tmp_path):
    """内容不同 → 全部保留。"""
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    _write_png(a, b"bytes-aaa")
    _write_png(b, b"bytes-bbb")

    result = _dedupe_image_paths(sorted(tmp_path.glob("*.png")))
    assert len(result) == 2


def test_dedupe_single_image_noop(tmp_path):
    """单图无副作用。"""
    a = tmp_path / "only.png"
    _write_png(a, b"x")
    result = _dedupe_image_paths([a])
    assert result == [a]


def test_dedupe_multiple_duplicates(tmp_path):
    """多张重复：手动文件优先登记，自动副本全丢弃。"""
    m1 = tmp_path / "chart1.png"
    m2 = tmp_path / "chart2.png"
    f1 = tmp_path / "figure_1.png"
    f2 = tmp_path / "figure_2.png"
    _write_png(m1, b"content-1")
    _write_png(m2, b"content-2")
    _write_png(f1, b"content-1")
    _write_png(f2, b"content-2")

    result = _dedupe_image_paths(sorted(tmp_path.glob("*.png")))
    names = {p.name for p in result}
    assert names == {"chart1.png", "chart2.png"}
