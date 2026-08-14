<script setup lang="ts">
import type { Message } from "@/types/response";
import { computed } from "vue";
import BubbleAvatar from "./BubbleAvatar.vue";

const props = defineProps<{
  message: Message;
}>();

const content = computed(() => props.message.content ?? "");
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
    <div class="flex-1 min-w-0">
      <div class="flex flex-col items-end">
        <div
          class="max-w-[85%] rounded-md rounded-br-sm px-4 py-3 text-sm leading-relaxed bg-foreground text-background"
        >
          {{ content }}
        </div>
        <span
          v-if="timestamp"
          class="font-mono text-[10px] text-muted-foreground/50 mt-0.5"
        >{{ timestamp }}</span>
      </div>
    </div>
    <div class="flex shrink-0 flex-col items-center self-start pt-0.5">
      <BubbleAvatar :message="message" />
    </div>
  </div>
</template>
