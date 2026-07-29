<template>
  <div class="flex h-full bg-background">
    <div class="flex-1 flex flex-col">
      <div class="flex items-center justify-between border-b px-6 py-3">
        <div class="flex items-center gap-3">
          <button class="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors" @click="$router.push('/learn')">
            <ArrowLeft class="h-4 w-4" />
            返回学习工位
          </button>
          <span class="text-muted-foreground">/</span>
          <span class="font-display font-medium">{{ unitTitle }}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="font-mono text-[10px] text-muted-foreground">🧩 建模师 · 讲解中</span>
        </div>
      </div>

      <ChatArea
        :messages="messages"
        :is-running="false"
        :empty-text="`开始学习 ${unitTitle}`"
        empty-subtext="智能体将用对话方式为你讲解这个知识点"
        :input-placeholder="`向建模师提问关于 ${unitTitle} 的问题...`"
        @send="handleSend"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRoute } from "vue-router";
import { ArrowLeft } from "lucide-vue-next";
import ChatArea from "@/components/ChatArea.vue";
import type { Message } from "@/types/response";

const route = useRoute();
const unitTitle = computed(() => (route.params.unitId as string) || "未选择");
const messages = ref<Message[]>([]);

function handleSend(text: string) {
  const msg: Message = {
    id: `msg_${Date.now()}`,
    msg_type: "user",
    content: text,
    created_at: new Date().toISOString(),
  };
  messages.value.push(msg);
}
</script>
