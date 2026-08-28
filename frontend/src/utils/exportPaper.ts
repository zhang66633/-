/** 把 Markdown（含 KaTeX 公式 $...$ / $$...$$）渲染成完整 HTML 文档并在新窗口打开。
 *
 * 导出/打印路径：**完全离线自足**，不依赖任何外部 CDN。
 *   旧实现依赖 cdn.jsdelivr.net 的 katex/marked/dompurify——离线或被墙时，
 *   公式回退成原始 LaTeX、或卡在"正在加载渲染引擎"（用户反馈的公式渲染问题根因）。
 *   现改为：先用应用内已验证的 `renderMarkdownAsync`（marked + marked-katex-extension
 *   + DOMPurify，与论文阅读器同管线）预渲染出含 `.katex` 静态 HTML 的正文，
 *   再把 katex.min.css 与 paper.css 内联进打印窗口——离线、无网也能正确渲染公式。
 */

import paperCss from "@/assets/paper.css?raw";
import { renderMarkdownAsync } from "@/utils/markdown";
import katexCss from "katex/dist/katex.min.css?raw";

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** 打印/导出基础排版样式（katex/paper 专属样式另行内联） */
const BASE_CSS = `
:root { --fg:#1a1a1a; --muted:#6b7280; --border:#e5e7eb; --bg:#ffffff; --bg-soft:#f8fafc; }
@media print {
  body { margin: 1.5cm; font-size: 11pt; }
  @page {
    margin: 1.5cm; size: A4;
    @bottom-center { content: "— " counter(page) " —"; font-size: 9pt; color: #999; }
  }
  pre, code, table, img { page-break-inside: avoid; }
  pre { overflow-x: visible; white-space: pre-wrap; word-break: break-word; }
  h1, h2, h3, h4 { page-break-after: avoid; }
  thead { display: table-header-group; }
  tr { page-break-inside: avoid; }
  .no-print { display: none !important; }
}
html, body { background: var(--bg); color: var(--fg); }
body {
  font-family: "Source Han Serif SC","Songti SC","STSong",-apple-system,BlinkMacSystemFont,
               "Segoe UI","PingFang SC","Microsoft YaHei","Helvetica Neue",sans-serif;
  max-width: 820px; margin: 2.5em auto; padding: 0 1.5em; line-height: 1.85; font-size: 14px;
}
h1 { font-size: 1.9em; margin-top: 1.5em; margin-bottom: 0.6em; font-weight:700;
     border-bottom: 2px solid var(--border); padding-bottom: 0.3em; }
h2 { font-size: 1.5em; margin-top: 1.4em; margin-bottom: 0.5em; font-weight:700;
     border-bottom: 1px solid var(--border); padding-bottom: 0.25em; }
h3 { font-size: 1.25em; margin-top: 1.2em; margin-bottom: 0.4em; font-weight:600; }
h4 { font-size: 1.1em; margin-top: 1em; margin-bottom: 0.3em; font-weight:600; }
p { margin: 0.8em 0; }
ul, ol { padding-left: 1.6em; margin: 0.6em 0; }
li { margin: 0.3em 0; }
strong { font-weight: 600; }
code { font-family:"SF Mono","Cascadia Code",Consolas,monospace; background:var(--code,#f1f5f9);
       padding: 0.15em 0.4em; border-radius: 4px; font-size: 0.9em; }
pre { background: var(--bg-soft); border: 1px solid var(--border); padding: 1em 1.2em;
      border-radius: 6px; overflow-x: auto; font-size: 0.88em; line-height: 1.55; }
pre code { background: transparent; padding: 0; font-size: 1em; }
blockquote { border-left:3px solid var(--border); margin:1em 0; padding:0.3em 1em;
             color:var(--muted); background:var(--bg-soft); }
img { max-width:100%; height:auto; display:block; margin:1em auto; }
table { border-collapse:collapse; width:100%; margin:1em 0; font-size:0.95em; }
th, td { border:1px solid var(--border); padding:0.5em 0.8em; text-align:left; }
th { background:var(--bg-soft); font-weight:600; }
tbody tr:nth-child(even){ background:var(--bg-soft); }
a { color:#2563eb; text-decoration:none; }
.doc-header { text-align:center; border-bottom:2px solid var(--border); padding-bottom:1.2em;
              margin-bottom:2em; }
.doc-header h1 { border-bottom:none; padding:0; margin:0; font-size:1.8em; }
.doc-header .meta { color:var(--muted); font-size:0.9em; margin-top:0.4em; }
#loading { text-align:center; color:var(--muted); padding:4em 0; }
`;

const PRINT_HTML_TEMPLATE = (
  title: string,
  bodyHtml: string,
) => `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>${escapeHtml(title)}</title>
  <style>${BASE_CSS}\n/* ── KaTeX 公式样式（内联，离线可渲染）── */\n${katexCss}\n/* ── 论文排版（与 PaperViewer 同）── */\n${paperCss}</style>
</head>
<body>
  <div id="loading">正在渲染…</div>
  <div id="content" style="display:none"></div>
</body>
</html>`;

/** 打开新窗口渲染论文 markdown 并触发打印对话框（离线自足，无 CDN 依赖）。 */
export async function exportPaperAsPDF(opts: {
  title: string;
  markdown: string;
}): Promise<void> {
  // 先同步开窗（刷新用户手势内，避免被弹窗拦截），写入骨架占位
  const w = window.open("", "_blank", "width=900,height=1100");
  if (!w) {
    alert("浏览器拦截了新窗口，请在地址栏允许弹窗后重试。");
    return;
  }
  // 阻断子窗口对父窗口的引用（防跨窗口窃取 localStorage），部分浏览器可能抛错，忽略
  try {
    w.opener = null;
  } catch {
    /* ignore */
  }
  w.document.open();
  w.document.write(PRINT_HTML_TEMPLATE(opts.title, ""));
  w.document.close();

  // 相对路径图片（/api/images/...、/api/task_files/...）在 about:blank 里解析失败
  // → 转成父页面 origin 的绝对 URL，图表才能插入 PDF
  const base = window.location.origin;
  const markdown = opts.markdown.replace(
    /\]\(\/(api\/[^)\s]+)\)/g,
    `](${base}/$1)`,
  );

  // 用应用内已验证的渲染管线预渲染（marked + KaTeX + DOMPurify，离线可用）
  let bodyHtml: string;
  try {
    bodyHtml = await renderMarkdownAsync(markdown);
  } catch (e) {
    bodyHtml = `<pre>渲染失败: ${e instanceof Error ? e.message : String(e)}</pre>`;
  }

  const content = w.document.getElementById("content");
  if (content) {
    content.innerHTML = `<div class="doc-header"><h1>${escapeHtml(opts.title)}</h1><div class="meta">由 Math Agent 生成 · ${new Date().toLocaleDateString("zh-CN")}</div></div>${bodyHtml}`;
    const loading = w.document.getElementById("loading");
    if (loading) loading.style.display = "none";
    content.style.display = "";
  }
  w.document.title = opts.title;

  // 等所有图片加载完成（含失败）再弹打印，避免 PDF 缺图；超时 6s 兜底
  const imgs = Array.from(content?.querySelectorAll("img") ?? []);
  const waitImg = (img: HTMLImageElement) =>
    new Promise<void>((resolve) => {
      if (img.complete) {
        resolve();
        return;
      }
      img.onload = () => resolve();
      img.onerror = () => resolve();
    });
  await Promise.race([
    Promise.all(imgs.map(waitImg)),
    new Promise((r) => setTimeout(r, 6000)),
  ]).catch(() => {});
  try {
    w.print();
  } catch {
    /* 打印被拒/失败不阻塞 */
  }
}
