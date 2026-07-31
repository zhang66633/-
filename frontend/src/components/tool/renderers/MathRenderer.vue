<script setup lang="ts">
/**
 * 数学计算渲染器 — SymPy 符号计算 / 优化求解
 *
 * 对应 tool_name: sympy_compute, solve_optimization
 */
import { computed } from "vue";
import { Sigma } from "lucide-vue-next";
import type { ToolStatus } from "@/types/response";
import ToolStatusBadge from "@/components/tool/ToolStatusBadge.vue";

const props = defineProps<{
  input: Record<string, unknown> | null;
  output: unknown[] | null;
  status?: ToolStatus;
}>();

const expression = computed(() => {
  if (!props.input) return "";
  return (props.input.expression as string) ?? (props.input.problem as string) ?? JSON.stringify(props.input).slice(0, 200);
});

const resultText = computed(() => {
  const out = props.output;
  if (!out || !Array.isArray(out) || out.length === 0) return "";
  const first = out[0];
  if (first && typeof first === "object" && "preview" in first) {
    return (first as any).preview as string;
  }
  return "";
});

const isRunning = computed(() => props.status === "running");
const isEmpty = computed(() => !resultText.value);
</script>

<template>
  <div class="rounded-md rounded-bl-sm border border-border bg-background px-4 py-3 text-sm leading-relaxed">
    <div class="space-y-2 min-w-[260px]">
      <!-- 标题行 -->
      <div class="flex items-center gap-2">
        <div class="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          <Sigma class="h-3 w-3" />
          <span>数学计算</span>
        </div>
        <ToolStatusBadge :status="status" />
      </div>

      <!-- 输入表达式 -->
      <div v-if="expression" class="text-xs font-mono bg-muted/40 rounded border border-border p-2">
        {{ expression }}
      </div>

      <!-- 运行中 -->
      <div v-if="isRunning && isEmpty" class="flex items-center gap-1.5 text-xs text-muted-foreground">
        <span class="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
        <span>计算中…</span>
      </div>

      <!-- 计算结果 -->
      <div v-if="resultText" class="text-xs font-mono bg-muted/40 rounded border border-border p-2.5 max-h-48 overflow-y-auto">
        <pre class="whitespace-pre-wrap break-all">{{ resultText }}</pre>
      </div>
    </div>
  </div>
</template>