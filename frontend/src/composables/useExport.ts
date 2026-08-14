/** 对话导出 — 将当前会话消息格式化为 Markdown 并下载。 */
import type { Message } from "@/types/response";

function formatTime(iso?: string): string {
  if (!iso) return "";
  return new Date(iso).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** 将消息数组转为 Markdown 文本。 */
export function messagesToMarkdown(
  messages: Message[],
  title = "对话记录",
): string {
  const lines: string[] = [
    `# ${title}`,
    "",
    `> 导出时间: ${new Date().toLocaleString("zh-CN")}`,
    "",
  ];

  for (const msg of messages) {
    const time = formatTime(msg.created_at);

    if (msg.msg_type === "user") {
      lines.push(
        `## 🧑 用户 ${time ? `(${time})` : ""}`,
        "",
        msg.content as string,
        "",
      );
    } else if (msg.msg_type === "agent") {
      lines.push(
        `## 🤖 助手 ${time ? `(${time})` : ""}`,
        "",
        msg.content as string,
        "",
      );
    } else if (msg.msg_type === "tool") {
      const m = msg as any;
      const toolName = m.tool_name || "tool";
      const preview = m.output?.[0]?.preview || JSON.stringify(m.input || {});
      lines.push(
        `### 🔧 工具调用: ${toolName}`,
        "",
        "```",
        String(preview).slice(0, 500),
        "```",
        "",
      );
      // 内联图片
      const images = m.output?.[0]?.images;
      if (images?.length) {
        for (const url of images) {
          lines.push(`![图表](${url})`, "");
        }
      }
    } else if (msg.msg_type === "clarify") {
      lines.push("### ❓ 澄清提问", "", msg.content as string, "");
    }
  }

  lines.push("---", "*由 MathModelAgent 导出*");
  return lines.join("\n");
}

/** 触发浏览器下载 Markdown 文件。 */
export function downloadMarkdown(
  messages: Message[],
  filename = "对话记录.md",
) {
  const md = messagesToMarkdown(messages);
  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** 打开打印对话框（用户可选"另存为 PDF"）。 */
export function printAsPdf(messages: Message[], title = "对话记录") {
  const md = messagesToMarkdown(messages, title);
  const printWindow = window.open("", "_blank");
  if (!printWindow) return;

  printWindow.document.write(`<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>${title}</title>
<style>
  body { font-family: "Microsoft YaHei", sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.7; color: #333; }
  h1 { border-bottom: 2px solid #333; padding-bottom: 8px; }
  h2 { margin-top: 24px; color: #1a1a1a; }
  h3 { color: #555; }
  pre { background: #f5f5f5; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 13px; }
  code { font-family: "Cascadia Code", monospace; }
  blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 12px; color: #666; }
  img { max-width: 100%; }
  hr { border: none; border-top: 1px solid #ddd; margin: 32px 0; }
</style></head><body><pre style="white-space:pre-wrap;background:none;padding:0;font-family:inherit;font-size:15px">${md.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</pre>
<script>window.onload=function(){window.print()}<\/script>
</body></html>`);
  printWindow.document.close();
}
