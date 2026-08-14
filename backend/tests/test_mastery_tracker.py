"""mastery_tracker 峰值掌握度与幂等衰减的单元测试.

覆盖 plan 006：apply_decay 幂等、峰值抬升、掌握度随天数单调衰减，
以及 REVIEW_THRESHOLD 语义保持不变。
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 让 `app` 包可导入（把 backend/ 加入 sys.path）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.learning.mastery_tracker import (
    MasteryTracker,
    ebbinghaus_retention,
    REVIEW_THRESHOLD,
)
from app.learning.schemas import LearningEvent


T0 = datetime(2026, 1, 1, 12, 0, 0)


def _close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) < tol


def _event(skill_ids, event_type="practice", score=None, created_at=None):
    return LearningEvent(
        event_id="evt_test",
        user_id="u1",
        unit_id="unit1",
        skill_ids=skill_ids,
        event_type=event_type,
        score=score,
        created_at=created_at or T0,
    )


def test_apply_decay_is_idempotent():
    tracker = MasteryTracker()
    tracker.update_from_event("u1", _event(["s1"], score=0.9))
    now = T0 + timedelta(days=30)  # 30 天后保留率低于阈值，needs_review 非空
    first = tracker.apply_decay("u1", now=now)
    m1 = tracker.skills["u1"]["s1"].mastery
    second = tracker.apply_decay("u1", now=now)
    m2 = tracker.skills["u1"]["s1"].mastery
    # 同 now 连续两次结果一致，且 mastery 不再被原地相乘
    assert first == second
    assert m1 == m2
    peak = tracker.skills["u1"]["s1"].peak_mastery
    assert _close(m1, peak * ebbinghaus_retention(30.0))


def test_practice_raises_peak_and_mastery_decays():
    tracker = MasteryTracker()
    tracker.update_from_event("u1", _event(["s1"], score=0.9))
    skill = tracker.skills["u1"]["s1"]
    # 练习正确后峰值抬升（先验 0.2 + 0.15）
    assert skill.peak_mastery > 0.2
    # 刚练习完（now = T0）展示值≈峰值（保留率=1）
    tracker.apply_decay("u1", now=T0)
    m0 = tracker.skills["u1"]["s1"].mastery
    assert _close(m0, skill.peak_mastery)
    # 随天数单调衰减，始终等于 峰值 × 保留率
    prev = m0
    for days in (1, 3, 7, 30):
        tracker.apply_decay("u1", now=T0 + timedelta(days=days))
        cur = tracker.skills["u1"]["s1"].mastery
        assert cur < prev
        assert _close(cur, skill.peak_mastery * ebbinghaus_retention(days))
        prev = cur


def test_review_threshold_semantics():
    tracker = MasteryTracker()
    tracker.update_from_event("u1", _event(["s1"], score=0.9))
    # 30 天后保留率远低于阈值 → 进入 needs_review
    needs = tracker.apply_decay("u1", now=T0 + timedelta(days=30))
    assert "s1" in needs
    assert needs["s1"] < REVIEW_THRESHOLD


def test_legacy_skill_without_peak():
    # 存量技能缺 peak_mastery：以当前 mastery 初始化，apply_decay 幂等
    tracker = MasteryTracker()
    skill = tracker.get_or_create_skill("u1", "s1", prior=0.7)
    # 模拟旧数据：峰值字段偏低/缺失，mastery 才是真实掌握度
    skill.mastery = 0.7
    skill.peak_mastery = 0.2
    skill.last_practiced_at = T0
    now = T0 + timedelta(days=5)
    first = tracker.apply_decay("u1", now=now)
    second = tracker.apply_decay("u1", now=now)
    assert first == second
    # 峰值被抬升到至少当前 mastery（0.7），不会用 0.2 作为衰减基数
    assert tracker.skills["u1"]["s1"].peak_mastery >= 0.7


if __name__ == "__main__":
    # 简单脚本运行器：逐个执行以 test_ 开头的函数，兼容无 pytest 环境
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"PASS {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {name}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
