<script setup lang="ts">
/**
 * 消息气泡 — 按 msg_type 分发到对应子组件
 *
 *   user     → BubbleUser
 *   agent    → BubbleAgent（含 Markdown / 打字机 / 论文操作）
 *   tool     → BubbleTool（含输入 / 输出 / 图表）
 *   system   → BubbleSystem（含图标 / 摘要）
 *   clarify  → BubbleClarify（含澄清卡片）
 */
import { computed } from "vue";
import type { Message } from "@/types/response";
import BubbleUser from "@/components/bubble/BubbleUser.vue";
import BubbleAgent from "@/components/bubble/BubbleAgent.vue";
import BubbleTool from "@/components/bubble/BubbleTool.vue";
import BubbleSystem from "@/components/bubble/BubbleSystem.vue";
import BubbleClarify from "@/components/bubble/BubbleClarify.vue";

const props = withDefaults(
  defineProps<{
    message: Message;
    isLast?: boolean;
  }>(),
  { isLast: false },
);

const emit = defineEmits<{
  openPaper: [];
}>();

const component = computed(() => {
  switch (props.message.msg_type) {
    case "user":    return BubbleUser;
    case "agent":   return BubbleAgent;
    case "tool":    return BubbleTool;
    case "system":  return BubbleSystem;
    case "clarify": return BubbleClarify;
    default:        return BubbleSystem;
  }
});
</script>

<template>
  <component :is="component" :message="message" :is-last="isLast" @open-paper="emit('openPaper')" />
</template>
