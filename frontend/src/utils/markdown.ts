import { marked } from "marked";
import markedKatex from "marked-katex-extension";
import DOMPurify from "dompurify";

marked.use(markedKatex({ throwOnError: false, nonStandard: true }));

/**
 * 记忆化渲染缓存 — 按内容 hash 缓存最近 200 条渲染结果
 */
const renderCache = new Map<string, string>();
const MAX_CACHE_SIZE = 200;

function hashContent(text: string): string {
  // 简单 hash：长度 + 首尾 + 中间采样（性能优先于碰撞率）
  const len = text.length;
  if (len < 200) return `${len}:${text}`;
  return `${len}:${text.slice(0, 40)}:${text.slice(Math.floor(len / 2) - 20, Math.floor(len / 2) + 20)}:${text.slice(-40)}`;
}

function cacheSet(key: string, value: string) {
  if (renderCache.size >= MAX_CACHE_SIZE) {
    // 删除最早的一项
    const first = renderCache.keys().next().value;
    if (first !== undefined) renderCache.delete(first);
  }
  renderCache.set(key, value);
}

/**
 * 安全渲染 Markdown → HTML。
 * 先 marked.parse 转 HTML，再 DOMPurify 过滤 XSS 载荷。
 * 结果按内容 hash 缓存，避免重复 parse + sanitize。
 */
export function renderMarkdown(text: string): string {
  if (!text) return "";

  const key = hashContent(text);
  const cached = renderCache.get(key);
  if (cached !== undefined) return cached;

  const raw = marked.parse(text) as string;
  const sanitized = DOMPurify.sanitize(raw);

  cacheSet(key, sanitized);
  return sanitized;
}

/**
 * 流式渲染节流 — 避免逐字符 parse。
 * 返回节流后的渲染结果；若距上次渲染不足 minInterval，返回上次值。
 */
let lastStreamRender = 0;
let lastStreamResult = "";
const MIN_INTERVAL = 50; // ms

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

/** 清空缓存（页面切换时可选调用） */
export function clearMarkdownCache() {
  renderCache.clear();
  lastStreamRender = 0;
  lastStreamResult = "";
}
