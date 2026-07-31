<template>
  <div>
    <h2 class="font-display text-xl font-medium mb-1">自评能力</h2>
    <p class="text-sm text-muted-foreground mb-5">1-5 分，分数越高表示越有信心</p>
    <div class="space-y-5">
      <div v-for="item in items" :key="item.key">
        <div class="flex items-center justify-between mb-1.5">
          <span class="text-sm">{{ item.label }}</span>
          <span class="font-mono text-xs text-muted-foreground">{{ modelValue[item.key as keyof typeof modelValue] }}/5</span>
        </div>
        <input
          type="range"
          min="1"
          max="5"
          :value="modelValue[item.key as keyof typeof modelValue]"
          class="w-full h-1.5 rounded-full appearance-none bg-muted cursor-pointer accent-primary"
          @input="(e: Event) => {
            const val = +(e.target as HTMLInputElement).value;
            $emit('update:modelValue', { ...modelValue, [item.key]: val });
          }"
        />
        <div class="flex justify-between mt-0.5">
          <span class="text-[9px] text-muted-foreground/50">基础薄弱</span>
          <span class="text-[9px] text-muted-foreground/50">精通</span>
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