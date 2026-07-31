<script setup lang="ts">
/**
 * 代码执行渲染器 — Python 语法高亮 + stdout + 图片 + 错误
 *
 * 对应 tool_name: "run_code"
 * highlight.js 动态导入，不增加初始包体积。
 */
import { computed, ref, watch } from "vue";
import { Code2, ChevronRight } from "lucide-vue-next";
import type { ToolStatus } from "@/types/response";
import ToolStatusBadge from "@/components/tool/ToolStatusBadge.vue";

const props = defineProps<{
  input: Record<string, unknown> | null;
  output: unknown[] | null;
  status?: ToolStatus;
}>();

const code = computed(() => {
  if (!props.input) return "";
  return (props.input.code as string) ?? (props.input.source as string) ?? "";
});

const codeExpanded = ref(false);
const codeLines = computed(() => code.value.split("\n").length);
const isLongCode = computed(() => codeLines.value > 15);

const highlightedCode = ref("");

// 动态导入 highlight.js
watch(
  () => code.value,
  async (src) => {
    if (!src) {
      highlightedCode.value = "";
      return;
    }
    try {
      const hljs = (await import("highlight.js/lib/core")).default;
      const python = (await import("highlight.js/lib/languages/python")).default;
      hljs.registerLanguage("python", python);
      highlightedCode.value = hljs.highlight(src, { language: "python" }).value;
    } catch {
      // 高亮失败时回退到纯文本
      highlightedCode.value = src.replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }
  },
  { immediate: true },
);

// 输出解析
const stdout = computed(() => {
  const out = props.output;
  if (!out || !Array.isArray(out)) return "";
  const codeOut = out.find((o) => o && typeof o === "object" && (o as any).name === "run_code");
  if (!codeOut) return "";
  const preview = (codeOut as any).preview as string;
  // 提取 stdout 部分
  const m = preview?.match(/输出:\n([\s\S]*)/);
  return m ? m[1].trim() : "";
});

const hasImages = computed(() => {
  const out = props.output;
  if (!out || !Array.isArray(out)) return false;
  const codeOut = out.find((o) => o && typeof o === "object" && (o as any).name === "run_code");
  return Array.isArray((codeOut as any)?.images) && (codeOut as any).images.length > 0;
});

const toolImages = computed<string[]>(() => {
  const out = props.output;
  if (!out || !Array.isArray(out)) return [];
  const codeOut = out.find((o) => o && typeof o === "object" && (o as any).name === "run_code");
  return (codeOut as any)?.images ?? [];
});

const isRunning = computed(() => props.status === "running");
</script>

<template>
  <div class="rounded-md rounded-bl-sm border border-border bg-background px-4 py-3 text-sm leading-relaxed">
    <div class="space-y-2 min-w-[260px]">
      <!-- 标题行 -->
      <div class="flex items-center gap-2">
        <div class="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          <Code2 class="h-3 w-3" />
          <span>代码执行</span>
        </div>
        <ToolStatusBadge :status="status" />
      </div>

      <!-- 运行中骨架 -->
      <div v-if="isRunning && !code" class="space-y-2 animate-pulse">
        <div class="h-3 bg-muted rounded w-3/4" />
        <div class="h-3 bg-muted rounded w-1/2" />
        <div class="h-3 bg-muted rounded w-2/3" />
      </div>

      <!-- 代码块 -->
      <div v-if="code" class="relative">
        <div
          class="font-mono text-xs bg-muted/40 rounded border border-border overflow-hidden"
          :class="{ 'max-h-60': !codeExpanded && isLongCode }"
        >
          <pre class="p-2.5 overflow-x-auto"><code class="language-python" v-html="highlightedCode" /></pre>
        </div>
        <button
          v-if="isLongCode"
          class="mt-1 flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
          @click="codeExpanded = !codeExpanded"
        >
          <ChevronRight class="h-3 w-3 transition-transform" :class="{ 'rotate-90': codeExpanded }" />
          <span>{{ codeExpanded ? "收起代码" : `展开全部（${codeLines} 行）` }}</span>
        </button>
      </div>

      <!-- 运行中提示 -->
      <div v-if="isRunning && code" class="flex items-center gap-1.5 text-xs text-muted-foreground">
        <span class="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
        <span>代码执行中…</span>
      </div>

      <!-- 输出 -->
      <div v-if="stdout" class="font-mono text-xs bg-muted/40 rounded border border-border p-2.5 max-h-48 overflow-y-auto">
        <pre class="whitespace-pre-wrap break-all">{{ stdout }}</pre>
      </div>

      <!-- 图片 -->
      <div v-if="hasImages" class="space-y-2">
        <img
          v-for="(src, i) in toolImages"
          :key="i"
          :src="src"
          class="max-w-full rounded-md border border-border"
          loading="lazy"
        />
      </div>
    </div>
  </div>
</template>