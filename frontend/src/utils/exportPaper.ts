/** 把 Markdown（含 KaTeX 公式 $...$ / $$...$$）渲染成完整 HTML 文档并在新窗口打开。
 *
 * 设计目标: 用户点击"导出 PDF" → 新窗口自动弹出含论文的 HTML →
 * 浏览器原生 Ctrl+P → PDF。零后端依赖。
 *
 * 打印窗口内联 marked + KaTeX (CDN)，把 markdown 转成 HTML 后用 auto-render
 * 把 $...$/$$...$$ 公式渲染成 KaTeX 静态 HTML（不可点击的渲染结果，确保打印效果）。
 */

const KATEX_CSS =
  "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css";
const KATEX_JS = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js";
const KATEX_AUTO =
  "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js";
const MARKED_JS = "https://cdn.jsdelivr.net/npm/marked@12.0.0/marked.min.js";
const DOMPURIFY_JS =
  "https://cdn.jsdelivr.net/npm/dompurify@3.4.12/dist/purify.min.js";

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** 将字符串序列化为可安全嵌入 <script> 的 JSON：转义 `<` 为 \u003c，杜绝 </script> 逃逸。 */
function jsonForScript(value: string): string {
  return JSON.stringify(value).replace(/</g, "\\u003c");
}

const PRINT_HTML_TEMPLATE = (
  title: string,
  markdown: string,
) => `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>${escapeHtml(title)}</title>
  <link rel="stylesheet" href="${KATEX_CSS}" />
  <style>
    :root {
      --fg: #1a1a1a;
      --muted: #6b7280;
      --border: #e5e7eb;
      --bg: #ffffff;
      --bg-soft: #f8fafc;
      --code: #f1f5f9;
    }
    @media print {
      body { margin: 1.5cm; font-size: 11pt; }
      @page {
        margin: 1.5cm; size: A4;
        @bottom-center { content: "— " counter(page) " —"; font-size: 9pt; color: #999; }
      }
      pre, code, table, img { page-break-inside: avoid; }
      /* 打印时代码超长行自动折行,去掉横向滚动条(学术论文排版惯例) */
      pre {
        overflow-x: visible;
        white-space: pre-wrap;
        word-break: break-word;
      }
      h1, h2, h3, h4 { page-break-after: avoid; }
      thead { display: table-header-group; }
      tr { page-break-inside: avoid; }
    }
    html, body { background: var(--bg); color: var(--fg); }
    body {
      font-family: "Source Han Serif SC", "Songti SC", "STSong", -apple-system,
                   BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                   "Microsoft YaHei", "Helvetica Neue", sans-serif;
      max-width: 820px;
      margin: 2.5em auto;
      padding: 0 1.5em;
      line-height: 1.85;
      font-size: 14px;
    }
    h1 { font-size: 1.9em; margin-top: 1.5em; margin-bottom: 0.6em;
         font-weight: 700; border-bottom: 2px solid var(--border); padding-bottom: 0.3em; }
    h2 { font-size: 1.5em; margin-top: 1.4em; margin-bottom: 0.5em;
         font-weight: 700; border-bottom: 1px solid var(--border); padding-bottom: 0.25em; }
    h3 { font-size: 1.25em; margin-top: 1.2em; margin-bottom: 0.4em; font-weight: 600; }
    h4 { font-size: 1.1em; margin-top: 1em; margin-bottom: 0.3em; font-weight: 600; }
    p { margin: 0.8em 0; }
    ul, ol { padding-left: 1.6em; margin: 0.6em 0; }
    li { margin: 0.3em 0; }
    strong { font-weight: 600; color: var(--fg); }
    em { color: var(--fg); font-style: italic; }
    code {
      font-family: "SF Mono", "Cascadia Code", Consolas, "Liberation Mono", monospace;
      background: var(--code);
      padding: 0.15em 0.4em;
      border-radius: 4px;
      font-size: 0.9em;
    }
    pre {
      background: var(--bg-soft);
      border: 1px solid var(--border);
      padding: 1em 1.2em;
      border-radius: 6px;
      overflow-x: auto;
      font-size: 0.88em;
      line-height: 1.55;
    }
    pre code { background: transparent; padding: 0; font-size: 1em; }
    blockquote {
      border-left: 3px solid var(--border);
      margin: 1em 0;
      padding: 0.3em 1em;
      color: var(--muted);
      background: var(--bg-soft);
    }
    hr { border: none; border-top: 1px solid var(--border); margin: 2em 0; }
    img {
      max-width: 100%;
      height: auto;
      display: block;
      margin: 1em auto;
    }
    table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 0.95em; }
    th, td { border: 1px solid var(--border); padding: 0.5em 0.8em; text-align: left; }
    th { background: var(--bg-soft); font-weight: 600; }
    tbody tr:nth-child(even) { background: var(--bg-soft); }
    /* 代码块语言标签 */
    .code-lang-label {
      display: inline-block;
      font-size: 0.75em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 0.4em;
      font-family: "SF Mono", "Cascadia Code", Consolas, monospace;
    }
    .katex-display { margin: 1em 0 !important; }
    a { color: #2563eb; text-decoration: none; }
    /* 顶部标题块 */
    .doc-header {
      text-align: center;
      border-bottom: 2px solid var(--border);
      padding-bottom: 1.2em;
      margin-bottom: 2em;
    }
    .doc-header h1 { border-bottom: none; padding: 0; margin: 0; font-size: 1.8em; }
    .doc-header .meta { color: var(--muted); font-size: 0.9em; margin-top: 0.4em; }
    /* 加载占位 */
    #loading { text-align: center; color: var(--muted); padding: 4em 0; }
  </style>
</head>
<body>
  <div id="loading">📄 正在加载渲染引擎 (KaTeX + Marked)…</div>
  <div id="content" style="display:none"></div>

  <script src="${MARKED_JS}"></script>
  <script src="${KATEX_JS}"></script>
  <script src="${KATEX_AUTO}"></script>
  <script src="${DOMPURIFY_JS}"></script>

  <!-- markdown 原文：以 JSON 数据块承载，避免内联 <script> 被 </script> 逃逸注入 -->
  <script type="application/json" id="raw-md">${jsonForScript(markdown)}</script>
  <script>
    const RAW_MD = JSON.parse(document.getElementById("raw-md").textContent);
    const TITLE = ${jsonForScript(title)};

    // 配置 marked: 启用 GFM + 不在跨行 \$ 上炸错
    marked.setOptions({ gfm: true, breaks: false });

    function render() {
      const rawHtml = marked.parse(RAW_MD);
      // 渲染前用 DOMPurify 消毒（保留 MathML 供 KaTeX 无障碍输出）
      const html = DOMPurify.sanitize(rawHtml, {
        USE_PROFILES: { html: true, svg: true, svgFilters: true, mathMl: true },
        ADD_TAGS: ["semantics", "annotation", "annotation-xml"],
        ADD_ATTR: ["xmlns"],
      });
      const content = document.getElementById("content");
      content.innerHTML =
        '<div class="doc-header">' +
          '<h1>' + escape(TITLE) + '</h1>' +
          '<div class="meta">由 Math Agent 生成 · ' + new Date().toLocaleDateString("zh-CN") + '</div>' +
        '</div>' + html;

      // KaTeX: 渲染所有 $...$ 与 $$...$$
      renderMathInElement(content, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
          { left: "\\\\(", right: "\\\\)", display: false },
          { left: "\\\\[", right: "\\\\]", display: true },
        ],
        throwOnError: false,
      });

      document.getElementById("loading").style.display = "none";
      content.style.display = "";
      document.title = TITLE;

      // 等所有图片加载完成（含失败）再弹打印，避免 PDF 缺图；
      // 超时 6s 兜底，防止某张图卡住整个导出
      const imgs = Array.from(content.querySelectorAll("img"));
      const waitImg = (img) => new Promise((resolve) => {
        if (img.complete) { resolve(); return; }
        img.onload = () => resolve();
        img.onerror = () => resolve();
      });
      Promise.race([
        Promise.all(imgs.map(waitImg)),
        new Promise((r) => setTimeout(r, 6000)),
      ]).then(() => {
        try { window.print(); } catch (e) {}
      });
    }

    function escape(s) {
      return String(s).replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[c]));
    }

    // 等所有 CDN 资源就绪再渲染
    if (document.readyState === "complete") render();
    else window.addEventListener("load", render);
  </script>
</body>
</html>`;

/** 打开新窗口渲染论文 markdown 并触发打印对话框。 */
export function exportPaperAsPDF(opts: {
  title: string;
  markdown: string;
}): void {
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
  // 相对路径图片（/api/images/...、/api/task_files/...）在打印窗口
  // （about:blank）里会解析失败 → 转成父页面 origin 的绝对 URL，图表才能插入 PDF
  const base = window.location.origin;
  const markdown = opts.markdown.replace(
    /\]\(\/(api\/[^)\s]+)\)/g,
    `](${base}/$1)`,
  );
  w.document.open();
  w.document.write(PRINT_HTML_TEMPLATE(opts.title, markdown));
  w.document.close();
}
