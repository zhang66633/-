<template>
  <div>
    <h2 class="font-display text-xl font-medium mb-1">设定目标</h2>
    <p class="text-sm text-muted-foreground mb-5">你的备赛计划将根据目标调整</p>
    <div class="space-y-5">
      <!-- 竞赛目标 -->
      <div>
        <label class="text-sm font-medium mb-2 block">竞赛目标</label>
        <div class="grid grid-cols-2 gap-2">
          <button
            v-for="g in goals"
            :key="g.value"
            class="rounded-md border px-4 py-3 text-sm text-left transition-all"
            :class="goal === g.value
              ? 'border-primary bg-primary/5 text-foreground'
              : 'border-border text-muted-foreground hover:border-muted-foreground/30'"
            @click="$emit('update:goal', g.value)"
          >
            <span class="text-lg">{{ g.emoji }}</span>
            <span class="ml-2 font-medium">{{ g.label }}</span>
          </button>
        </div>
      </div>

      <!-- 每周时间 -->
      <div>
        <label class="text-sm font-medium mb-2 block">每周可用时间</label>
        <div class="flex items-center gap-3">
          <input
            type="range"
            min="5"
            max="40"
            step="5"
            :value="weeklyHours"
            class="flex-1 h-1.5 rounded-full appearance-none bg-muted cursor-pointer accent-primary"
            @input="(e: Event) => $emit('update:weeklyHours', +(e.target as HTMLInputElement).value)"
          />
          <span class="font-mono text-sm w-12 text-right">{{ weeklyHours }}h</span>
        </div>
      </div>

      <!-- 目标日期 -->
      <div>
        <label class="text-sm font-medium mb-2 block">目标日期（可选）</label>
        <input
          type="month"
          :value="targetDate"
          class="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          @input="(e: Event) => $emit('update:targetDate', (e.target as HTMLInputElement).value)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
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