<script setup lang="ts">
import ToolStatusBadge from "@/components/tool/ToolStatusBadge.vue";
import type { ToolStatus } from "@/types/response";
import { BookOpen, ExternalLink, FileText, Search } from "lucide-vue-next";
/**
 * 搜索结果渲染器 — 方法卡片 / 论文卡片 / 网页搜索
 *
 * 对应 tool_name: web_search, search_method_cards, search_similar_papers, get_analysis_template
 */
import { computed } from "vue";

const props = defineProps<{
  input: Record<string, unknown> | null;
  output: unknown[] | null;
  status?: ToolStatus;
  durationMs?: number;
  errorText?: string;
}>();

/** 从 output 中提取文本预览 */
const previewText = computed(() => {
  const out = props.output;
  if (!out || !Array.isArray(out) || out.length === 0) return "";
  const first = out[0];
  if (first && typeof first === "object" && "preview" in first) {
    return (first as any).preview as string;
  }
  return "";
});

/** 解析结果条目 */
interface ParsedItem {
  title: string;
  snippet: string;
  url?: string;
  kind: "method" | "paper" | "web" | "generic";
}

const items = computed<ParsedItem[]>(() => {
  const text = previewText.value;
  if (!text) return [];

  // 尝试按行分割，识别标题模式
  const lines = text.split("\n").filter(Boolean);
  const result: ParsedItem[] = [];
  let current: ParsedItem | null = null;

  for (const line of lines) {
    // 标题行：**Title** 或 ## Title 或 1. Title
    const titleMatch = line.match(
      /^(?:\*{1,2}(.+?)\*{1,2}|#{1,3}\s+(.+)|(?:\d+[\.\、])\s*(.+))/,
    );
    if (titleMatch) {
      if (current) result.push(current);
      const title = (
        titleMatch[1] ??
        titleMatch[2] ??
        titleMatch[3] ??
        line
      ).trim();
      // 跳过长行（可能是正文而非标题）
      if (title.length > 80) {
        if (current) current.snippet += `\n${line}`;
        else
          result.push({
            title: `${title.slice(0, 60)}…`,
            snippet: line,
            kind: "generic",
          });
        continue;
      }
      current = { title, snippet: "", kind: "generic" };
      continue;
    }

    // URL 行
    const urlMatch = line.match(/(https?:\/\/\S+)/);
    if (urlMatch && current) {
      current.url = urlMatch[1];
      continue;
    }

    // 累积内容
    if (current) {
      current.snippet += (current.snippet ? "\n" : "") + line;
    }
  }
  if (current) result.push(current);

  // 如果没解析出结果，显示全文
  if (result.length === 0) {
    return [{ title: "搜索结果", snippet: text, kind: "generic" }];
  }

  return result;
});

const isEmpty = computed(() => items.value.length === 0);
const isRunning = computed(() => props.status === "running");
</script>

<template>
  <div class="rounded-md rounded-bl-sm border border-border bg-background px-4 py-3 text-sm leading-relaxed">
    <div class="space-y-2 min-w-[260px]">
      <!-- 标题行 -->
      <div class="flex items-center gap-2">
        <div class="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          <Search class="h-3 w-3" />
          <span>搜索结果</span>
        </div>
        <ToolStatusBadge :status="status" :duration-ms="durationMs" :error-text="errorText" />
      </div>

      <!-- 运行中 -->
      <div v-if="isRunning && isEmpty" class="flex items-center gap-1.5 text-xs text-muted-foreground animate-pulse">
        <span>正在搜索…</span>
      </div>

      <!-- 结果列表 -->
      <div v-if="items.length > 0" class="space-y-2">
        <div
          v-for="(item, i) in items"
          :key="i"
          class="rounded border border-border bg-muted/20 p-2.5"
        >
          <div class="flex items-start gap-1.5">
            <BookOpen v-if="item.kind === 'method'" class="h-3.5 w-3.5 text-blue-500 shrink-0 mt-0.5" />
            <FileText v-else-if="item.kind === 'paper'" class="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
            <ExternalLink v-else class="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />
            <div class="min-w-0 flex-1">
              <div class="text-xs font-medium truncate">{{ item.title }}</div>
              <div v-if="item.snippet" class="text-[11px] text-muted-foreground mt-0.5 line-clamp-3">
                {{ item.snippet }}
              </div>
              <a
                v-if="item.url"
                :href="item.url"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-0.5 text-[10px] text-primary hover:underline mt-1"
              >
                <ExternalLink class="h-2.5 w-2.5" />
                <span class="truncate">{{ item.url }}</span>
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- 空结果 -->
      <div v-if="!isRunning && isEmpty" class="text-xs text-muted-foreground py-2 text-center">
        未找到相关结果
      </div>
    </div>
  </div>
</template>