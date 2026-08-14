<script setup lang="ts">
import ChatArea from "@/components/ChatArea.vue";
import SkillGraph from "@/components/SkillGraph.vue";
// biome-ignore lint/style/useImportType: Vue 组件注册需要值导入,type-only 会导致运行期组件解析失败
import NextRecommendationCard from "@/components/learning/NextRecommendationCard.vue";
// biome-ignore lint/style/useImportType: Vue 组件注册需要值导入,type-only 会导致运行期组件解析失败
import OnboardingWizard from "@/components/onboarding/OnboardingWizard.vue";
import { useStreamChat } from "@/composables/useStreamChat";
import { toast } from "@/composables/useToast";
import { useChatSessionStore } from "@/stores/chatSession";
import { type AgentRole, useLearningStore } from "@/stores/learning";
import { type DiagnosePayload, useOnboardingStore } from "@/stores/onboarding";
import { useProfileStore } from "@/stores/profile";
import { PanelLeft, PanelLeftOpen } from "lucide-vue-next";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const treeOpen = ref(true);
const store = useLearningStore();
const chatSession = useChatSessionStore();
const onboardingStore = useOnboardingStore();
const profileStore = useProfileStore();
const wizard = ref<InstanceType<typeof OnboardingWizard>>();
const recCard = ref<InstanceType<typeof NextRecommendationCard>>();
const { handleUserSend, restoreLatestSession, cancelStream } = useStreamChat(
  "learning",
  "learning",
);

const roleLabel = computed(() => {
  const labels: Record<AgentRole, string> = {
    modeler: "建模手",
    programmer: "编程手",
    writer: "论文手",
  };
  return labels[store.currentRole] ?? "建模手";
});

onMounted(async () => {
  await profileStore.checkProfile();
  if (!profileStore.hasProfile) {
    onboardingStore.start();
  }
  store.loadPath();
  restoreLatestSession();
});

// 诊断: 向导点「开始分析」后执行真实 API,期间向导保持分析动画
let diagnosing = false;
async function onDiagnose(payload: DiagnosePayload) {
  if (diagnosing) return;
  diagnosing = true;
  try {
    await profileStore.runDiagnose(payload);
    // 用诊断结果的水平生成自适应学习路径
    store.currentLevel = payload.level;
    await store.generateNewPath(payload.role, payload.level, payload.goal);
    // generateNewPath 内部吞错,以 store.error 判断成败
    wizard.value?.reportResult(!store.error, store.error || undefined);
  } catch (e: any) {
    wizard.value?.reportResult(false, e?.message || "诊断失败,请检查后端服务");
  } finally {
    diagnosing = false;
  }
}

// 收尾: 零 API 调用(诊断已在 onDiagnose 完成,防止跑两遍)
function onDiagnoseFinish(_payload: DiagnosePayload) {
  toast("诊断完成,你的个性化学习路径已生成", "success");
  recCard.value?.refresh();
}

function handleUnitSelect(unitId: string) {
  router.push(`/learn/${unitId}`);
}

function handleSend(text: string) {
  handleUserSend(text);
}

// 工位聊天空态快捷提问
const hubQuickActions = [
  {
    label: "我现在该学什么",
    text: "我现在该学什么?请根据我的学习路径给我一个建议",
  },
  { label: "帮我制定学习计划", text: "帮我制定一个本周的学习计划" },
];
</script>

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
        <!-- 左侧技能树(可折叠,折叠按钮固定在底部) -->
        <div
          class="shrink-0 border-r flex flex-col transition-all duration-200"
          :class="treeOpen ? 'w-64' : 'w-10'"
        >
          <div v-show="treeOpen" class="flex-1 overflow-y-auto p-4 min-h-0">
            <!-- AI 下一步推荐 -->
            <NextRecommendationCard
              ref="recCard"
              class="mb-3"
              :role="store.currentRole"
              compact
              @go="handleUnitSelect"
            />
            <SkillGraph
              :categories="store.skillTree"
              :title="`${roleLabel}技能树`"
              :loading="store.loading"
              :error="store.error"
              @select="handleUnitSelect"
            />
          </div>
          <button
            class="flex shrink-0 items-center justify-center border-t py-2 transition-colors hover:bg-accent/50"
            :title="treeOpen ? '折叠技能树' : '展开技能树'"
            @click="treeOpen = !treeOpen"
          >
            <PanelLeftOpen v-if="treeOpen" class="h-3.5 w-3.5 text-muted-foreground" />
            <PanelLeft v-else class="h-3.5 w-3.5 text-muted-foreground" />
          </button>
        </div>

        <!-- 右侧智能体对话区 -->
        <div class="flex-1 flex flex-col min-w-0">
          <ChatArea
            :messages="chatSession.activeLearningMessages"
            :is-running="chatSession.getIsRunning('learning')"
            empty-text="从左侧技能树选择一个知识点"
            empty-subtext="智能体将用对话方式为你讲解"
            input-placeholder="向智能体提问..."
            :session-title="chatSession.activeLearningSession?.title"
            :quick-actions="hubQuickActions"
            cancellable
            @send="handleSend"
            @cancel="cancelStream"
            @clear="chatSession.clearSession('learning')"
            @new-session="chatSession.newSession('learning')"
          />
        </div>
      </div>
    </div>

    <!-- 诊断向导 -->
    <OnboardingWizard
      ref="wizard"
      @diagnose="onDiagnose"
      @finish="onDiagnoseFinish"
    />
  </div>
</template>