<script setup lang="ts">
import ToolStatusBadge from "@/components/tool/ToolStatusBadge.vue";
import type { ToolStatus } from "@/types/response";
import { ChevronRight, Code2 } from "lucide-vue-next";
/**
 * 代码执行渲染器 — Python 语法高亮 + stdout + 图片 + 错误
 *
 * 对应 tool_name: "run_code"
 * highlight.js 动态导入，不增加初始包体积。
 */
import { computed, ref, watch } from "vue";

const props = defineProps<{
  input: Record<string, unknown> | null;
  output: unknown[] | null;
  status?: ToolStatus;
  durationMs?: number;
  errorText?: string;
}>();

const code = computed(() => {
  if (!props.input) return "";
  return (props.input.code as string) ?? (props.input.source as string) ?? "";
});

const codeExpanded = ref(false);
const codeLines = computed(() => code.value.split("\n").length);

const highlightedCode = ref("");

// 执行失败时自动展开代码，便于用户直接看到出错位置
watch(
  () => props.status,
  (s) => {
    if (s === "error") codeExpanded.value = true;
  },
);

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
      const python = (await import("highlight.js/lib/languages/python"))
        .default;
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
  const codeOut = out.find(
    (o) => o && typeof o === "object" && (o as any).name === "run_code",
  );
  if (!codeOut) return "";
  const preview = (codeOut as any).preview as string;
  // 提取 stdout 部分
  const m = preview?.match(/输出:\n([\s\S]*)/);
  return m ? m[1].trim() : "";
});

const hasImages = computed(() => {
  const out = props.output;
  if (!out || !Array.isArray(out)) return false;
  const codeOut = out.find(
    (o) => o && typeof o === "object" && (o as any).name === "run_code",
  );
  return (
    Array.isArray((codeOut as any)?.images) &&
    (codeOut as any).images.length > 0
  );
});

const toolImages = computed<string[]>(() => {
  const out = props.output;
  if (!out || !Array.isArray(out)) return [];
  const codeOut = out.find(
    (o) => o && typeof o === "object" && (o as any).name === "run_code",
  );
  return (codeOut as any)?.images ?? [];
});

const isRunning = computed(() => props.status === "running");

// 图片加载失败（404/临时目录被清理）时隐藏，避免破图占位行
const failedImages = ref<Set<number>>(new Set());

function onImgError(i: number) {
  failedImages.value = new Set([...failedImages.value, i]);
}
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
        <ToolStatusBadge :status="status" :duration-ms="durationMs" :error-text="errorText" />
      </div>

      <!-- 运行中骨架 -->
      <div v-if="isRunning && !code" class="space-y-2 animate-pulse">
        <div class="h-3 bg-muted rounded w-3/4" />
        <div class="h-3 bg-muted rounded w-1/2" />
        <div class="h-3 bg-muted rounded w-2/3" />
      </div>

      <!-- 代码块（默认折叠：只显示展开按钮，点击才渲染代码主体，节省版面） -->
      <div v-if="code">
        <button
          class="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
          @click="codeExpanded = !codeExpanded"
        >
          <ChevronRight class="h-3 w-3 transition-transform" :class="{ 'rotate-90': codeExpanded }" />
          <span>{{ codeExpanded ? "收起代码" : `展开代码（${codeLines} 行）` }}</span>
        </button>
        <div
          v-if="codeExpanded"
          class="mt-1 font-mono text-xs bg-muted/40 rounded border border-border overflow-hidden"
        >
          <pre class="p-2.5 overflow-x-auto max-h-72 overflow-y-auto"><code class="language-python" v-html="highlightedCode" /></pre>
        </div>
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

      <!-- 图片（加载失败自动隐藏，不留破图占位） -->
      <div v-if="hasImages" class="space-y-2">
        <template v-for="(src, i) in toolImages" :key="i">
          <img
            v-if="!failedImages.has(i)"
            :src="src"
            class="max-w-full rounded-md border border-border"
            loading="lazy"
            @error="onImgError(i)"
          />
        </template>
      </div>
    </div>
  </div>
</template>