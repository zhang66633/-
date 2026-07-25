<template>
  <div class="flex h-full bg-background">
    <div class="flex-1 min-w-0 relative">
      <ChatArea
        :messages="chatSession.activeChatMessages"
        :is-running="chatSession.getIsRunning('chat')"
        :cancellable="true"
        @send="handleUserSend"
        @cancel="cancelStream"
        @export="handleExport"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import ChatArea from "@/components/ChatArea.vue";
import { useChatSessionStore } from "@/stores/chatSession";
import { useStreamChat } from "@/composables/useStreamChat";
import { downloadMarkdown } from "@/composables/useExport";

const chatSession = useChatSessionStore();
const { handleUserSend, restoreLatestSession, cancelStream } = useStreamChat("chat", "chat");

function handleExport() {
  downloadMarkdown(chatSession.activeChatMessages, "对话记录.md");
}

onMounted(restoreLatestSession);
</script>
