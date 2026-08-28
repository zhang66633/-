/**
 * Markdown 渲染管线冒烟回归（无 DOM，node 直接跑）。
 *
 * 目的：钉死"方案论文里的 $...$ / $$...$$（含标题、表格内）必须渲染成
 *       .katex 静态 HTML，且不得出现 katex-error"。这是公式渲染问题的
 *       回归护栏——若 marked / marked-katex-extension 升级或配置漂移导致
 *       公式回退成原始 LaTeX，本脚本立即以非零码失败。
 *
 * 使用（frontend/ 目录）：
 *   node scripts/markdown_pipeline_smoke.mjs
 *
 * 说明：配置值（throwOnError/nonStandard）与 KATEX_OPTIONS 保持一致，
 *       唯一真源在 src/utils/markdown.ts。此处不复刻 DOMPurify（需 DOM），
 *       只验证 marked + KaTeX 扩展这一环——这正是公式能否识别解析的关键。
 */

import { marked } from "marked";
import markedKatex from "marked-katex-extension";

// 与 src/utils/markdown.ts 的 KATEX_OPTIONS 保持一致（修改请看那边）
marked.use(markedKatex({ throwOnError: false, nonStandard: true }));

const SAMPLE = `# 建模论文

行内公式 $E=mc^2$ 与独立块：

$$\\min\\ Z = \\sum_{i=1}^{n} c_i x_i$$

### 4.1 子问题（标题内含公式）$x_1 + x_2$

| 符号 | 值 |
|---|---|
| $p_i^*$ | 最优定价 |
| $q_i$ | 需求量 |

敏感性分析表明 $\\frac{\\partial Z}{\\partial p} > 0$。
`;

let html;
try {
  html = marked.parse(SAMPLE);
} catch (e) {
  console.error("FAIL: marked.parse 抛出异常:", e?.message ?? e);
  process.exit(1);
}

const katexSpans = (html.match(/class="katex"/g) ?? []).length;
const katexErrors = (html.match(/katex-error/g) ?? []).length;
const katexDisplays = (html.match(/katex-display/g) ?? []).length;

// 断言：正文、标题、表格内的公式都被 KaTeX 处理
let fail = false;
if (katexSpans < 4) {
  console.error(`FAIL: 期望 ≥4 处 .katex，实际 ${katexSpans}`);
  fail = true;
}
if (katexDisplays < 1) {
  console.error(`FAIL: 期望 ≥1 处 .katex-display，实际 ${katexDisplays}`);
  fail = true;
}
if (katexErrors > 0) {
  console.error(`FAIL: 出现 ${katexErrors} 处 katex-error（公式解析失败）`);
  fail = true;
}
if (!/class="katex"/.test(html.match(/<h3[^>]*>[\s\S]{0,200}/)?.[0] ?? "")) {
  console.error("FAIL: 标题内公式未渲染为 .katex");
  fail = true;
}
if (!/<td><span class="katex"/.test(html)) {
  console.error("FAIL: 表格内公式未渲染为 .katex");
  fail = true;
}

if (fail) {
  console.error("\n--- 渲染结果前 400 字 ---\n" + html.slice(0, 400));
  process.exit(1);
}
console.log(
  `PASS: katex=${katexSpans}, display=${katexDisplays}, errors=${katexErrors} —— 公式管线正常`,
);
