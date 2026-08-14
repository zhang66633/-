<template>
  <div class="flex h-full bg-background">
    <div class="flex-1 min-w-0 relative">
      <ChatArea
        :messages="chatSession.activeChatMessages"
        :is-running="chatSession.getIsRunning('chat')"
        :cancellable="true"
        :session-title="chatSession.activeChatSession?.title"
        empty-text="开始对话"
        empty-subtext="在下方输入你的问题，智能体将实时回复"
        input-placeholder="输入消息..."
        @send="handleUserSend"
        @cancel="cancelStream"
        @clear="chatSession.clearSession('chat')"
        @new-session="chatSession.newSession('chat')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import ChatArea from "@/components/ChatArea.vue";
import { useStreamChat } from "@/composables/useStreamChat";
import { useChatSessionStore } from "@/stores/chatSession";
import { onMounted } from "vue";

const chatSession = useChatSessionStore();
const { handleUserSend, restoreLatestSession, cancelStream } = useStreamChat(
  "chat",
  "chat",
);

onMounted(restoreLatestSession);
</script>
