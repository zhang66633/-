import DOMPurify from "dompurify";
import { type Token, marked } from "marked";
import markedKatex from "marked-katex-extension";

marked.use(markedKatex({ throwOnError: false, nonStandard: true }));

/**
 * highlight.js 懒加载 — 首次代码块渲染时加载，之后缓存。
 */
let hljsModule: typeof import("highlight.js/lib/core").default | null = null;
const loadedLanguages = new Set<string>();

async function loadHljs() {
  if (!hljsModule) {
    const hljs = (await import("highlight.js/lib/core")).default;
    hljsModule = hljs;
  }
  return hljsModule;
}

/** 静态语言导入映射 — 避免 Vite 无法分析动态 import 路径 */
const LANG_IMPORTERS: Record<string, () => Promise<{ default: any }>> = {
  python: () => import("highlight.js/lib/languages/python"),
  r: () => import("highlight.js/lib/languages/r"),
  matlab: () => import("highlight.js/lib/languages/matlab"),
  julia: () => import("highlight.js/lib/languages/julia"),
  bash: () => import("highlight.js/lib/languages/bash"),
  c: () => import("highlight.js/lib/languages/c"),
  cpp: () => import("highlight.js/lib/languages/cpp"),
  java: () => import("highlight.js/lib/languages/java"),
  javascript: () => import("highlight.js/lib/languages/javascript"),
  typescript: () => import("highlight.js/lib/languages/typescript"),
  json: () => import("highlight.js/lib/languages/json"),
  yaml: () => import("highlight.js/lib/languages/yaml"),
  sql: () => import("highlight.js/lib/languages/sql"),
};

async function ensureLanguage(lang: string) {
  const hljs = await loadHljs();
  if (loadedLanguages.has(lang)) return;
  const importer = LANG_IMPORTERS[lang];
  if (!importer) return; // 不支持的语言，跳过
  try {
    const mod = await importer();
    hljs.registerLanguage(lang, mod.default);
    loadedLanguages.add(lang);
  } catch {
    // 注册失败，跳过
  }
}

/** 已注册的常用语言映射（小写 → hljs 语言名） */
const LANG_MAP: Record<string, string> = {
  python: "python",
  py: "python",
  r: "r",
  matlab: "matlab",
  julia: "julia",
  bash: "bash",
  sh: "bash",
  shell: "bash",
  c: "c",
  cpp: "cpp",
  "c++": "cpp",
  java: "java",
  javascript: "javascript",
  js: "javascript",
  typescript: "typescript",
  ts: "typescript",
  json: "json",
  yaml: "yaml",
  sql: "sql",
  text: "plaintext",
  plaintext: "plaintext",
};

async function highlightCode(code: string, lang?: string): Promise<string> {
  const escaped = code
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  if (!lang || !code.trim()) return escaped;

  const hljsLang = LANG_MAP[lang.toLowerCase()] ?? lang.toLowerCase();
  if (hljsLang === "plaintext") return escaped;

  try {
    await ensureLanguage(hljsLang);
    const hljs = await loadHljs();
    const result = hljs.highlight(code, {
      language: hljsLang,
      ignoreIllegals: true,
    });
    return result.value;
  } catch {
    // 高亮失败，回退纯文本
    return escaped;
  }
}

/**
 * 记忆化渲染缓存 — 按内容 hash 缓存最近 200 条渲染结果
 */
const renderCache = new Map<string, string>();
const MAX_CACHE_SIZE = 200;

function hashContent(text: string): string {
  const len = text.length;
  if (len < 200) return `${len}:${text}`;
  return `${len}:${text.slice(0, 40)}:${text.slice(Math.floor(len / 2) - 20, Math.floor(len / 2) + 20)}:${text.slice(-40)}`;
}

function cacheSet(key: string, value: string) {
  if (renderCache.size >= MAX_CACHE_SIZE) {
    const first = renderCache.keys().next().value;
    if (first !== undefined) renderCache.delete(first);
  }
  renderCache.set(key, value);
}

/**
 * 创建带语法高亮的 marked renderer。
 * 重写 code 渲染为带语言标签 + 复制按钮的代码块。
 */
function createHighlightedRenderer() {
  const renderer = new marked.Renderer();

  renderer.code = ({ text, lang }: { text: string; lang?: string }) => {
    // 用随机 id 关联复制按钮
    const id = `code-${Math.random().toString(36).slice(2, 9)}`;
    const langLabel = lang || "text";
    const escaped = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    return `
<div class="code-block-wrapper relative group my-4 rounded-lg border border-border overflow-hidden">
  <div class="flex items-center justify-between px-4 py-1.5 bg-muted/50 border-b border-border">
    <span class="text-[11px] font-mono text-muted-foreground uppercase tracking-wider">${langLabel}</span>
    <button
      type="button"
      class="text-[11px] text-muted-foreground hover:text-foreground transition-colors opacity-0 group-hover:opacity-100"
      data-code-id="${id}"
    >复制</button>
  </div>
  <pre class="!bg-[#1e1e2e] !text-[#cdd6f4] !p-4 !m-0 !overflow-x-auto !text-sm !leading-relaxed"><code id="${id}" class="language-${langLabel}">${escaped}</code></pre>
</div>`;
  };

  // 表格增强：包裹在响应式容器中（单元格用 parseInline 渲染行内格式）
  renderer.table = ({ header, rows }: { header: any[]; rows: any[][] }) => {
    const thead = `<thead><tr>${header.map((h: any) => `<th>${renderer.parser.parseInline(h.tokens ?? [])}</th>`).join("")}</tr></thead>`;
    const tbody = `<tbody>${rows
      .map(
        (row: any[]) =>
          `<tr>${row.map((cell: any) => `<td>${renderer.parser.parseInline(cell.tokens ?? [])}</td>`).join("")}</tr>`,
      )
      .join("")}</tbody>`;
    return `<div class="table-wrapper overflow-x-auto my-4 rounded-lg border border-border"><table class="min-w-full">${thead}${tbody}</table></div>`;
  };

  // 标题添加锚点 id（供 TOC 跳转），正文用 parseInline 渲染行内格式
  renderer.heading = ({
    text,
    tokens,
    depth,
  }: { text: string; tokens: Token[]; depth: number }) => {
    const id = text
      .replace(/<[^>]*>/g, "")
      .replace(/[^\w一-鿿\s-]/g, "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, "-");
    const inner = renderer.parser.parseInline(tokens ?? []);
    return `<h${depth} id="${id}" class="scroll-mt-20">${inner}</h${depth}>`;
  };

  return renderer;
}

/** 带语法高亮的渲染器实例（同步部分） */
const paperRenderer = createHighlightedRenderer();

/**
 * DOMPurify 安全配置：启用 MathML 配置（保留 KaTeX 的 MathML 无障碍输出），
 * 并补充 KaTeX 输出集中默认未列入白名单的标签。
 * 注意：USE_PROFILES 一旦设置会重置白名单，须显式保留 html/svg 配置以免误伤正文。
 */
const SANITIZE_CONFIG = {
  USE_PROFILES: { html: true, svg: true, svgFilters: true, mathMl: true },
  ADD_TAGS: ["semantics", "annotation", "annotation-xml"],
};

/**
 * 异步渲染 Markdown → HTML，支持代码语法高亮。
 * 第一次调用时加载 highlight.js 和对应语言包。
 */
export async function renderMarkdownAsync(text: string): Promise<string> {
  if (!text) return "";

  const key = hashContent(text);
  const cached = renderCache.get(key);
  if (cached !== undefined) return cached;

  // 先用 marked 解析（此时代码块还是纯文本）
  const raw = marked.parse(text, { renderer: paperRenderer }) as string;
  const sanitized = DOMPurify.sanitize(raw, SANITIZE_CONFIG);

  cacheSet(key, sanitized);
  return sanitized;
}

/**
 * 安全渲染 Markdown → HTML（同步，不带语法高亮，向后兼容）。
 */
export function renderMarkdown(text: string): string {
  if (!text) return "";

  const key = hashContent(text);
  const cached = renderCache.get(key);
  if (cached !== undefined) return cached;

  const raw = marked.parse(text) as string;
  const sanitized = DOMPurify.sanitize(raw, SANITIZE_CONFIG);

  cacheSet(key, sanitized);
  return sanitized;
}

/**
 * 从渲染后的 HTML 中提取所有标题，返回 TOC 条目。
 * 用于 PaperToc 组件。
 */
export interface TocEntry {
  id: string;
  text: string;
  level: number; // 1 = h1, 2 = h2, 3 = h3
}

export function extractToc(html: string): TocEntry[] {
  const headingRegex = /<h([1-3])\s+id="([^"]*)"[^>]*>(.*?)<\/h[1-3]>/gi;
  const entries: TocEntry[] = [];
  let match = headingRegex.exec(html);
  while (match !== null) {
    entries.push({
      level: Number.parseInt(match[1]),
      id: match[2],
      text: match[3].replace(/<[^>]*>/g, ""),
    });
    match = headingRegex.exec(html);
  }
  return entries;
}

/**
 * 流式渲染节流。
 */
let lastStreamRender = 0;
let lastStreamResult = "";
const MIN_INTERVAL = 50;

export function renderMarkdownStreaming(text: string): string {
  if (!text) return "";

  const now = performance.now();
  if (now - lastStreamRender < MIN_INTERVAL) {
    return lastStreamResult;
  }

  lastStreamRender = now;
  lastStreamResult = renderMarkdown(text);
  return lastStreamResult;
}

/** 清空缓存 */
export function clearMarkdownCache() {
  renderCache.clear();
  lastStreamRender = 0;
  lastStreamResult = "";
}
