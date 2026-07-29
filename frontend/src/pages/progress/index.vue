<template>
  <div class="h-full overflow-y-auto bg-grid-paper">
    <div class="mx-auto max-w-4xl px-6 sm:px-10 py-12 sm:py-16">
      <p class="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground mb-4">§ 成长档案</p>
      <h1 class="font-display text-3xl sm:text-4xl font-medium tracking-tight">你的学习之旅</h1>

      <!-- 管家播报 -->
      <div class="mt-6 rounded-md border border-border bg-card p-5">
        <div class="flex items-start gap-3">
          <span class="text-xl">📊</span>
          <div>
            <p class="text-sm font-medium mb-1">管家 本周播报</p>
            <p class="text-sm text-muted-foreground leading-relaxed">
              本周你学了 0 个新方法，做了 0 道练习题。
              开始你的第一条学习路径，让数据慢慢积累起来吧！
            </p>
          </div>
        </div>
      </div>

      <!-- 学习统计卡片 -->
      <div class="grid grid-cols-4 gap-4 mt-8">
        <div class="rounded-md border border-border bg-card p-4 text-center">
          <p class="font-mono text-3xl font-medium tabular-nums">0</p>
          <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mt-2">连续学习天数</p>
        </div>
        <div class="rounded-md border border-border bg-card p-4 text-center">
          <p class="font-mono text-3xl font-medium tabular-nums">0h</p>
          <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mt-2">累计学习时长</p>
        </div>
        <div class="rounded-md border border-border bg-card p-4 text-center">
          <p class="font-mono text-3xl font-medium tabular-nums">0/45</p>
          <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mt-2">完成单元</p>
        </div>
        <div class="rounded-md border border-border bg-card p-4 text-center">
          <p class="font-mono text-3xl font-medium tabular-nums">0</p>
          <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mt-2">成就解锁</p>
        </div>
      </div>

      <!-- 学习日历 -->
      <div class="mt-10">
        <p class="font-display text-lg font-medium mb-4">学习日历</p>
        <div class="rounded-md border border-border bg-card p-6">
          <p class="text-sm text-muted-foreground text-center py-8">
            开始学习后，这里将显示你的月度学习热力图（类似 GitHub 贡献图）
          </p>
        </div>
      </div>

      <!-- 成就系统 -->
      <div class="mt-10">
        <p class="font-display text-lg font-medium mb-4">🏆 成就</p>
        <div class="grid grid-cols-4 gap-4">
          <div
            v-for="achievement in achievements"
            :key="achievement.name"
            class="rounded-md border border-border p-4 text-center transition-colors"
            :class="achievement.unlocked ? 'bg-card border-primary/30' : 'bg-muted/20 opacity-50'"
          >
            <p class="text-2xl mb-1">{{ achievement.unlocked ? '⭐' : '⬜' }}</p>
            <p class="text-xs font-medium" :class="achievement.unlocked ? 'text-foreground' : 'text-muted-foreground'">{{ achievement.name }}</p>
            <p class="text-[10px] text-muted-foreground mt-1">{{ achievement.desc }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const achievements = ref([
  { name: "初出茅庐", desc: "完成第一次建模练习", unlocked: false },
  { name: "坚持不懈", desc: "连续学习 7 天", unlocked: false },
  { name: "方法大师", desc: "掌握 10 种建模方法", unlocked: false },
  { name: "实战达人", desc: "完成一次完整实战", unlocked: false },
  { name: "代码高手", desc: "完成 10 道编程练习", unlocked: false },
  { name: "论文新星", desc: "完成一次论文写作练习", unlocked: false },
  { name: "全能选手", desc: "三个角色各完成 5 个单元", unlocked: false },
  { name: "竞赛勇士", desc: "在实战中取得 A 级评价", unlocked: false },
]);
</script>
