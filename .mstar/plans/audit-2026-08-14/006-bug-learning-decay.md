# 006 BKT 衰减幂等化（发现 #11）

## Status
- **Priority**: P1 · **Effort**: S · **Risk**: LOW · **Depends on**: 010（同步加表征测试） · **Category**: bug
- **Planned at**: commit 1c03e8b, 2026-08-14

## Context
`apply_decay` 每次调用把 `skill.mastery` 原地乘 retention；`profile_routes.py:89` 每次拉取 profile 都调用 → 掌握度按 e^(−N(N+1)/40) 指数崩塌，触发虚假「需复习」标记。

## Current state
- `backend/app/learning/mastery_tracker.py:91-119` — `skill.mastery = old_mastery * retention` 原地乘
- `backend/app/api/profile_routes.py:89` — 每 profile fetch 调 `apply_decay`

## Spec
1. 引入峰值掌握度：skill 增 `peak_mastery` 字段（`record_*` 时 `peak_mastery = max(peak_mastery, 事件 mastery)`）；`mastery` 改为**派生展示值**：`peak_mastery * retention(days_since_last_practiced)`
2. `apply_decay` 变为幂等：不再原地乘，仅计算 `needs_review` 列表；存量无 `peak_mastery` 的技能以当前 mastery 初始化
3. `profile_routes` 保持调用（幂等后无害）——不额外改调用点

## Verification
- [ ] 单测：同 `now` 连续两次 `apply_decay` → 两次返回值一致且 `skill.mastery` 不变
- [ ] 单测：练习事件后 peak 抬升、mastery 随天数单调衰减至 peak·retention 下限
