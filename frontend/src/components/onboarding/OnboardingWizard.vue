<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div class="w-full max-w-[520px] animate-in fade-in zoom-in-95 duration-200 mx-4 overflow-hidden rounded-2xl border border-border bg-card shadow-xl">
        <!-- 步骤阶段 -->
        <template v-if="phase === 'steps'">
          <!-- 进度条 -->
          <div class="px-6 pt-6">
            <div class="mb-2.5 flex items-center justify-between">
              <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                {{ step < 3 ? `第 ${step + 1} 步 · 共 3 步` : "诊断结果" }}
              </span>
              <span class="font-mono text-[10px] text-muted-foreground/60">{{ progressLabel }}</span>
            </div>
            <div class="flex items-center gap-1">
              <div v-for="i in 3" :key="i" class="h-1 flex-1 rounded-full transition-colors duration-300"
                :class="i <= step + 1 ? 'bg-primary' : 'bg-muted'" />
            </div>
          </div>

          <!-- 步骤内容 -->
          <div class="px-6 py-5">
            <Transition name="wizard-step" mode="out-in">
              <div :key="step">
                <div class="mb-5">
                  <p class="font-mono text-[10px] uppercase tracking-wider text-primary">{{ stepKicker[step] }}</p>
                  <p v-if="step === 1" class="mt-1 text-xs text-muted-foreground">
                    先了解一下你的基础 · 根据你的回答,我会为你调整今天的学习内容
                  </p>
                </div>
                <StepRole v-if="step === 0" :model-value="role" @update:model-value="role = $event" />
                <StepAssessment v-else-if="step === 1" :model-value="assessment" @update:model-value="assessment = $event" />
                <StepGoal v-else-if="step === 2" v-model:goal="goal" v-model:weekly-hours="weeklyHours" v-model:target-date="targetDate" />
                <!-- 诊断结果 -->
                <div v-else class="py-4 text-center">
                  <div class="mb-3 text-4xl">{{ role === 'modeler' ? '🧩' : role === 'programmer' ? '💻' : '✍️' }}</div>
                  <h3 class="mb-2 font-display text-xl font-medium">诊断结果</h3>
                  <div class="mb-3 inline-flex items-center gap-2 rounded-full px-4 py-1.5"
                    :class="store.computedLevel === 'beginner' ? 'bg-emerald-50 text-emerald-700' : store.computedLevel === 'intermediate' ? 'bg-amber-50 text-amber-700' : 'bg-purple-50 text-purple-700'">
                    <span class="font-display text-lg font-bold">{{ store.levelLabel }}</span>
                    <span class="text-xs">水平</span>
                  </div>
                  <p class="mb-2 text-sm font-medium">{{ store.levelSuggestion.title }}</p>
                  <ul class="mb-4 space-y-1 text-xs text-muted-foreground">
                    <li v-for="t in store.levelSuggestion.tips" :key="t">{{ t }}</li>
                  </ul>
                  <div class="text-xs text-muted-foreground">
                    <p>我们将为你推荐 <strong class="text-foreground">{{ store.levelSuggestion.focus }}</strong></p>
                    <p class="mt-1">包含入门·进阶·实战三个难度级别</p>
                  </div>
                </div>
              </div>
            </Transition>
          </div>

          <!-- 底部按钮 -->
          <div class="flex items-center justify-between border-t px-6 py-4">
            <button
              v-if="step > 0"
              class="cursor-pointer text-sm text-muted-foreground transition-colors hover:text-foreground"
              @click="prev"
            >
              上一步
            </button>
            <span v-else />
            <button
              class="h-10 cursor-pointer rounded-lg bg-primary px-6 text-sm font-medium text-primary-foreground transition-all duration-150 hover:bg-primary/90 active:scale-[0.98]"
              @click="step < 3 ? next() : startAnalysis()"
            >
              {{ step < 3 ? '下一步' : '开始分析' }}
            </button>
          </div>
        </template>

        <!-- AI 分析阶段 -->
        <div v-else class="px-6 py-8">
          <Transition name="wizard-step" mode="out-in">
            <!-- 分析中: 清单依次点亮(真实 API 并发执行) -->
            <div v-if="phase === 'analyzing'" key="analyzing" class="text-center">
              <h3 class="font-display text-xl font-medium">正在分析你的学习情况</h3>
              <p class="mt-1 text-xs text-muted-foreground">根据你的回答,为你匹配合适的学习路径</p>
              <ul class="mx-auto mt-7 max-w-xs space-y-2.5 text-left">
                <li v-for="(row, i) in 3" :key="i" class="flex items-center gap-2.5 text-sm">
                  <template v-if="analysisStep > i">
                    <Check class="h-4 w-4 shrink-0 text-emerald-500" />
                    <span class="text-foreground/80">{{ rowLabel(i) }}</span>
                  </template>
                  <template v-else-if="analysisStep === i">
                    <Loader2 class="h-4 w-4 shrink-0 animate-spin text-primary" />
                    <span class="text-foreground">{{ rowLabel(i) }}</span>
                  </template>
                  <template v-else>
                    <span class="flex h-4 w-4 shrink-0 items-center justify-center">
                      <span class="h-1.5 w-1.5 rounded-full bg-muted" />
                    </span>
                    <span class="text-muted-foreground/50">{{ rowLabel(i) }}</span>
                  </template>
                </li>
              </ul>
            </div>

            <!-- 就绪 -->
            <div v-else-if="phase === 'ready'" key="ready" class="text-center">
              <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 dark:bg-emerald-950/40">
                <Check class="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
              </div>
              <h3 class="font-display text-xl font-medium">你的学习路径已经准备好了</h3>
              <p class="mt-1.5 text-xs text-muted-foreground">已根据你的基础和目标,生成个性化学习路径</p>
              <button
                class="mt-6 h-10 w-full cursor-pointer rounded-lg bg-primary px-6 text-sm font-medium text-primary-foreground transition-all duration-150 hover:bg-primary/90 active:scale-[0.98]"
                @click="beginLearning"
              >
                开始学习 →
              </button>
            </div>

            <!-- 失败 -->
            <div v-else key="failed" class="text-center">
              <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-red-50 dark:bg-red-950/40">
                <AlertCircle class="h-6 w-6 text-destructive" />
              </div>
              <h3 class="font-display text-xl font-medium">学习路径生成失败</h3>
              <p class="mt-1.5 text-xs text-muted-foreground">{{ errorMsg }}</p>
              <button
                class="mt-6 h-10 w-full cursor-pointer rounded-lg bg-primary px-6 text-sm font-medium text-primary-foreground transition-all duration-150 hover:bg-primary/90 active:scale-[0.98]"
                @click="startAnalysis"
              >
                重试
              </button>
              <button
                class="mt-2 w-full cursor-pointer text-xs text-muted-foreground transition-colors hover:text-foreground"
                @click="bailOut"
              >
                关闭,先逛逛默认课程
              </button>
            </div>
          </Transition>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { type DiagnosePayload, useOnboardingStore } from "@/stores/onboarding";
import { AlertCircle, Check, Loader2 } from "lucide-vue-next";
import { computed, onBeforeUnmount, ref } from "vue";
import StepAssessment from "./StepAssessment.vue";
import StepGoal from "./StepGoal.vue";
import StepRole from "./StepRole.vue";

const store = useOnboardingStore();

const visible = computed(() => store.visible);
const step = computed(() => store.step);
const role = computed({
  get: () => store.role,
  set: (v) => {
    store.role = v;
  },
});
const assessment = computed({
  get: () => store.assessment,
  set: (v) => {
    store.assessment = v;
  },
});
const goal = computed({
  get: () => store.goal,
  set: (v) => {
    store.goal = v;
  },
});
const weeklyHours = computed({
  get: () => store.weeklyHours,
  set: (v) => {
    store.weeklyHours = v;
  },
});
const targetDate = computed({
  get: () => store.targetDate,
  set: (v) => {
    store.targetDate = v;
  },
});

const progressLabel = computed(() => {
  const labels = ["选择角色", "能力自评", "设定目标"];
  return labels[step.value] ?? "诊断";
});

function next() {
  store.next();
}
function prev() {
  store.prev();
}

const emit = defineEmits<{
  /** 诊断结果页点「开始分析」→ 父页面执行 runDiagnose + generateNewPath 后回调 reportResult */
  diagnose: [payload: DiagnosePayload];
  /** 分析成功且用户点「开始学习 →」,payload 与 diagnose 相同;父页面只做收尾(如 toast) */
  finish: [payload: DiagnosePayload];
}>();

// ── AI 分析相位机 ──────────────────────────────────
const phase = ref<"steps" | "analyzing" | "ready" | "failed">("steps");
const analysisStep = ref(0); // 已点亮的清单行数(0-3)
const errorMsg = ref("");
let analysisTimers: number[] = [];

const stepKicker = ["01 · 选择角色", "02 · 基础水平", "03 · 学习目标"];
const analysisLabels = ["已了解你的基础", "已识别你的学习目标"];
function rowLabel(i: number) {
  if (phase.value === "ready") {
    return i < 2 ? analysisLabels[i] : "已生成你的学习路径";
  }
  return i < 2 ? analysisLabels[i] : "正在生成学习路径";
}

function clearAnalysisTimers() {
  for (const t of analysisTimers) window.clearTimeout(t);
  analysisTimers = [];
}

/** 进入分析阶段: 清单动画 + 通知父页面执行真实 API */
function startAnalysis() {
  phase.value = "analyzing";
  analysisStep.value = 0;
  errorMsg.value = "";
  clearAnalysisTimers();
  analysisTimers.push(
    window.setTimeout(() => {
      analysisStep.value = 1;
    }, 450),
  );
  analysisTimers.push(
    window.setTimeout(() => {
      analysisStep.value = 2;
    }, 900),
  );
  emit("diagnose", store.buildPayload());
}

/** 父页面 API 完成后回调。提前返回时快进动画,动画永不拖住 API 结果 */
function reportResult(ok: boolean, message?: string) {
  clearAnalysisTimers();
  if (ok) {
    analysisStep.value = 3;
    phase.value = "ready";
  } else {
    errorMsg.value = message || "生成学习路径失败,请重试";
    phase.value = "failed";
  }
}

/** 就绪态点「开始学习 →」: 关闭向导并通知父页面收尾 */
function beginLearning() {
  const payload = store.finish();
  emit("finish", payload);
}

/** 失败态兜底关闭(不生成个性化路径,回落默认课程) */
function bailOut() {
  store.finish();
}

onBeforeUnmount(() => {
  clearAnalysisTimers();
});

defineExpose({ reportResult });
</script>

<style scoped>
.wizard-step-enter-active,
.wizard-step-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s ease;
}
.wizard-step-enter-from {
  opacity: 0;
  transform: translateY(4px);
}
.wizard-step-leave-to {
  opacity: 0;
}
@media (prefers-reduced-motion: reduce) {
  .wizard-step-enter-active,
  .wizard-step-leave-active {
    transition: none;
  }
}
</style>
