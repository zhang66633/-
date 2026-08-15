# 014 前端体验六项 — 实施记录与验收

> 承接方变更（用户决策）：六项由 A 自己实现，不分配给 B（原 NEXT_DEV_PLAN §4.6 已更新）。

## 状态
- 实施：子代理 680358be 进行中
- 后端契约已核验（前置条件全部成立）：
  - SSE tool_result 携带 ok/duration_ms/error ✓（chat_routes.py 并行执行改造）
  - code_exec running/done + ok/duration_ms ✓
  - GET /api/sandbox/status ✓（TestClient 200 验证过）
  - writing node_progress：outline → 章节批量（并行完成后一次到达）→ abstract → red_team → revise ✓（nodes.py:1081/1139/1158/1170）

## 前端数据流挂点（已核清，供验收对照）
1. 工具徽标：`useStreamChat.ts onToolResult`（当前丢弃 ok/duration，恒标 success）→ store 消息 → BubbleTool/ToolStatusBadge
2. 执行态：`onCodeExec`（running/done 已分支）→ RunCodeRenderer
3. 首字占位：`ensureAgentMsg` 延迟创建 agent 气泡 → ChatThinking
4. 错误重试：`onError`（写「出错了：…」）→ ChatArea/页面渲染处加重试按钮（幂等）
5. 沙箱徽章：新 api + settings 页/侧栏
6. 写作并行提示：solution 页 WS node_progress → ProgressTimeline

## 验收
- [ ] vue-tsc --noEmit exit 0
- [ ] biome check src 0 errors
- [ ] diff 逐项核对六项落点
- [ ] git 提交（type: feat）
