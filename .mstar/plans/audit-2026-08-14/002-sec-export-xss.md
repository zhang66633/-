# 002 论文导出打印窗口 XSS 修复（发现 #2）

## Status
- **Priority**: P1 · **Effort**: S · **Risk**: MED · **Depends on**: none · **Category**: security
- **Planned at**: commit 1c03e8b, 2026-08-14

## Context
`exportPaper.ts` 在 `window.open("", "_blank")` 的同源子窗口里 `document.write` 完整 HTML：`RAW_MD` 经 `JSON.stringify` 注入内联 `<script>`（`</script>` 可逃逸），marked 输出不经 DOMPurify 直接 `innerHTML`。LLM 论文内容回显用户题目文本，可被 prompt-injection 触发，窃取 `window.opener.localStorage` 中的 JWT。

## Current state
- `frontend/src/utils/exportPaper.ts:133` — `const RAW_MD = ${JSON.stringify(markdown)};`
- `exportPaper.ts:140-146` — `content.innerHTML = ... + html`（html 来自 `marked.parse(RAW_MD)`，无 sanitize）
- 调用点：`components/bubble/BubbleAgent.vue:64-66`、`components/paper/PaperToolbar.vue:46-47`

## Spec
1. markdown 传值改 `<script type="application/json" id="raw-md">` + 服务端（此处为生成端）`JSON.stringify(markdown).replace(/</g, "\\u003c")` 再写入，读取时 `JSON.parse`——彻底杜绝 `</script>` 逃逸
2. 渲染前 `DOMPurify.sanitize(html, { ADD_TAGS: ['math',...MathML 集], ADD_ATTR: ['xmlns'] })`（打印窗口内联 DOMPurify CDN，与主应用同源策略一致）
3. 同源子窗口显式 `w.opener = null`（或 `rel="noopener"` 等价处理），阻断对父窗口的直接引用
4. KaTeX auto-render 在 sanitize 之后执行（保持公式渲染）

## Verification
- [ ] 构造含 `</script><script>alert(document.domain)</script>` 与 `<img src=x onerror=...>` 的 markdown 导出，断言无弹窗、无非法节点
- [ ] 正常论文（含 $$ 公式、表格、代码块）导出渲染不回归
- [ ] `pnpm exec vue-tsc`（见 010 基线）通过
