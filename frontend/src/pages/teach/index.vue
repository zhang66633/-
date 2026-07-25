<template>
  <div class="flex h-full bg-background">
    <div class="flex-1 min-w-0 relative">
      <ChatArea
        :messages="chatSession.activeTeachMessages"
        :is-running="chatSession.getIsRunning('teach')"
        :cancellable="true"
        empty-text="开始学习"
        empty-subtext="描述你的问题，我将引导你逐步建立建模思维"
        input-placeholder="描述你想学习的建模问题..."
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
const { handleUserSend, restoreLatestSession, cancelStream } = useStreamChat("teach", "teach");

function handleExport() {
  downloadMarkdown(chatSession.activeTeachMessages, "教学对话.md");
}

onMounted(restoreLatestSession);
</script>
