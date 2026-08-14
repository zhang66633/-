<template>
  <div class="h-full overflow-y-auto">
    <div class="mx-auto max-w-4xl px-6 sm:px-10 py-12 sm:py-16">
      <p class="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground mb-4">§ 成长档案</p>
      <h1 class="font-display text-3xl sm:text-4xl font-medium tracking-tight">你的学习之旅</h1>

      <!-- 加载骨架屏 -->
      <div v-if="profileStore.loading" class="mt-6 space-y-6">
        <Skeleton class="h-20 w-full" />
        <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Skeleton v-for="i in 4" :key="i" class="h-24" />
        </div>
        <Skeleton class="h-40 w-full" />
        <Skeleton class="h-24 w-full" />
      </div>

      <!-- 加载失败(与「尚未开始学习」空态区分) -->
      <div v-else-if="failed" class="py-20 text-center">
        <p class="mb-3 text-sm text-muted-foreground">成长档案加载失败,请检查后端服务</p>
        <button
          class="cursor-pointer rounded-md border border-border px-4 py-1.5 text-sm transition-colors hover:bg-accent"
          @click="loadProgress"
        >
          重试
        </button>
      </div>

      <template v-else-if="progress">
        <!-- 今日学习 -->
        <div class="mt-6 rounded-md border border-border bg-card p-5">
          <div class="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
            <span class="font-medium">今日学习</span>
            <span v-if="todayEntry?.count" class="text-emerald-600">已学习 ✓</span>
            <span v-else class="text-muted-foreground">
              今天还没有学习记录,
              <RouterLink to="/learn" class="text-primary hover:underline">去学习工位开始吧</RouterLink>
            </span>
            <span class="font-mono text-xs text-muted-foreground">连续学习 {{ streak }} 天</span>
            <span class="font-mono text-xs text-muted-foreground">已完成 {{ completedUnits }}/{{ totalUnits }} 单元</span>
          </div>
        </div>

        <!-- 管家播报 -->
        <div class="mt-6 rounded-md border border-border bg-card p-5" v-bind="stagger.itemProps(0)">
          <div class="flex items-start gap-3">
            <span class="text-xl">📊</span>
            <div>
              <p class="text-sm font-medium mb-1">管家 本周播报</p>
              <p class="text-sm text-muted-foreground leading-relaxed">
                {{ progress.weekly?.message || "新的旅程从今天开始!" }}
              </p>
            </div>
          </div>
        </div>

        <!-- 数字大屏 -->
        <div class="mt-6">
          <StatHero :stats="progress.stats ?? {}" />
        </div>

        <!-- 学习进度 -->
        <div class="mt-6 rounded-md border border-border bg-card p-5">
          <p class="mb-2 text-sm font-medium">
            学习进度
            <span class="ml-2 font-mono text-xs text-muted-foreground">
              {{ completedUnits }}/{{ totalUnits }} 单元 · {{ progressPct }}%
            </span>
          </p>
          <div class="h-2 overflow-hidden rounded-full bg-muted">
            <div
              class="h-full rounded-full bg-primary transition-all duration-500"
              :style="{ width: progressPct + '%' }"
            />
          </div>
        </div>

        <!-- 已掌握知识点(角色掌握度) -->
        <div class="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
          <SkillRadar :skills="roleSkills" />
          <div class="rounded-md border border-border bg-card p-5">
            <p class="font-display text-base font-medium mb-4">各角色掌握度</p>
            <div v-for="s in roleSkills" :key="s.name" class="mb-3 last:mb-0">
              <div class="mb-1 flex items-center justify-between text-xs">
                <span class="text-muted-foreground">{{ s.name }}</span>
                <span class="font-mono">{{ s.value }}%</span>
              </div>
              <div class="h-1.5 overflow-hidden rounded-full bg-muted">
                <div
                  class="h-full rounded-full bg-primary transition-all duration-500"
                  :style="{ width: s.value + '%' }"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- AI 下一步建议 -->
        <div class="mt-6">
          <p class="font-display text-lg font-medium mb-3">🧭 AI 下一步建议</p>
          <NextRecommendationCard :role="recRole" @go="(id: string) => router.push(`/learn/${id}`)" />
        </div>

        <!-- 学习日历热力图 -->
        <div class="mt-6">
          <CalendarHeatmap :calendar="progress.calendar ?? []" />
        </div>

        <!-- 勋章墙 -->
        <div class="mt-10">
          <p class="font-display text-lg font-medium mb-4">🏆 勋章墙</p>
          <AchievementWall
            :achievements="progress.achievements ?? []"
            @ack="profileStore.ackAchievements"
          />
        </div>

        <!-- 待复习 -->
        <div v-if="reviewItems.length > 0" class="mt-8">
          <p class="font-display text-base font-medium mb-3">🧠 待复习</p>
          <ReviewList :items="reviewItems" @open="(id: string) => router.push(`/learn/${id}`)" />
        </div>
      </template>

      <!-- 空状态 -->
      <div v-else class="text-center py-20">
        <p class="text-2xl mb-3">🌱</p>
        <p class="text-sm text-muted-foreground">尚未开始学习。去学习工位开启第一条学习路径吧!</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// biome-ignore lint/style/useImportType: Vue 组件注册需要值导入,type-only 会导致运行期组件解析失败
import NextRecommendationCard from "@/components/learning/NextRecommendationCard.vue";
import AchievementWall from "@/components/progress/AchievementWall.vue";
import CalendarHeatmap from "@/components/progress/CalendarHeatmap.vue";
import ReviewList from "@/components/progress/ReviewList.vue";
// biome-ignore lint/style/useImportType: Vue 组件注册需要值导入,type-only 会导致运行期组件解析失败
import SkillRadar from "@/components/progress/SkillRadar.vue";
import StatHero from "@/components/progress/StatHero.vue";
import { Skeleton } from "@/components/ui/skeleton";
import { useStaggerReveal } from "@/composables/useStaggerReveal";
import { useLearningStore } from "@/stores/learning";
import { useProfileStore } from "@/stores/profile";
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";

const router = useRouter();
const profileStore = useProfileStore();
const learningStore = useLearningStore();
const progress = computed(() => profileStore.progress);
const stagger = useStaggerReveal({ count: 1, delay: 100 });
const failed = ref(false);

async function loadProgress() {
  failed.value = false;
  const ok = await profileStore.loadProgress();
  if (!ok) failed.value = true;
}
onMounted(loadProgress);

// ── 今日学习(数据严格来自现有字段,不编造学习时长) ──
const todayKey = computed(() => {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
});
const todayEntry = computed(() =>
  (progress.value?.calendar ?? []).find(
    (c: { date: string; count: number }) => c.date === todayKey.value,
  ),
);
const streak = computed(() => progress.value?.stats?.streak_days ?? 0);

// ── 学习进度 ──
const totalUnits = computed(() => progress.value?.stats?.total_units ?? 0);
const completedUnits = computed(
  () => progress.value?.stats?.completed_units ?? 0,
);
const progressPct = computed(() =>
  totalUnits.value > 0
    ? Math.round((completedUnits.value / totalUnits.value) * 100)
    : 0,
);

// ── 已掌握知识点(角色掌握度,复用孤儿组件 SkillRadar) ──
const roleSkills = computed(() => {
  const roles = progress.value?.roles ?? {};
  return [
    { name: "建模", value: Math.round(Number(roles.modeler) || 0) },
    { name: "编程", value: Math.round(Number(roles.programmer) || 0) },
    { name: "论文", value: Math.round(Number(roles.writer) || 0) },
  ];
});

// ── AI 推荐下一步(取掌握度最高的角色,兜底当前角色) ──
const recRole = computed(() => {
  const roles = progress.value?.roles ?? {};
  const entries = Object.entries(roles).filter(
    ([, v]) => typeof v === "number",
  );
  if (entries.length === 0) return learningStore.currentRole;
  entries.sort((a, b) => (b[1] as number) - (a[1] as number));
  return entries[0][0];
});

const reviewItems = computed(() => {
  const list = progress.value?.needs_review ?? [];
  return list.map((r: { skill_id: string; retention: number }) => ({
    id: r.skill_id,
    name: r.skill_id,
    retention: Math.round((r.retention ?? 0) * 100),
  }));
});
</script>
