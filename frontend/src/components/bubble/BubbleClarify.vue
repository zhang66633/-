<script setup lang="ts">
import { computed } from "vue";
import type { Message, ClarifyMessage } from "@/types/response";
import ClarifyCard from "@/components/ClarifyCard.vue";
import BubbleAvatar from "./BubbleAvatar.vue";

const props = defineProps<{
  message: Message;
}>();

const clarifyData = computed(() => {
  if (!props.message.content) return null;
  try {
    return JSON.parse(props.message.content);
  } catch {
    return null;
  }
});

const clarifyAnswered = computed(() => {
  return (props.message as ClarifyMessage).answered ?? false;
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
          <div v-if="clarifyData" class="min-w-[280px]">
            <ClarifyCard :questions="clarifyData" :answered="clarifyAnswered" />
          </div>
        </div>
        <span v-if="timestamp" class="font-mono text-[10px] text-muted-foreground/50 mt-0.5">{{ timestamp }}</span>
      </div>
    </div>
  </div>
</template>
