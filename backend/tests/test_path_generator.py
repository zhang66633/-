"""学习路径数据/逻辑拆分不变量测试（god-files 拆分 #31）。

运行: 在 backend/ 目录下 `python -m pytest tests/test_path_generator.py -q`
      或直接 `python tests/test_path_generator.py`。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.learning.unit_content import ALL_UNITS, ALL_MODELER, CONTENT_LIBRARY  # noqa: E402
from app.learning.path_generator import generate_learning_path, get_unit_detail  # noqa: E402


def test_content_library_nonempty():
    assert len(CONTENT_LIBRARY) >= 55, "学习单元内容库应包含 55+ 条真实内容"


def test_all_roles_have_units():
    for role in ("modeler", "programmer", "writer"):
        assert len(ALL_UNITS[role]) > 0, f"{role} 角色应有学习单元"


def test_unit_content_backed():
    # 每个单元都应能从 CONTENT_LIBRARY 取到内容或回退占位（_u 的 content_md 非空）
    for role_units in ALL_UNITS.values():
        for u in role_units:
            assert u.content_md and len(u.content_md) > 10, f"{u.unit_id} 内容为空"


def test_generate_and_lookup():
    p = generate_learning_path()
    assert len(p.phases) > 0
    total = sum(len(ph.units) for ph in p.phases)
    assert total >= len(ALL_MODELER) * 0.9, "默认路径应展示建模手绝大多数单元"
    u = get_unit_detail("modeler_lp_01")
    assert u is not None and u.title
    assert get_unit_detail("不存在的单元") is None


if __name__ == "__main__":
    test_content_library_nonempty()
    test_all_roles_have_units()
    test_unit_content_backed()
    test_generate_and_lookup()
    print("ALL TESTS PASSED")
