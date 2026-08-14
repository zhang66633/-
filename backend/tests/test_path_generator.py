"""学习路径数据/逻辑拆分不变量测试(god-files 拆分 #31 + 内容文件化)。

运行: 在 backend/ 目录下 `python -m pytest tests/test_path_generator.py -q`
      或直接 `python tests/test_path_generator.py`。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.learning.path_generator import generate_learning_path, get_unit_detail  # noqa: E402
from app.learning.unit_content import ALL_MODELER, ALL_UNITS, CONTENT_DIR  # noqa: E402


def test_all_roles_have_units():
    for role in ("modeler", "programmer", "writer"):
        assert len(ALL_UNITS[role]) > 0, f"{role} 角色应有学习单元"


def test_every_unit_has_content_file():
    # 每个单元都应有独立的 content/<role>/<unit_id>.md 内容文件
    for role, units in ALL_UNITS.items():
        for u in units:
            p = CONTENT_DIR / role / f"{u.unit_id}.md"
            assert p.exists(), f"{u.unit_id} 缺少内容文件 {p}"


def test_unit_content_rich():
    # 内容文件应足够丰富(≥1000 字符),不得是占位文本
    for role, units in ALL_UNITS.items():
        for u in units:
            p = CONTENT_DIR / role / f"{u.unit_id}.md"
            text = p.read_text(encoding="utf-8")
            assert len(text) >= 1000, f"{u.unit_id} 内容过于单薄({len(text)} 字符)"
            assert "内容正在编写中" not in text, f"{u.unit_id} 仍是占位内容"


def test_unit_content_backed():
    # 每个单元的 content_md 应从文件加载且非空
    for role_units in ALL_UNITS.values():
        for u in role_units:
            assert u.content_md and len(u.content_md) > 100, f"{u.unit_id} 内容为空"


def test_generate_and_lookup():
    p = generate_learning_path()
    assert len(p.phases) > 0
    total = sum(len(ph.units) for ph in p.phases)
    assert total >= len(ALL_MODELER) * 0.9, "默认路径应展示建模手绝大多数单元"
    u = get_unit_detail("modeler_lp_01")
    assert u is not None and u.title
    assert get_unit_detail("不存在的单元") is None


if __name__ == "__main__":
    test_all_roles_have_units()
    test_every_unit_has_content_file()
    test_unit_content_rich()
    test_unit_content_backed()
    test_generate_and_lookup()
    print("ALL TESTS PASSED")
