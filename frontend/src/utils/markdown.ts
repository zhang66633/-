import { marked } from "marked";
import markedKatex from "marked-katex-extension";
import DOMPurify from "dompurify";

marked.use(markedKatex({ throwOnError: false, nonStandard: true }));

/**
 * 安全渲染 Markdown → HTML。
 * 先 marked.parse 转 HTML，再 DOMPurify 过滤 XSS 载荷。
 */
export function renderMarkdown(text: string): string {
  if (!text) return "";
  const raw = marked.parse(text) as string;
  return DOMPurify.sanitize(raw);
}
