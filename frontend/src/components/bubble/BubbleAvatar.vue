<script setup lang="ts">
import { computed } from "vue";
import type { Message, AgentMessage } from "@/types/response";
import { AgentType } from "@/types/enum";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const props = defineProps<{
  message: Message;
}>();

const isUser = computed(() => props.message.msg_type === "user");
const isAgent = computed(() => props.message.msg_type === "agent");
const isSystem = computed(() => props.message.msg_type === "system");
const isTool = computed(() => props.message.msg_type === "tool");
const isClarify = computed(() => props.message.msg_type === "clarify");

const letter = computed(() => {
  if (isAgent.value) return "A";
  if (isSystem.value) return "S";
  if (isTool.value) return "T";
  if (isClarify.value) return "?";
  return "A";
});
</script>

<template>
  <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border border-border">
    <AvatarFallback class="text-xs">{{ letter }}</AvatarFallback>
  </div>
</template>
