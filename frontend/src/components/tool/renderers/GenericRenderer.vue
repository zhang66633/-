<script setup lang="ts">
/**
 * 通用工具渲染器 — 回退方案，展示 JSON 输入/输出
 *
 * 当工具名不在 toolRenderers 注册表中时使用此组件。
 */
import { computed, ref } from "vue";
import { Wrench, ChevronRight } from "lucide-vue-next";
import type { ToolStatus } from "@/types/response";
import ToolStatusBadge from "@/components/tool/ToolStatusBadge.vue";

const props = defineProps<{
  input: Record<string, unknown> | null;
  output: unknown[] | null;
  status?: ToolStatus;
}>();

const outputOpen = ref(false);

const inputText = computed(() => {
  if (!props.input) return "";
  try {
    return JSON.stringify(props.input, null, 2).slice(0, 500);
  } catch {
    return String(props.input);
  }
});

const outputText = computed(() => {
  if (!props.output || !Array.isArray(props.output)) return "";
  try {
    return JSON.stringify(props.output, null, 2).slice(0, 2000);
  } catch {
    return String(props.output);
  }
});

const hasImages = computed(() => {
  const out = props.output;
  if (!out || !Array.isArray(out)) return false;
  return out.some((item) => item && typeof item === "object" && "images" in item);
});

const toolImages = computed<string[]>(() => {
  const out = props.output;
  if (!out || !Array.isArray(out)) return [];
  const imgs: string[] = [];
  for (const item of out) {
    if (item && typeof item === "object" && "images" in item) {
      const arr = (item as any).images;
      if (Array.isArray(arr)) imgs.push(...arr);
    }
  }
  return imgs;
});
</script>

<template>
  <div class="rounded-md rounded-bl-sm border border-border bg-background px-4 py-3 text-sm leading-relaxed">
    <div class="space-y-1.5 min-w-[260px]">
      <div class="flex items-center gap-2">
        <div class="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          <Wrench class="h-3 w-3" />
          <span>工具调用</span>
        </div>
        <ToolStatusBadge :status="status" />
      </div>

      <div
        v-if="inputText"
        class="text-xs text-muted-foreground font-mono bg-muted/40 rounded p-1.5 overflow-x-auto border border-border"
      >
        {{ inputText }}
      </div>

      <!-- 图表内联 -->
      <div v-if="hasImages" class="space-y-2 mt-1.5">
        <img
          v-for="(src, i) in toolImages"
          :key="i"
          :src="src"
          class="max-w-full rounded-md border border-border"
          loading="lazy"
        />
      </div>

      <details v-if="outputText" class="text-xs">
        <summary class="cursor-pointer text-muted-foreground hover:text-foreground select-none flex items-center gap-1">
          <ChevronRight class="h-3 w-3 transition-transform" :class="{ 'rotate-90': outputOpen }" />
          <span class="font-mono text-[10px] uppercase tracking-wider">{{ outputOpen ? "收起结果" : "查看结果" }}</span>
        </summary>
        <div class="mt-1.5 font-mono bg-muted/40 rounded p-2 border border-border max-h-60 overflow-y-auto whitespace-pre-wrap break-all">
          {{ outputText }}
        </div>
      </details>
    </div>
  </div>
</template>