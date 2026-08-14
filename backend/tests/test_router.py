"""router.py 回退路由状态机的单元测试.

覆盖 plan 005 §1：验证 FAIL 只回退一次，建模节点消费回退标志后走
solving→verification，PASS 永不回退，重试耗尽后正常收尾、不再死循环。
"""
import sys
from pathlib import Path

# 让 `app` 包可导入（把 backend/ 加入 sys.path）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.router import after_agent_router


PLAN = ["analysis", "modeling", "solving", "verification", "writing"]


def _state(**overrides) -> dict:
    """构造一个最小可路由状态（缺失键走 after_agent_router 的默认值）。"""
    state = {
        "execution_plan": PLAN,
        "current_step_index": 0,
        "max_retries": 3,
        "retry_count": 0,
        "rollback_target": None,
        "verification_passed": None,
    }
    state.update(overrides)
    return state


def test_fail_rolls_back_to_modeling():
    # 验证节点 FAIL 后：rollback_target="modeling"、retry_count=1 → 回退到建模
    state = _state(current_step_index=3, rollback_target="modeling",
                   retry_count=1, verification_passed=False)
    assert after_agent_router(state) == "modeling_agent"


def test_modeling_consumes_rollback_then_goes_to_solving():
    # 建模节点消费回退标志（rollback_target=None）、指针在建模位置 → 下一步求解
    state = _state(current_step_index=1, rollback_target=None)
    assert after_agent_router(state) == "solving_agent"


def test_solving_goes_to_verification():
    state = _state(current_step_index=2)
    assert after_agent_router(state) == "verification_agent"


def test_pass_never_rolls_back():
    # PASS 时 rollback_target=None → 走正常下一步（写作），绝不回退建模
    state = _state(current_step_index=3, rollback_target=None, verification_passed=True)
    assert after_agent_router(state) == "writing_agent"


def test_retries_exhausted_falls_through():
    # 重试耗尽：验证节点不再置 rollback_target → 正常下一步
    state = _state(current_step_index=3, rollback_target=None, retry_count=4)
    assert after_agent_router(state) == "writing_agent"


def test_stale_rollback_target_over_retries_does_not_loop():
    # 防御：即便 rollback_target 残留但已超重试额度，也不回退（防死循环）
    state = _state(current_step_index=3, rollback_target="modeling", retry_count=4)
    assert after_agent_router(state) == "writing_agent"


def test_last_step_goes_to_format_response():
    state = _state(current_step_index=4, rollback_target=None)
    assert after_agent_router(state) == "format_response"


def test_full_fail_cycle():
    # 完整回退周期：FAIL → modeling → solving → verification
    # 第一次 FAIL
    s = _state(current_step_index=3, rollback_target="modeling",
               retry_count=1, verification_passed=False)
    assert after_agent_router(s) == "modeling_agent"
    # 建模消费标志（指针拨回建模位置 1）
    s = _state(current_step_index=1, rollback_target=None)
    assert after_agent_router(s) == "solving_agent"
    # 求解 → 验证
    s = _state(current_step_index=2)
    assert after_agent_router(s) == "verification_agent"


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
