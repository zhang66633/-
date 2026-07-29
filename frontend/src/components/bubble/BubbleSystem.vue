<script setup lang="ts">
import { computed } from "vue";
import { Info, AlertTriangle, CheckCircle2, XCircle } from "lucide-vue-next";
import type { Message, SystemMessage as SysMsg } from "@/types/response";
import { renderMarkdown } from "@/utils/markdown";
import BubbleAvatar from "./BubbleAvatar.vue";

const props = defineProps<{
  message: Message;
}>();

const content = computed(() => props.message.content ?? "");

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

const headline = computed(() => {
  const c = content.value;
  const idx = c.indexOf("\n");
  return idx === -1 ? c : c.slice(0, idx);
});

const body = computed(() => {
  const c = content.value;
  const idx = c.indexOf("\n");
  return idx === -1 ? "" : c.slice(idx + 1).trim();
});

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
          <div class="min-w-[260px] space-y-1.5">
            <div class="flex items-center gap-1.5">
              <component :is="sysIcon" class="h-3.5 w-3.5 shrink-0" :class="sysColor" />
              <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{{ headline }}</span>
            </div>
            <div
              class="prose prose-sm dark:prose-invert max-w-none break-words text-xs leading-relaxed text-foreground/90"
              v-html="renderMarkdown(body)"
            />
          </div>
        </div>
        <span v-if="timestamp" class="font-mono text-[10px] text-muted-foreground/50 mt-0.5">{{ timestamp }}</span>
      </div>
    </div>
  </div>
</template>
