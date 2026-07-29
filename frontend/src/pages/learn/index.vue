<template>
  <div class="flex h-full bg-background">
    <div class="flex-1 min-w-0 flex flex-col">
      <!-- 顶部状态栏 -->
      <div class="flex items-center justify-between border-b px-6 py-3">
        <div class="flex items-center gap-3">
          <span class="font-display text-lg font-medium">学习工位</span>
          <span class="font-mono text-[10px] text-muted-foreground">· 智能体对话式教学</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="font-mono text-[10px] text-muted-foreground">当前角色</span>
          <select class="rounded-md border border-border bg-background px-3 py-1.5 text-sm">
            <option>建模手</option>
            <option>编程手</option>
            <option>论文手</option>
          </select>
        </div>
      </div>

      <!-- 主内容区: 技能树 + 对话区 -->
      <div class="flex-1 flex min-h-0">
        <!-- 左侧技能树 -->
        <div class="w-64 shrink-0 border-r overflow-y-auto p-4">
          <div class="relative mb-4">
            <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="搜索方法..."
              class="w-full rounded-md border border-border bg-background pl-9 pr-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>
          <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mb-3">建模手技能树</p>

          <!-- 技能树占位 -->
          <div class="space-y-1">
            <div v-for="cat in categories" :key="cat.name" class="mb-3">
              <button
                class="flex items-center gap-2 w-full text-left py-1.5 text-sm font-medium hover:text-foreground transition-colors"
                :class="cat.expanded ? 'text-foreground' : 'text-muted-foreground'"
                @click="cat.expanded = !cat.expanded"
              >
                <ChevronRight class="h-3.5 w-3.5 transition-transform" :class="{ 'rotate-90': cat.expanded }" />
                {{ cat.name }}
              </button>
              <div v-if="cat.expanded" class="ml-4 space-y-0.5">
                <div
                  v-for="item in cat.items"
                  :key="item.name"
                  class="flex items-center gap-2 py-1 px-2 rounded text-sm cursor-pointer transition-colors hover:bg-accent"
                  :class="item.status === 'completed' ? 'text-foreground' : item.status === 'active' ? 'text-primary font-medium bg-primary/5' : 'text-muted-foreground'"
                >
                  <span class="text-xs">{{ item.status === 'completed' ? '✅' : item.status === 'active' ? '🔄' : '⬜' }}</span>
                  {{ item.name }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧智能体对话区 -->
        <div class="flex-1 flex flex-col min-w-0">
          <ChatArea
            :messages="messages"
            :is-running="false"
            empty-text="选择左侧技能树开始学习"
            empty-subtext="点击任意方法，智能体将为你讲解"
            input-placeholder="向智能体提问..."
            @send="handleSend"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { Search, ChevronRight } from "lucide-vue-next";
import ChatArea from "@/components/ChatArea.vue";
import type { Message } from "@/types/response";

const messages = ref<Message[]>([]);

const categories = reactive([
  {
    name: "📂 优化类",
    expanded: true,
    items: [
      { name: "线性规划", status: "completed" as const },
      { name: "整数规划", status: "completed" as const },
      { name: "动态规划", status: "active" as const },
      { name: "遗传算法", status: "locked" as const },
    ],
  },
  {
    name: "📂 预测类",
    expanded: false,
    items: [
      { name: "回归分析", status: "completed" as const },
      { name: "时间序列", status: "locked" as const },
      { name: "灰色预测", status: "locked" as const },
    ],
  },
  {
    name: "📂 评价类",
    expanded: false,
    items: [
      { name: "层次分析法(AHP)", status: "locked" as const },
      { name: "TOPSIS", status: "locked" as const },
      { name: "熵权法", status: "locked" as const },
    ],
  },
  {
    name: "📂 统计类",
    expanded: false,
    items: [
      { name: "极大似然估计", status: "locked" as const },
      { name: "贝叶斯推断", status: "locked" as const },
      { name: "蒙特卡洛模拟", status: "locked" as const },
    ],
  },
  {
    name: "📂 图论类",
    expanded: false,
    items: [
      { name: "最短路径", status: "locked" as const },
      { name: "网络流", status: "locked" as const },
    ],
  },
]);

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
