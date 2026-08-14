<template>
  <div class="flex h-full bg-background">
    <div class="flex-1 min-w-0 flex flex-col">
      <!-- 顶部 -->
      <div class="flex items-center justify-between border-b px-6 py-3">
        <div class="flex items-center gap-3">
          <span class="font-display text-lg font-medium">答疑室</span>
          <span class="font-mono text-[10px] text-muted-foreground">· 随时 @智能体 提问</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-muted-foreground">当前:</span>
          <select class="rounded-md border border-border bg-background px-3 py-1.5 text-sm">
            <option>🤖 自动匹配</option>
            <option>🔍 分析师</option>
            <option>🧩 建模师</option>
            <option>💻 求解器</option>
            <option>🔬 检验员</option>
            <option>✍️ 编辑</option>
          </select>
        </div>
      </div>

      <!-- 对话区: 复用 ChatArea -->
      <div class="flex-1 min-h-0 flex">
        <div class="flex-1">
          <ChatArea
            :messages="chatSession.activeQaMessages"
            :is-running="chatSession.getIsRunning('qa')"
            empty-text="智能答疑"
            empty-subtext="输入 @智能体名 召唤指定智能体回答，联网推荐外部资源"
            input-placeholder="输入问题，或 @分析师/@建模师 指定智能体..."
            :session-title="chatSession.activeQaSession?.title"
            cancellable
            @send="handleSend"
            @cancel="cancelStream"
            @new-session="chatSession.newSession('qa')"
          />
        </div>

        <!-- 右侧面板: 可召唤智能体 + 相关知识点 -->
        <div class="w-56 shrink-0 border-l p-4 overflow-y-auto">
          <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mb-3">可召唤智能体</p>
          <div class="space-y-1.5">
            <button
              v-for="agent in agents"
              :key="agent.name"
              class="flex items-center gap-2 w-full text-left py-1.5 px-2 rounded text-sm transition-colors hover:bg-accent"
              :class="agent.active ? 'text-foreground bg-accent' : 'text-muted-foreground'"
            >
              <span>{{ agent.emoji }}</span>
              <span>{{ agent.name }}</span>
              <span class="ml-auto text-[10px] text-muted-foreground/50">{{ agent.active ? '当前' : '' }}</span>
            </button>
          </div>

          <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mt-6 mb-3">相关知识点</p>
          <div class="space-y-1.5">
            <div class="text-xs text-muted-foreground">选择左侧技能树后将显示相关知识点</div>
          </div>

          <!-- 图片上传 -->
          <div class="mt-6 pt-4 border-t">
            <button class="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
              <ImageIcon class="h-3.5 w-3.5" />
              上传题目图片
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ChatArea from "@/components/ChatArea.vue";
import { useStreamChat } from "@/composables/useStreamChat";
import { useChatSessionStore } from "@/stores/chatSession";
import { ImageIcon } from "lucide-vue-next";
import { ref } from "vue";

const chatSession = useChatSessionStore();
const { handleUserSend, cancelStream } = useStreamChat("qa", "qa");

const agents = ref([
  { name: "分析师", emoji: "🔍", active: false },
  { name: "建模师", emoji: "🧩", active: false },
  { name: "求解器", emoji: "💻", active: false },
  { name: "检验员", emoji: "🔬", active: false },
  { name: "编辑", emoji: "✍️", active: false },
  { name: "自动匹配", emoji: "🤖", active: true },
]);

function handleSend(text: string) {
  handleUserSend(text);
}
</script>
