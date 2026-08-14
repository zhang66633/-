<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div class="w-full max-w-[520px] animate-in fade-in zoom-in-95 duration-200 mx-4 overflow-hidden rounded-2xl border border-border bg-card shadow-xl">
        <!-- 进度条 -->
        <div class="px-6 pt-6">
          <div class="mb-2.5 flex items-center justify-between">
            <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              第 {{ step + 1 }} 步 · 共 3 步
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
            @click="step < 2 ? next() : finish()"
          >
            {{ step < 2 ? '下一步' : '开始学习' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useOnboardingStore } from "@/stores/onboarding";
import { computed } from "vue";
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
const emit = defineEmits<{ finish: [payload: any] }>();
function finish() {
  const payload = store.finish();
  emit("finish", payload);
}
</script>
