<template>
  <div>
    <h2 class="text-[19px] font-semibold leading-snug tracking-tight text-foreground">设定目标</h2>
    <p class="mt-1.5 text-sm text-muted-foreground">你的备赛计划将根据目标调整</p>
    <div class="mt-6 space-y-6">
      <!-- 竞赛目标 -->
      <div>
        <label class="mb-2 block text-sm font-medium text-foreground">竞赛目标</label>
        <div class="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
          <button
            v-for="g in goals"
            :key="g.value"
            type="button"
            class="relative cursor-pointer rounded-xl border p-3.5 text-left transition-all duration-150"
            :class="goal === g.value
              ? 'border-primary bg-primary/5 ring-1 ring-primary/30'
              : 'border-border bg-card hover:border-muted-foreground/30 hover:bg-accent/40'"
            @click="$emit('update:goal', g.value)"
          >
            <span
              v-if="goal === g.value"
              class="absolute right-2 top-2 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-primary-foreground"
            >
              <Check class="h-3 w-3" />
            </span>
            <span class="block text-lg leading-none">{{ g.emoji }}</span>
            <span class="mt-2 block text-sm font-medium text-foreground">{{ g.label }}</span>
          </button>
        </div>
      </div>

      <!-- 每周时间 -->
      <div>
        <label class="mb-2 block text-sm font-medium text-foreground">每周可用时间</label>
        <div class="flex items-center gap-3">
          <input
            type="range"
            min="5"
            max="40"
            step="5"
            :value="weeklyHours"
            class="h-1.5 flex-1 cursor-pointer appearance-none rounded-full bg-muted accent-primary"
            @input="(e: Event) => $emit('update:weeklyHours', +(e.target as HTMLInputElement).value)"
          />
          <span class="w-12 text-right font-mono text-sm text-foreground">{{ weeklyHours }}h</span>
        </div>
      </div>

      <!-- 目标日期 -->
      <div>
        <label class="mb-2 block text-sm font-medium text-foreground">目标日期(可选)</label>
        <input
          type="month"
          :value="targetDate"
          class="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          @input="(e: Event) => $emit('update:targetDate', (e.target as HTMLInputElement).value)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Check } from "lucide-vue-next";

defineProps<{
  goal: string;
  weeklyHours: number;
  targetDate: string;
}>();

defineEmits<{
  "update:goal": [value: string];
  "update:weeklyHours": [value: number];
  "update:targetDate": [value: string];
}>();

const goals = [
  { value: "国赛", label: "国赛", emoji: "🇨🇳" },
  { value: "美赛", label: "美赛", emoji: "🌍" },
  { value: "研赛", label: "研赛", emoji: "🎓" },
  { value: "兴趣", label: "兴趣学习", emoji: "📚" },
];
</script>
