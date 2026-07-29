<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue";
import { Printer, Clipboard } from "lucide-vue-next";
import type { Message, AgentMessage } from "@/types/response";
import { AgentType } from "@/types/enum";
import { useTypewriter } from "@/composables/useTypewriter";
import { renderMarkdown } from "@/utils/markdown";
import BubbleAvatar from "./BubbleAvatar.vue";

const props = withDefaults(
  defineProps<{
    message: Message;
    isLast?: boolean;
  }>(),
  { isLast: false },
);

const content = computed(() => props.message.content ?? "");

// 打字机仅用于「非流式的一次性外部消息」
const enableTypewriter = computed(
  () => props.isLast && !("streaming" in props.message),
);
const rawText = ref(content.value);
const { displayText, isTyping, skip } = useTypewriter(rawText, 12, enableTypewriter);

watch(content, (val) => { rawText.value = val; }, { immediate: true });

onMounted(() => {
  if (!content.value) return;
  displayText.value = content.value;
  isTyping.value = false;
});

const agentLabel = computed(() => {
  const agentType = (props.message as AgentMessage).agent_type;
  if (!agentType) return "";
  const labels: Record<string, string> = {
    [AgentType.ORCHESTRATOR]: "主控",
    [AgentType.ANALYSIS]: "分析",
    [AgentType.MODELING]: "建模",
    [AgentType.SOLVING]: "求解",
    [AgentType.VERIFICATION]: "验证",
    [AgentType.WRITING]: "写作",
  };
  return labels[agentType] ?? agentType;
});

const isFinalPaper = computed(
  () => typeof props.message.id === "string" && props.message.id.startsWith("final-"),
);
const copied = ref(false);

async function copyMarkdown() {
  try {
    await navigator.clipboard.writeText(content.value);
    copied.value = true;
    setTimeout(() => (copied.value = false), 1500);
  } catch { /* ignore */ }
}

function exportPdf() {
  import("@/utils/exportPaper").then(({ exportPaperAsPDF }) => {
    exportPaperAsPDF({ title: "数学建模论文", markdown: content.value });
  });
}

const renderedContent = computed(() => {
  const text = enableTypewriter.value ? displayText.value : content.value;
  if (!text) return "";
  return renderMarkdown(text);
});

const timestamp = computed(() => {
  if (!props.message.created_at) return "";
  return new Date(props.message.created_at).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });
});
</script>

<template>
  <div class="flex gap-3 w-full my-2 animate-in fade-in slide-in-from-bottom-2">
    <div class="flex flex-col items-center shrink-0">
      <BubbleAvatar :message="message" />
    </div>
    <div class="flex-1 min-w-0">
      <div class="flex flex-col items-start">
        <div class="max-w-[calc(100%-72px)] rounded-md rounded-bl-sm border border-border bg-background text-foreground px-4 py-3 text-sm leading-relaxed">
          <!-- Agent 标签 -->
          <div v-if="agentLabel" class="mb-1.5">
            <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">[{{ agentLabel }}]</span>
          </div>

          <!-- 内容 / 打字机 / 思考点 -->
          <div
            v-if="content"
            class="prose prose-sm dark:prose-invert max-w-none break-words"
            :class="{ 'cursor-pointer': isTyping }"
            v-html="renderedContent"
            @click="isTyping && skip()"
          />
          <div v-else class="flex items-center gap-1.5 py-1">
            <span class="h-1.5 w-1.5 rounded-full bg-current animate-bounce" style="animation-delay: 0ms" />
            <span class="h-1.5 w-1.5 rounded-full bg-current animate-bounce" style="animation-delay: 150ms" />
            <span class="h-1.5 w-1.5 rounded-full bg-current animate-bounce" style="animation-delay: 300ms" />
          </div>

          <!-- 论文操作 -->
          <div v-if="isFinalPaper" class="mt-2 flex items-center gap-2 border-t border-border pt-2">
            <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">论文操作</span>
            <button
              class="inline-flex h-7 items-center gap-1 rounded-md border border-border bg-background px-2.5 text-xs hover:bg-accent hover:text-foreground transition-colors"
              title="在新窗口中打开论文并调出打印对话框，可保存为 PDF"
              @click="exportPdf"
            >
              <Printer class="h-3 w-3" />
              <span>导出 PDF</span>
            </button>
            <button
              class="inline-flex h-7 items-center gap-1 rounded-md border border-border bg-background px-2.5 text-xs hover:bg-accent hover:text-foreground transition-colors"
              title="复制论文 Markdown 源（含 LaTeX 公式）"
              @click="copyMarkdown"
            >
              <Clipboard class="h-3 w-3" />
              <span>{{ copied ? "已复制" : "复制 Markdown" }}</span>
            </button>
          </div>
        </div>
        <span v-if="timestamp" class="font-mono text-[10px] text-muted-foreground/50 mt-0.5">{{ timestamp }}</span>
      </div>
    </div>
  </div>
</template>
