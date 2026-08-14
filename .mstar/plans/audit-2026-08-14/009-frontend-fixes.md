# 009 前端批量修复（发现 #8 前端部分、#14–#20）

## Status
- **Priority**: P2 · **Effort**: M · **Risk**: MED · **Depends on**: none · **Category**: bug
- **Planned at**: commit 1c03e8b, 2026-08-14

## Context
登出不清理持久化会话（跨账号泄露）；代码块复制按钮 onclick 被 DOMPurify 剥离失效；SSE 自动重连死代码；流式无卸载清理 + abort 竞态；流式渲染节流状态跨组件互串；知识库「保存」按钮零 API 空操作；KaTeX MathML 被剥离（a11y）；SSE 解析器健壮性。

## Current state
- `frontend/src/stores/auth.ts:83-89` — `_clearSession` 只删 token
- `frontend/src/stores/chatSession.ts:262-268` — persist `mma-chat-sessions` 无清理无上限
- `frontend/src/utils/markdown.ts:132-135,180` — 复制按钮内联 onclick 被 sanitize 剥离
- `frontend/src/composables/useStreamChat.ts:204-223` — `handleUserSendWithRetry` 无调用者、`handleUserSend` 不抛错
- `useStreamChat.ts` — 无 onUnmounted abort；`abortController` 单引用
- `markdown.ts:230-244` — 模块级 `lastStreamRender/lastStreamResult`
- `frontend/src/pages/knowledge/index.vue:778-798,841-846` — `doSaveExtract`/`paperDoSave` 无 API 调用无条件 alert 成功
- `markdown.ts:142-158,180` — heading/table 用原始 `.text`；DOMPurify 无 MathML profile
- `frontend/src/apis/chatApi.ts:150-156` — `\n\n` 切帧 + 单行 `data:` 假设

## Spec
1. `_clearSession` 同时 `localStorage.removeItem("mma-chat-sessions")`（及已知 per-user 键）；persist 加数量上限（如每模式 50 会话，超出淘汰最旧）
2. 复制按钮改事件委托：renderer 输出 `data-code-id`，`PaperViewer`/聊天区容器级 click 监听统一处理
3. 删除 `handleUserSendWithRetry`（或接线到页面发送并加幂等守卫——优先删除，注释同步纠正）
4. `useStreamChat` 每次发送新建独立 AbortController（Map 按会话记录），`onUnmounted`/`onDeactivated` abort 当前流
5. `renderMarkdownStreaming` 节流状态按内容哈希键控（模块级 Map）
6. `doSaveExtract`/`paperDoSave` 对接真实保存（确认后端提取即持久化 → 校验 `entry_id` 存在才报成功并改文案；否则补 create API）
7. DOMPurify 加 `USE_PROFILES: { mathMl: true }` + `ADD_TAGS`（annotation/semantics/mstyle 等 KaTeX 输出集）；heading/table 渲染器改用 `this.parser.parseInline(tokens)`
8. SSE 解析：`\r\n` 归一化后按帧聚合多行 `data:` 拼接；JSON 解析失败计数 console.warn（不静默）

## Verification
- [ ] `pnpm exec vue-tsc` 零错误（010 落脚本后）
- [ ] 手工：登录 A → 聊天 → 登出 → 登录 B → A 的会话不可见
- [ ] 手工：代码块复制按钮可复制；公式渲染正常；流式并发两会话无互串
