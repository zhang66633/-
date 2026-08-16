<template>
  <div class="grid grid-cols-4 gap-4 mt-8">
    <div class="rounded-md border border-border bg-card p-4 text-center">
      <p class="font-mono text-3xl font-medium tabular-nums">{{ stats.streak_days ?? 0 }}</p>
      <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mt-2">连续学习天数</p>
    </div>
    <div class="rounded-md border border-border bg-card p-4 text-center">
      <p class="font-mono text-3xl font-medium tabular-nums">{{ stats.completed_units ?? 0 }}<span class="text-base text-muted-foreground">/{{ stats.total_units ?? 45 }}</span></p>
      <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mt-2">完成单元</p>
    </div>
    <div class="rounded-md border border-border bg-card p-4 text-center">
      <p class="font-mono text-3xl font-medium tabular-nums">{{ stats.total_units ? Math.round((stats.completed_units ?? 0) / (stats.total_units || 1) * 100) : 0 }}<span class="text-base">%</span></p>
      <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mt-2">完成率</p>
    </div>
    <div class="rounded-md border border-border bg-card p-4 text-center">
      <p class="font-mono text-3xl font-medium tabular-nums">{{ achievements.filter((a) => a.unlocked).length }}<span class="text-base text-muted-foreground">/{{ achievements.length }}</span></p>
      <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mt-2">成就解锁</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  stats: Record<string, number>;
  achievements: Array<{ id: string; unlocked: boolean }>;
}>();
</script>