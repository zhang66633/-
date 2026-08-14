"""选择题题库与练习记录不变量测试。

运行: 在 backend/ 目录下 `python -m pytest tests/test_quiz_bank.py -q`
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.learning.quiz_bank import (  # noqa: E402
    categories_summary, get_by_unit, get_question, list_questions, public_view,
    total_count,
)
from app.services.practice_store import PracticeStore  # noqa: E402


def test_quiz_bank_nonempty():
    assert total_count() >= 60, "题库应包含 60+ 道选择题(每单元 3 题)"


def test_quiz_bank_schema_valid():
    for q in list_questions():
        assert len(q["options"]) == 4, f"{q['id']} 选项数必须为 4"
        assert 0 <= q["answer_index"] < 4, f"{q['id']} 答案下标越界"
        assert q["question"].strip(), f"{q['id']} 题干为空"
        assert q["explanation"].strip(), f"{q['id']} 解析为空"
        assert q["role"] in ("modeler", "programmer", "writer")
        assert q["difficulty"] in ("beginner", "intermediate", "advanced")


def test_public_view_hides_answer():
    for q in list_questions()[:20]:
        view = public_view(q)
        assert "answer_index" not in view, f"{q['id']} 泄露答案"
        assert "explanation" not in view, f"{q['id']} 泄露解析"
        assert view["options"] == q["options"]


def test_filters():
    modeler_only = list_questions(role="modeler")
    assert modeler_only and all(q["role"] == "modeler" for q in modeler_only)
    beginner_only = list_questions(difficulty="beginner")
    assert beginner_only and all(q["difficulty"] == "beginner" for q in beginner_only)
    # 每类至少覆盖一个单元的题目
    assert list_questions(category="优化"), "优化类应有题目"
    assert list_questions(category="评价"), "评价类应有题目"


def test_every_unit_has_questions():
    # 每个学习单元都应有自测题(一库两用: 单元页自测)
    from app.learning.unit_content import ALL_UNITS

    for role, units in ALL_UNITS.items():
        for u in units:
            qs = get_by_unit(u.unit_id)
            assert len(qs) >= 1, f"{u.unit_id} 缺少选择题"


def test_categories_summary():
    summary = categories_summary()
    assert summary, "分类统计不应为空"
    total = sum(c["count"] for c in summary)
    assert total == total_count(), "分类统计总数应与题库总数一致"


def test_practice_store_mistake_flow(tmp_path):
    """错题生命周期: 答错入错题本 → 答对自动掌握。"""
    store = PracticeStore(db_path=tmp_path / "practice.db")

    # 未作答
    assert store.get_wrong_question_ids() == set()
    assert store.get_tried_ids() == set()

    # 答错 → 入错题本
    store.record_answer("q1", 0, False)
    assert store.get_wrong_question_ids() == {"q1"}
    assert store.get_wrong_counts() == {"q1": 1}
    assert store.get_tried_ids() == {"q1"}

    # 再错一次 → 错误次数累加
    store.record_answer("q1", 2, False)
    assert store.get_wrong_counts()["q1"] == 2

    # 答对 → 自动移出错题本(最新状态推导)
    store.record_answer("q1", 1, True)
    assert store.get_wrong_question_ids() == set()
    assert store.get_tried_ids() == {"q1"}

    # 统计
    stats = store.get_stats()
    assert stats["total_answers"] == 3
    assert stats["correct_answers"] == 1
    assert stats["wrong_questions"] == 0
    assert stats["mastered_questions"] == 1


def test_get_question():
    q = get_question("modeler_lp_01_q1")
    assert q is not None and q["unit_id"] == "modeler_lp_01"
    assert get_question("不存在的题") is None


if __name__ == "__main__":
    test_quiz_bank_nonempty()
    test_quiz_bank_schema_valid()
    test_public_view_hides_answer()
    test_filters()
    test_every_unit_has_questions()
    test_categories_summary()
    print("ALL TESTS PASSED")
