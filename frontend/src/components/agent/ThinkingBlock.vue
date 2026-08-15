<script setup lang="ts">
import { renderMarkdownStreaming } from "@/utils/markdown";
import { Brain, ChevronDown } from "lucide-vue-next";
/**
 * 思考过程展示 — 可折叠的推理链区域
 *
 * 用于 BubbleAgent 内部，在 agent 回复正文上方展示模型的思考/推理过程。
 * 流式期间实时更新，默认折叠，用户点击展开。
 *
 * 原生折叠实现（button + v-show）：不依赖 radix Collapsible，
 * 避免在虚拟列表环境下点击无响应的问题。
 */
import { computed, ref } from "vue";

const props = withDefaults(
  defineProps<{
    thinking: string;
    streaming?: boolean;
    defaultOpen?: boolean;
  }>(),
  {
    streaming: false,
    defaultOpen: false,
  },
);

const isOpen = ref(props.defaultOpen);

const renderedThinking = computed(() => {
  if (!props.thinking) return "";
  return renderMarkdownStreaming(props.thinking);
});
</script>

<template>
  <div>
    <button
      type="button"
      class="group flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors py-1 select-none cursor-pointer"
      @click="isOpen = !isOpen"
    >
      <Brain class="h-3 w-3" />
      <span class="font-mono text-[10px] uppercase tracking-wider">思考过程</span>
      <ChevronDown
        class="h-3 w-3 transition-transform duration-200"
        :class="{ 'rotate-180': isOpen }"
      />
      <!-- 流式脉冲指示 -->
      <span
        v-if="streaming"
        class="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse"
      />
    </button>
    <div
      v-show="isOpen"
      class="mt-1 mb-2 pl-3 border-l-2 border-muted-foreground/20 text-xs text-muted-foreground/80 leading-relaxed max-h-64 overflow-y-auto"
    >
      <div
        class="prose prose-xs dark:prose-invert max-w-none break-words"
        v-html="renderedThinking"
      />
      <!-- 流式光标 -->
      <span
        v-if="streaming"
        class="inline-block w-1.5 h-4 bg-muted-foreground/50 animate-pulse align-middle ml-0.5"
      />
    </div>
  </div>
</template>
