<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div class="bg-card border border-border rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        <!-- 进度条 -->
        <div class="flex items-center gap-1 px-6 pt-6 pb-4">
          <div
            v-for="i in 3"
            :key="i"
            class="h-1.5 flex-1 rounded-full transition-colors duration-300"
            :class="i <= step + 1 ? 'bg-primary' : 'bg-muted'"
          />
        </div>

        <!-- 步骤内容 -->
        <div class="px-6 py-2">
          <StepRole
            v-if="step === 0"
            :model-value="role"
            @update:model-value="role = $event"
          />
          <StepAssessment
            v-else-if="step === 1"
            :model-value="assessment"
            @update:model-value="assessment = $event"
          />
          <StepGoal
            v-else
            v-model:goal="goal"
            v-model:weekly-hours="weeklyHours"
            v-model:target-date="targetDate"
          />
        </div>

        <!-- 底部按钮 -->
        <div class="flex items-center justify-between px-6 py-4 border-t">
          <button
            v-if="step > 0"
            class="text-sm text-muted-foreground hover:text-foreground transition-colors"
            @click="prev"
          >
            上一步
          </button>
          <span v-else />
          <button
            class="rounded-md bg-primary text-primary-foreground px-6 py-2 text-sm font-medium hover:bg-primary/90 transition-colors"
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
import { computed } from "vue";
import { useOnboardingStore } from "@/stores/onboarding";
import StepRole from "./StepRole.vue";
import StepAssessment from "./StepAssessment.vue";
import StepGoal from "./StepGoal.vue";

const store = useOnboardingStore();

const visible = computed(() => store.visible);
const step = computed(() => store.step);
const role = computed({
  get: () => store.role,
  set: (v) => (store.role = v),
});
const assessment = computed({
  get: () => store.assessment,
  set: (v) => (store.assessment = v),
});
const goal = computed({
  get: () => store.goal,
  set: (v) => (store.goal = v),
});
const weeklyHours = computed({
  get: () => store.weeklyHours,
  set: (v) => (store.weeklyHours = v),
});
const targetDate = computed({
  get: () => store.targetDate,
  set: (v) => (store.targetDate = v),
});

function next() { store.next(); }
function prev() { store.prev(); }
const emit = defineEmits<{ finish: [payload: any] }>();
function finish() {
  const payload = store.finish();
  emit("finish", payload);
}
</script>