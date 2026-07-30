<template>
  <div class="flex h-full bg-background">
    <div class="flex-1 min-w-0 flex flex-col">
      <!-- 顶部状态栏 -->
      <div class="flex items-center justify-between border-b px-6 py-3 shrink-0">
        <div class="flex items-center gap-3">
          <span class="font-display text-lg font-medium">学习工位</span>
          <span class="font-mono text-[10px] text-muted-foreground">· 智能体对话式教学</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="font-mono text-[10px] text-muted-foreground">角色</span>
          <select
            class="rounded-md border border-border bg-background px-3 py-1.5 text-sm"
            :value="store.currentRole"
            @change="store.switchRole(($event.target as HTMLSelectElement).value as AgentRole)"
          >
            <option value="modeler">🧩 建模手</option>
            <option value="programmer">💻 编程手</option>
            <option value="writer">✍️ 论文手</option>
          </select>
        </div>
      </div>

      <!-- 主内容区: 技能树 + 对话区 -->
      <div class="flex-1 flex min-h-0">
        <!-- 左侧技能树 -->
        <div class="w-64 shrink-0 border-r overflow-y-auto p-4">
          <SkillGraph
            :categories="store.skillTree"
            :title="`${roleLabel}技能树`"
            :loading="store.loading"
            :error="store.error"
            @select="handleUnitSelect"
          />
        </div>

        <!-- 右侧智能体对话区 -->
        <div class="flex-1 flex flex-col min-w-0">
          <ChatArea
            :messages="chatSession.activeLearningMessages"
            :is-running="chatSession.getIsRunning('learning')"
            empty-text="从左侧技能树选择一个知识点"
            empty-subtext="智能体将用对话方式为你讲解"
            input-placeholder="向智能体提问..."
            cancellable
            @send="handleSend"
            @cancel="cancelStream"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import ChatArea from "@/components/ChatArea.vue";
import SkillGraph from "@/components/SkillGraph.vue";
import { useLearningStore, type AgentRole } from "@/stores/learning";
import { useChatSessionStore } from "@/stores/chatSession";
import { useStreamChat } from "@/composables/useStreamChat";

const router = useRouter();
const store = useLearningStore();
const chatSession = useChatSessionStore();
const { handleUserSend, restoreLatestSession, cancelStream } = useStreamChat("learning", "learning");

const roleLabel = computed(() => {
  const labels: Record<AgentRole, string> = { modeler: "建模手", programmer: "编程手", writer: "论文手" };
  return labels[store.currentRole] ?? "建模手";
});

onMounted(() => {
  store.loadPath();
  restoreLatestSession();
});

function handleUnitSelect(unitId: string) {
  router.push(`/learn/${unitId}`);
}

function handleSend(text: string) {
  handleUserSend(text);
}
</script>
