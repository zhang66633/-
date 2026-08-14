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
          <ReviewList :items="reviewItems" />
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
import AchievementWall from "@/components/progress/AchievementWall.vue";
import CalendarHeatmap from "@/components/progress/CalendarHeatmap.vue";
import ReviewList from "@/components/progress/ReviewList.vue";
import StatHero from "@/components/progress/StatHero.vue";
import { useStaggerReveal } from "@/composables/useStaggerReveal";
import { useProfileStore } from "@/stores/profile";
import { Loader2 } from "lucide-vue-next";
import { computed, onMounted } from "vue";

const profileStore = useProfileStore();
const progress = computed(() => profileStore.progress);
const stagger = useStaggerReveal({ count: 1, delay: 100 });

const reviewItems = computed(() => {
  const list = progress.value?.needs_review ?? [];
  return list.map((r: { skill_id: string; retention: number }) => ({
    id: r.skill_id,
    name: r.skill_id,
    retention: Math.round((r.retention ?? 0) * 100),
  }));
});

onMounted(() => {
  profileStore.loadProgress();
});
</script>
