# 012 文档权威校准 + RULES 红线放宽（发现 #29 + 用户决策）

## Status
- **Priority**: P2 · **Effort**: S · **Risk**: LOW · **Depends on**: none · **Category**: docs
- **Planned at**: commit 1c03e8b, 2026-08-14

## Context
README 引用 RULES 明令废弃的 ARCHITECTURE.md；PLAN.md:3 声称 Next.js+MUI 与实盘矛盾；RULES「仅国产栈」红线与代码/依赖/.env 实际（langchain-anthropic、ANTHROPIC/OPENAI 键）冲突；roadmap 端口过期、把已实现模块标「未实现」。**用户已决策：更新 RULES.md 放宽红线（保留 Anthropic 支持），其余文档以代码为准校准。**

## Current state
- `RULES.md:7` — 「LLM：仅国产栈（DeepSeek / Qwen / GLM 等，不引入 Claude / GPT）」
- `README.md:225` — 「技术架构见 ARCHITECTURE.md」
- `PLAN.md:3` — Next.js+MUI 声称
- `RESOURCES_AND_ROADMAP.md:149-155` — working_memory/episodic_memory/checkpoint 标「❌ 未实现」；端口 8000 过期
- `ARCHITECTURE.md:6` — 自称 v0.2「学习系统设计中」状态过期

## Spec
1. `RULES.md`：红线改为「默认国产栈（DeepSeek/Qwen/GLM），Claude/GPT 经 OpenAI/Anthropic 兼容接口作为可选供应商，需在 .env 显式配置」
2. `README.md`：删除对 ARCHITECTURE.md 的引用（或改「历史设计文档」标注）；技术架构段落自包含
3. `ARCHITECTURE.md`：头部标注「历史文档（2026-07 前），权威见 PLAN.md/RULES.md」；不再作为开发参考
4. `PLAN.md:3` 技术栈声明改为 FastAPI+LangGraph+Vue3（与实盘一致）
5. `RESOURCES_AND_ROADMAP.md`：端口 8002 校正；working_memory/episodic_memory/kb_extractor/checkpoint 标记改为 ✅ 已实现（指向代码路径）；成就系统标「后端已实现待接线」；方向项（导师模式/智能体插话/LaTeX 导出）保留为 backlog
6. 方向 6 条（DIR-1~6）写入 roadmap 的「下一步候选」小节

## Verification
- [ ] grep：README 无「ARCHITECTURE.md」引用；PLAN.md 无 Next.js/MUI
- [ ] grep：RESOURCES_AND_ROADMAP.md 无「❌ 未实现」指向已存在模块
- [ ] RULES.md 新红线与实际依赖一致（langchain-anthropic 保留）
