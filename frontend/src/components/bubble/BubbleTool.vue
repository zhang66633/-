<script setup lang="ts">
import { computed, ref } from "vue";
import { Wrench, ChevronRight } from "lucide-vue-next";
import type { Message, ToolMessage } from "@/types/response";
import BubbleAvatar from "./BubbleAvatar.vue";

const props = defineProps<{
  message: Message;
}>();

const toolName = computed(() => (props.message as ToolMessage).tool_name ?? "");
const toolInput = computed(() => (props.message as ToolMessage).input);
const toolOutput = computed(() => (props.message as ToolMessage).output);
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

function formatToolInput(input: Record<string, unknown> | null): string {
  if (!input) return "";
  try {
    return JSON.stringify(input, null, 2).slice(0, 500);
  } catch {
    return String(input);
  }
}

const timestamp = computed(() => {
  if (!props.message.created_at) return "";
  return new Date(props.message.created_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
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
          <div class="space-y-1.5 min-w-[260px]">
            <div class="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              <Wrench class="h-3 w-3" />
              <span>调用工具: {{ toolName }}</span>
            </div>
            <div
              v-if="toolInput"
              class="text-xs text-muted-foreground font-mono bg-muted/40 rounded p-1.5 overflow-x-auto border border-border"
            >
              {{ formatToolInput(toolInput) }}
            </div>
            <!-- 图表内联 -->
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
        </div>
        <span v-if="timestamp" class="font-mono text-[10px] text-muted-foreground/50 mt-0.5">{{ timestamp }}</span>
      </div>
    </div>
  </div>
</template>
