<template>
  <div class="flex h-full bg-background">
    <div class="flex-1 flex flex-col min-w-0">
      <div class="flex items-center justify-between border-b px-6 py-3 shrink-0">
        <div class="flex items-center gap-3">
          <button
            class="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            @click="$router.push('/learn')"
          >
            <ArrowLeft class="h-4 w-4" />
            返回学习工位
          </button>
          <span class="text-muted-foreground">/</span>
          <span class="font-display font-medium">{{ unit?.title ?? '加载中...' }}</span>
          <span
            v-if="unit"
            class="font-mono text-[10px] px-2 py-0.5 rounded border"
            :class="difficultyBadge"
          >
            {{ difficultyLabel }}
          </span>
        </div>
        <div class="flex items-center gap-3">
          <span class="font-mono text-[10px] text-muted-foreground">
            ⏱ {{ unit?.estimated_minutes ?? '--' }}分钟
          </span>
          <span class="font-mono text-[10px] text-muted-foreground">
            {{ agentEmoji }} {{ agentName }} · 讲解中
          </span>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="store.loading" class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <Loader2 class="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
          <p class="text-sm text-muted-foreground mt-3">加载学习内容...</p>
        </div>
      </div>

      <!-- 错误 -->
      <div v-else-if="store.error" class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <p class="text-sm text-destructive">{{ store.error }}</p>
          <button class="mt-3 text-sm text-primary hover:underline" @click="retry">重试</button>
        </div>
      </div>

      <!-- 内容区 -->
      <div v-else-if="unit" class="flex-1 flex flex-col min-h-0">
        <!-- 单元信息 -->
        <div class="px-6 py-4 border-b bg-muted/20">
          <div class="flex flex-wrap gap-2">
            <span
              v-for="tag in unit.tags"
              :key="tag"
              class="px-2 py-0.5 rounded text-[10px] font-mono bg-accent text-muted-foreground"
            >
              {{ tag }}
            </span>
          </div>
          <p class="text-sm text-muted-foreground mt-2">
            {{ unit.type === 'knowledge' ? '📖 知识讲解' : unit.type === 'practice' ? '✏️ 练习' : '📋 综合项目' }}
            · {{ unit.method_category || '通用' }}
          </p>
          <p v-if="unit.prerequisites.length > 0" class="text-xs text-muted-foreground mt-1">
            前置: {{ unit.prerequisites.map(p => p.unit_id).join(', ') }}
          </p>
        </div>

        <!-- ChatArea 对话式学习 -->
        <ChatArea
          :messages="messages"
          :is-running="false"
          :empty-text="`开始学习: ${unit.title}`"
          :empty-subtext="`${agentName}将用对话方式为你讲解这个知识点`"
          :input-placeholder="`向${agentName}提问...`"
          @send="handleSend"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { ArrowLeft, Loader2 } from "lucide-vue-next";
import ChatArea from "@/components/ChatArea.vue";
import { useLearningStore } from "@/stores/learning";
import type { Message } from "@/types/response";

const route = useRoute();
const store = useLearningStore();
const messages = ref<Message[]>([]);

const unit = computed(() => store.currentUnit);

const agentMap: Record<string, { emoji: string; name: string }> = {
  analyst: { emoji: "🔍", name: "分析师" },
  modeler: { emoji: "🧩", name: "建模师" },
  solver: { emoji: "💻", name: "求解器" },
  verifier: { emoji: "🔬", name: "检验员" },
  editor: { emoji: "✍️", name: "编辑" },
};
const agentInfo = computed(() =>
  agentMap[unit.value?.primary_agent ?? ""] ?? { emoji: "🧭", name: "导航员" },
);
const agentEmoji = computed(() => agentInfo.value.emoji);
const agentName = computed(() => agentInfo.value.name);

const difficultyLabel = computed(() => {
  const m: Record<string, string> = { beginner: "入门", intermediate: "进阶", advanced: "高阶", competition: "竞赛" };
  return m[unit.value?.difficulty ?? "beginner"] ?? "入门";
});
const difficultyBadge = computed(() => {
  const m: Record<string, string> = {
    beginner: "border-emerald-200 text-emerald-700 bg-emerald-50",
    intermediate: "border-amber-200 text-amber-700 bg-amber-50",
    advanced: "border-red-200 text-red-700 bg-red-50",
    competition: "border-purple-200 text-purple-700 bg-purple-50",
  };
  return m[unit.value?.difficulty ?? "beginner"] ?? "";
});

onMounted(() => {
  const unitId = route.params.unitId as string;
  if (unitId) {
    store.loadUnit(unitId);
  }
});

watch(() => route.params.unitId, (newId) => {
  if (newId) store.loadUnit(newId as string);
});

function retry() {
  const unitId = route.params.unitId as string;
  if (unitId) store.loadUnit(unitId);
}

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
