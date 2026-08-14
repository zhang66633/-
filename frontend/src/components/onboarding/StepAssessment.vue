<template>
  <div>
    <h2 class="text-[19px] font-semibold leading-snug tracking-tight text-foreground">自评能力</h2>
    <p class="mt-1.5 text-sm text-muted-foreground">1-5 分,分数越高表示越有信心</p>
    <div class="mt-6 space-y-5">
      <div v-for="item in items" :key="item.key">
        <div class="mb-2 flex items-center justify-between">
          <span class="text-sm font-medium text-foreground">{{ item.label }}</span>
          <span class="rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-muted-foreground">
            {{ modelValue[item.key as keyof typeof modelValue] }}/5
          </span>
        </div>
        <input
          type="range"
          min="1"
          max="5"
          :value="modelValue[item.key as keyof typeof modelValue]"
          class="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-muted accent-primary"
          @input="(e: Event) => {
            const val = +(e.target as HTMLInputElement).value;
            $emit('update:modelValue', { ...modelValue, [item.key]: val });
          }"
        />
        <div class="mt-1 flex justify-between">
          <span class="text-[10px] text-muted-foreground/60">基础薄弱</span>
          <span class="text-[10px] text-muted-foreground/60">精通</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SelfAssessment } from "@/stores/onboarding";

defineProps<{ modelValue: SelfAssessment }>();
defineEmits<{ "update:modelValue": [value: SelfAssessment] }>();

const items = [
  { key: "math_level", label: "数学基础" },
  { key: "programming_level", label: "编程能力" },
  { key: "writing_level", label: "写作水平" },
  { key: "modeling_experience", label: "建模经验" },
];
</script>
