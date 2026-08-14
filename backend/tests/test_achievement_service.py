"""成就服务测试(阶段 2): 进度/目标/解锁/持久化/未读。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.services.achievement_service as ach_mod  # noqa: E402
import app.services.learning_store as ls_mod  # noqa: E402
import app.services.practice_store as ps_mod  # noqa: E402
from app.services.achievement_service import (  # noqa: E402
    ACHIEVEMENT_DEFS, get_achievement_service,
)
from app.services.learning_store import LearningStore  # noqa: E402
from app.services.practice_store import PracticeStore  # noqa: E402


def _use_tmp_stores(tmp_path: Path) -> tuple[LearningStore, PracticeStore]:
    ls = LearningStore(db_path=tmp_path / "learning.db")
    ps = PracticeStore(db_path=tmp_path / "practice.db")
    ls_mod._store = ls
    ps_mod._store = ps
    return ls, ps


def _fresh_service() -> ach_mod.AchievementService:
    ach_mod._service = None
    return get_achievement_service()


def test_empty_state(tmp_path):
    _use_tmp_stores(tmp_path)
    svc = _fresh_service()
    results = svc.check_all("default")
    assert len(results) == len(ACHIEVEMENT_DEFS) == 12
    for r in results:
        assert r["unlocked"] is False
        assert r["progress"] == 0
        assert r["target"] > 0
        assert r["is_new"] is False
    tiers = {r["tier"] for r in results}
    assert tiers == {"bronze", "silver", "gold"}


def test_progress_and_unlock(tmp_path):
    ls, ps = _use_tmp_stores(tmp_path)
    svc = _fresh_service()

    # 5 次作答(3 对 2 错)+ 完成 1 个单元
    for i, ok in enumerate([True, False, True, True, False]):
        ps.record_answer(f"modeler_lp_01_q{i % 3 + 1}", 0, ok, round_id="r1")
    ls.add_event("modeler_lp_01", "learn", 1.0)

    results = {r["id"]: r for r in svc.check_all("default")}
    assert results["first_practice"]["unlocked"] is True
    assert results["first_unit"]["unlocked"] is True
    assert results["quiz_10"]["progress"] == 5
    assert results["quiz_10"]["unlocked"] is False
    assert results["categories_5"]["progress"] >= 1

    # 新解锁的成就 is_new=True
    new_ones = [r["id"] for r in svc.check_all("default") if r["is_new"]]
    assert set(new_ones) == {"first_practice", "first_unit"}

    # ack 后不再 new
    svc.ack_all("default")
    results2 = {r["id"]: r for r in svc.check_all("default")}
    assert results2["first_practice"]["is_new"] is False


def test_persistence_across_restart(tmp_path):
    ls, ps = _use_tmp_stores(tmp_path)
    svc = _fresh_service()
    for i in range(10):
        ps.record_answer(f"q{i}", 0, True, round_id="r2")
    svc.check_all("default")  # 触发解锁持久化
    assert "quiz_10" in ls.unlocked_ids("default")

    # 模拟重启: 新 store 实例 + 新服务实例
    ls_mod._store = None
    ps_mod._store = None
    _use_tmp_stores(tmp_path)
    svc2 = _fresh_service()
    results = {r["id"]: r for r in svc2.check_all("default")}
    assert results["quiz_10"]["unlocked"] is True
    assert results["quiz_10"]["unlocked_at"] is not None


def test_streak_from_dates(tmp_path):
    ls, ps = _use_tmp_stores(tmp_path)
    svc = _fresh_service()
    # 连续 3 天有练习
    for d in ("2026-08-14", "2026-08-13", "2026-08-12"):
        ps.record_answer(
            f"q_{d}", 0, True, round_id="s1", created_at=f"{d}T10:00:00+00:00",
        )
    results = {r["id"]: r for r in svc.check_all("default")}
    assert results["streak_7"]["progress"] >= 3
    assert results["streak_7"]["unlocked"] is False


def test_fix_and_perfect(tmp_path):
    ls, ps = _use_tmp_stores(tmp_path)
    svc = _fresh_service()
    # 订正: 先错后对
    ps.record_answer("q1", 0, False, round_id="a")
    ps.record_answer("q1", 1, True, round_id="b")
    results = {r["id"]: r for r in svc.check_all("default")}
    assert results["fix_3"]["progress"] == 1

    # 十全十美: 单轮连对 12 题
    for i in range(12):
        ps.record_answer(f"p{i}", 0, True, round_id="perfect")
    results = {r["id"]: r for r in svc.check_all("default")}
    assert results["perfect_10"]["unlocked"] is True
    # 断在 9 连对的另一轮不影响(取最大值)
    ps2_round = "break"
    for i in range(9):
        ps.record_answer(f"b{i}", 0, True, round_id=ps2_round)
    ps.record_answer("b9", 1, False, round_id=ps2_round)
    results = {r["id"]: r for r in svc.check_all("default")}
    assert results["perfect_10"]["unlocked"] is True


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        test_empty_state(p / "e")
        test_progress_and_unlock(p / "p")
        test_persistence_across_restart(p / "r")
        test_streak_from_dates(p / "s")
        test_fix_and_perfect(p / "f")
        print("ALL TESTS PASSED")
