<template>
  <div class="flex h-full bg-background">
    <div class="flex-1 flex flex-col">
      <!-- 顶部 -->
      <div class="flex items-center justify-between border-b px-6 py-3">
        <div class="flex items-center gap-3">
          <span class="font-display text-lg font-medium">训练场</span>
          <span class="font-mono text-[10px] text-muted-foreground">· 智能体出题 + 批改</span>
        </div>
      </div>

      <!-- Tab 切换 -->
      <div class="flex items-center gap-6 border-b px-6">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          class="relative py-3 text-sm transition-colors"
          :class="activeTab === tab.value ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground'"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
          <span v-if="activeTab === tab.value" class="absolute left-0 right-0 -bottom-px h-px bg-primary" />
        </button>
      </div>

      <!-- 内容区 -->
      <div class="flex-1 flex flex-col min-h-0">
        <!-- 每日推荐 -->
        <div v-if="activeTab === 'daily'" class="flex-1 flex flex-col min-h-0">
          <ChatArea
            :messages="chatSession.activeLearningMessages"
            :is-running="chatSession.getIsRunning('learning')"
            empty-text="开始练习"
            empty-subtext="智能体将为你出题并批改答案"
            input-placeholder="请智能体出题，或描述你想练习的知识点..."
            cancellable
            @send="(text: string) => handleUserSend(text, undefined, { unit_type: '练习', title: '自由练习', difficulty: 'beginner', method_category: '通用', tags: '自由练习', primary_agent: 'verifier', estimated_minutes: '30' })"
            @cancel="cancelStream"
          />
        </div>

        <!-- 错题回顾 -->
        <div v-if="activeTab === 'mistakes'" class="max-w-2xl mx-auto w-full">
          <div class="text-center py-16 text-muted-foreground text-sm">
            暂无错题记录。完成练习后，错题会自动出现在这里。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import ChatArea from "@/components/ChatArea.vue";
import { useChatSessionStore } from "@/stores/chatSession";
import { useStreamChat } from "@/composables/useStreamChat";

const chatSession = useChatSessionStore();
const { handleUserSend, cancelStream } = useStreamChat("learning", "learning");

const activeTab = ref("daily");
const tabs = [
  { label: "每日推荐", value: "daily" },
  { label: "错题回顾", value: "mistakes" },
];
</script>
