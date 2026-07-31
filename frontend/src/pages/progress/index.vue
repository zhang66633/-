<template>
  <div class="h-full overflow-y-auto">
    <div class="mx-auto max-w-4xl px-6 sm:px-10 py-12 sm:py-16">
      <p class="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground mb-4">§ 成长档案</p>
      <h1 class="font-display text-3xl sm:text-4xl font-medium tracking-tight">你的学习之旅</h1>

      <!-- 加载中 -->
      <div v-if="profileStore.loading" class="flex items-center justify-center py-20">
        <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
      </div>

      <template v-else-if="progress">
        <!-- 管家播报 -->
        <div class="mt-6 rounded-md border border-border bg-card p-5">
          <div class="flex items-start gap-3">
            <span class="text-xl">📊</span>
            <div>
              <p class="text-sm font-medium mb-1">管家 本周播报</p>
              <p class="text-sm text-muted-foreground leading-relaxed">
                本周你学了 <strong>{{ progress.stats?.completed_units ?? 0 }}</strong> 个单元，
                连续学习 <strong>{{ progress.stats?.streak_days ?? 0 }}</strong> 天。
                {{ progress.weakest?.length > 0 ? `重点关注：${progress.weakest[0].name || '基础知识'}` : '继续保持！' }}
              </p>
            </div>
          </div>
        </div>

        <!-- 学习统计卡片 -->
        <StatsDashboard :stats="progress.stats ?? {}" :achievements="progress.achievements ?? []" />

        <!-- 技能雷达 -->
        <div class="mt-10 grid grid-cols-2 gap-6">
          <SkillRadar :skills="skillData" />
          <ReviewList :items="reviewItems" />
        </div>

        <!-- 成就 -->
        <div class="mt-10">
          <p class="font-display text-lg font-medium mb-4">🏆 成就</p>
          <div class="grid grid-cols-4 gap-4">
            <div
              v-for="ach in progress.achievements ?? achievementsFallback"
              :key="ach.id"
              class="rounded-md border border-border p-4 text-center transition-colors"
              :class="ach.unlocked ? 'bg-card border-primary/30' : 'bg-muted/20 opacity-50'"
            >
              <p class="text-2xl mb-1">{{ ach.unlocked ? (ach.icon ?? '⭐') : '⬜' }}</p>
              <p class="text-xs font-medium" :class="ach.unlocked ? 'text-foreground' : 'text-muted-foreground'">{{ ach.name }}</p>
              <p class="text-[10px] text-muted-foreground mt-1">{{ ach.desc }}</p>
            </div>
          </div>
        </div>
      </template>

      <!-- 空状态 -->
      <div v-else class="text-center py-20">
        <p class="text-sm text-muted-foreground">尚未开始学习。去学习工位开启第一条学习路径吧！</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { Loader2 } from "lucide-vue-next";
import StatsDashboard from "@/components/progress/StatsDashboard.vue";
import SkillRadar from "@/components/progress/SkillRadar.vue";
import ReviewList from "@/components/progress/ReviewList.vue";
import { useProfileStore } from "@/stores/profile";

const profileStore = useProfileStore();
const progress = computed(() => profileStore.progress);

const skillData = computed(() => {
  if (!progress.value) return [];
  return [
    { name: "建模", value: Math.round((progress.value.modeler ?? 0) * 100) },
    { name: "编程", value: Math.round((progress.value.programmer ?? 0) * 100) },
    { name: "写作", value: Math.round((progress.value.writer ?? 0) * 100) },
  ];
});

const reviewItems = computed(() => {
  if (!progress.value?.needs_review) return [];
  return progress.value.needs_review.map((r: any) => ({
    id: r.skill_id,
    name: r.skill_id,
    retention: Math.round((r.retention ?? 0) * 100),
  }));
});

const achievementsFallback = [
  { id: "1", name: "初出茅庐", desc: "完成第一次建模练习", icon: "🌱", unlocked: false },
  { id: "2", name: "坚持不懈", desc: "连续学习 7 天", icon: "🔥", unlocked: false },
  { id: "3", name: "方法大师", desc: "掌握 10 种建模方法", icon: "🧠", unlocked: false },
  { id: "4", name: "实战达人", desc: "完成一次完整实战", icon: "⚔️", unlocked: false },
  { id: "5", name: "代码高手", desc: "完成 10 道编程练习", icon: "💻", unlocked: false },
  { id: "6", name: "论文新星", desc: "完成一次论文写作练习", icon: "📄", unlocked: false },
  { id: "7", name: "全能选手", desc: "三个角色各完成 5 个单元", icon: "🌟", unlocked: false },
  { id: "8", name: "竞赛勇士", desc: "在实战中取得 A 级评价", icon: "🏆", unlocked: false },
];

onMounted(() => {
  profileStore.loadProgress();
});
</script>