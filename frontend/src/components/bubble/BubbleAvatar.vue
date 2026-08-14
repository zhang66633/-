<script setup lang="ts">
import { getAgentIdentity } from "@/components/agent/AgentIdentity";
import type { AgentMessage, Message } from "@/types/response";
import { computed } from "vue";

const props = defineProps<{
  message: Message;
}>();

const isUser = computed(() => props.message.msg_type === "user");
const isAgent = computed(() => props.message.msg_type === "agent");
const isSystem = computed(() => props.message.msg_type === "system");
const isTool = computed(() => props.message.msg_type === "tool");
const isClarify = computed(() => props.message.msg_type === "clarify");

const identity = computed(() => {
  if (isAgent.value)
    return getAgentIdentity((props.message as AgentMessage).agent_type);
  return null;
});

const agentColor = computed(() => identity.value?.color ?? "");

const letter = computed(() => {
  if (isUser.value) return "U";
  if (isAgent.value) return "";
  if (isSystem.value) return "S";
  if (isTool.value) return "T";
  if (isClarify.value) return "?";
  return "A";
});
</script>

<template>
  <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border border-border relative">
    <!-- agent 颜色指示点 -->
    <span v-if="agentColor" class="absolute -top-1 -right-1 h-2.5 w-2.5 rounded-full border border-background" :class="agentColor" />
    <!-- agent emoji 或字母 -->
    <span v-if="identity" class="text-xs">{{ identity.emoji }}</span>
    <span v-else class="text-xs">{{ letter }}</span>
  </div>
</template>
