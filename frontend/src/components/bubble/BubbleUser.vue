<script setup lang="ts">
import type { Message, UserMessage } from "@/types/response";
import { Paperclip } from "lucide-vue-next";
import { computed } from "vue";
import BubbleAvatar from "./BubbleAvatar.vue";

const props = defineProps<{
  message: Message;
}>();

const content = computed(() => props.message.content ?? "");
const files = computed(() => (props.message as UserMessage).files ?? []);
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
          <!-- 附件文件 chip（发送时携带的附件可见） -->
          <div
            v-if="files.length"
            class="mb-1.5 flex flex-wrap justify-end gap-1.5"
          >
            <span
              v-for="(f, i) in files"
              :key="`${f.file_id}-${i}`"
              class="inline-flex items-center gap-1 rounded bg-background/15 px-2 py-0.5 text-xs"
              :title="f.filename"
            >
              <Paperclip class="h-3 w-3 shrink-0" />
              <span class="max-w-40 truncate">{{ f.filename }}</span>
            </span>
          </div>
          <span v-if="content">{{ content }}</span>
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
