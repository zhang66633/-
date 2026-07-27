<template>
  <div class="flex gap-3 w-full my-2 animate-in fade-in slide-in-from-bottom-2">
    <div v-if="!isUser" class="flex flex-col items-center shrink-0">
      <div class="flex h-8 w-8 items-center justify-center rounded-sm border border-border">
        <span class="font-display text-xs font-medium leading-none">{{ avatarLetter }}</span>
      </div>
    </div>

    <div class="flex-1 min-w-0">
      <div :class="isUser ? 'flex flex-col items-end' : 'flex flex-col items-start'">
        <div
          :class="[
            'max-w-[calc(100%-72px)] rounded-md px-4 py-3 text-sm leading-relaxed',
            isUser
              ? 'bg-foreground text-background rounded-br-sm'
              : 'border border-border bg-background text-foreground rounded-bl-sm',
          ]"
        >
          <div v-if="isAgent && agentLabel" class="mb-1.5">
            <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">[{{ agentLabel }}]</span>
          </div>

          <div v-if="isClarify && clarifyData" class="min-w-[280px]">
            <ClarifyCard :questions="clarifyData" :answered="clarifyAnswered" />
          </div>

          <div v-else-if="isTool" class="space-y-1.5 min-w-[260px]">
            <div class="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              <Wrench class="h-3 w-3" />
              <span>调用工具: {{ toolName }}</span>
            </div>
            <div v-if="toolInput" class="text-xs text-muted-foreground font-mono bg-muted/40 rounded p-1.5 overflow-x-auto border border-border">
              {{ formatToolInput(toolInput) }}
            </div>
            <!-- run_code 图表内联显示 -->
            <div v-if="toolImages.length > 0" class="space-y-2 mt-1.5">
              <img
                v-for="(src, i) in toolImages"
                :key="i"
                :src="src"
                class="max-w-full rounded-md border border-border"
                loading="lazy"
              />
            </div>
            <details v-if="toolOutput" class="text-xs">
              <summary class="cursor-pointer text-muted-foreground hover:text-foreground select-none flex items-center gap-1">
                <ChevronRight class="h-3 w-3 transition-transform" :class="{ 'rotate-90': toolOutputOpen }" />
                <span class="font-mono text-[10px] uppercase tracking-wider">{{ toolOutputOpen ? "收起结果" : "查看结果" }}</span>
              </summary>
              <div class="mt-1.5 font-mono bg-muted/40 rounded p-2 border border-border max-h-60 overflow-y-auto whitespace-pre-wrap break-all">
                {{ toolOutputText }}
              </div>
            </details>
          </div>

          <div v-else-if="isSystem" class="min-w-[260px] space-y-1.5">
            <div class="flex items-center gap-1.5">
              <component :is="sysIcon" class="h-3.5 w-3.5 shrink-0" :class="sysColor" />
              <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                {{ systemHeadline }}
              </span>
            </div>
            <div
              class="prose prose-sm dark:prose-invert max-w-none break-words text-xs leading-relaxed text-foreground/90"
              v-html="renderMarkdown(systemBody)"
            />
          </div>

          <div
            v-else-if="content"
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

          <div v-if="isFinalPaper" class="mt-2 flex items-center gap-2 border-t border-border pt-2">
            <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              论文操作
            </span>
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

    <div v-if="isUser" class="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border border-border">
      <span class="font-display text-xs font-medium leading-none">U</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue";
import {
  Wrench,
  Info,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Printer,
  Clipboard,
  ChevronRight,
} from "lucide-vue-next";
import type { Message, SystemMessage as SysMsg, AgentMessage, ToolMessage, ClarifyMessage } from "@/types/response";
import ClarifyCard from "@/components/ClarifyCard.vue";
import { AgentType } from "@/types/enum";
import { useTypewriter } from "@/composables/useTypewriter";
import { renderMarkdown } from "@/utils/markdown";

const props = withDefaults(defineProps<{
  message: Message;
  isLast?: boolean;
}>(), {
  isLast: false,
});

const isUser = computed(() => props.message.msg_type === "user");
const isAgent = computed(() => props.message.msg_type === "agent");
const isSystem = computed(() => props.message.msg_type === "system");
const isTool = computed(() => props.message.msg_type === "tool");
const isClarify = computed(() => props.message.msg_type === "clarify");

const clarifyData = computed(() => {
  if (!isClarify.value || !props.message.content) return null;
  try {
    return JSON.parse(props.message.content);
  } catch {
    return null;
  }
});
const clarifyAnswered = computed(() => {
  if (!isClarify.value) return false;
  return (props.message as ClarifyMessage).answered ?? false;
});

const content = computed(() => props.message.content ?? "");

// 打字机仅用于「非流式的一次性外部消息」。
// 我们流式生成的消息（streaming 字段存在，无论 true/false）已实时逐字展示过，
// 切回历史后不应再重放，否则造成闪烁/重复。
const enableTypewriter = computed(
  () =>
    props.isLast &&
    isAgent.value &&
    !("streaming" in props.message),
);
const rawText = ref(content.value);

const { displayText, isTyping, skip } = useTypewriter(rawText, 12, enableTypewriter);

watch(content, (val) => {
  rawText.value = val;
}, { immediate: true });

/** 修复「切页回来重新流式输出」。
 *
 * useTypewriter 的 watch(text, immediate=true) 在每次组件 mount 时都会跑一遍
 * startTyping；如果 enabled=true（且 content 非空），displayText 会被清空然后
 * 从头打字 — 切到其它页面再切回时用户看到的是「再流式输出一遍」。
 *
 * 行为契约: 组件 mount 时 content.value 就是 store 里的当前文本。
 *   - 若 streaming=true/false（消息已被流式渲染过）：displayText 应直接 = content，不要 typewriter
 *   - 若消息是真正「一次性外部消息」且刚 push 进来：typewriter 才会启动
 *
 * 判定: useTypewriter 自身的 watch 跑过 startTyping 之后，如果 content 已等于 displayText
 * 就什么都不做；否则强制 displayText = content.value 同步一次。
 */
onMounted(() => {
  if (!content.value) return;
  displayText.value = content.value;
  isTyping.value = false;
});

const agentLabel = computed(() => {
  if (!isAgent.value) return "";
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

const avatarLetter = computed(() => {
  if (isAgent.value) return "A";
  if (isSystem.value) return "S";
  if (isTool.value) return "T";
  if (isClarify.value) return "?";
  return "A";
});

// 论文消息：id 以 "final-" 开头（来自 taskStore 写入的最终论文 agent 气泡）
const isFinalPaper = computed(
  () => isAgent.value && typeof props.message.id === "string" && props.message.id.startsWith("final-"),
);
const copied = ref(false);

async function copyMarkdown() {
  try {
    await navigator.clipboard.writeText(content.value);
    copied.value = true;
    setTimeout(() => (copied.value = false), 1500);
  } catch {
    /* 浏览器拦截复制权限 — 静默忽略 */
  }
}

function exportPdf() {
  // 动态引入避免主 bundle 体积
  import("@/utils/exportPaper").then(({ exportPaperAsPDF }) => {
    exportPaperAsPDF({
      title: "数学建模论文",
      markdown: content.value,
    });
  });
}

const toolName = computed(() => {
  if (!isTool.value) return "";
  return (props.message as ToolMessage).tool_name ?? "";
});

const toolInput = computed(() => {
  if (!isTool.value) return null;
  return (props.message as ToolMessage).input;
});

const toolOutput = computed(() => {
  if (!isTool.value) return null;
  return (props.message as ToolMessage).output;
});

const toolOutputOpen = ref(false);

const toolImages = computed<string[]>(() => {
  const out = toolOutput.value;
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

const toolOutputText = computed(() => {
  const out = toolOutput.value;
  if (!out) return "";
  try {
    return JSON.stringify(out, null, 2).slice(0, 2000);
  } catch {
    return String(out);
  }
});

const sysIcon = computed(() => {
  const sys = props.message as SysMsg;
  switch (sys.type) {
    case "success": return CheckCircle2;
    case "warning": return AlertTriangle;
    case "error": return XCircle;
    default: return Info;
  }
});

const sysColor = computed(() => {
  const sys = props.message as SysMsg;
  switch (sys.type) {
    case "success": return "text-primary";
    case "warning": return "text-amber-600";
    case "error": return "text-destructive";
    default: return "text-muted-foreground";
  }
});

// 把 "[阶段] 描述\n\n摘要…" 拆成"标题行 + 摘要正文"，便于分别样式化
const systemHeadline = computed(() => {
  if (!isSystem.value) return "";
  const c = content.value;
  const idx = c.indexOf("\n");
  return idx === -1 ? c : c.slice(0, idx);
});
const systemBody = computed(() => {
  if (!isSystem.value) return "";
  const c = content.value;
  const idx = c.indexOf("\n");
  return idx === -1 ? "" : c.slice(idx + 1).trim();
});

// 对带 LaTeX 的流式内容，流式期间每次全量 parse 可能渲染半个公式。
// 直接 parse 全量文本即可——marked 对不完整 $...$ 会按原样输出，不会报错。
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

function formatToolInput(input: Record<string, unknown> | null): string {
  if (!input) return "";
  try {
    return JSON.stringify(input, null, 2).slice(0, 500);
  } catch {
    return String(input);
  }
}
</script>
