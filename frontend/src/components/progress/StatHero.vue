<template>
  <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
    <div
      v-for="(tile, i) in tiles"
      :key="tile.label"
      class="rounded-md border border-border bg-card p-4"
      v-bind="stagger.itemProps(i)"
    >
      <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        {{ tile.label }}
      </p>
      <p class="mt-1.5 font-display text-3xl font-medium tabular-nums text-foreground">
        {{ tile.display }}
        <span v-if="tile.suffix" class="ml-0.5 text-base text-muted-foreground">{{ tile.suffix }}</span>
      </p>
      <p class="mt-1 text-[11px] text-muted-foreground">{{ tile.sub }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useCountAnimation } from "@/composables/useCountAnimation";
import { useStaggerReveal } from "@/composables/useStaggerReveal";
import { computed } from "vue";

const props = defineProps<{
  stats: {
    total_answers?: number;
    accuracy?: number;
    streak_days?: number;
    unlocked_achievements?: number;
    total_achievements?: number;
    completed_units?: number;
    total_units?: number;
    wrong_questions?: number;
  };
}>();

const stagger = useStaggerReveal({ count: 4, delay: 80 });

const anim = {
  total: useCountAnimation(() => props.stats.total_answers ?? 0),
  accuracy: useCountAnimation(() => props.stats.accuracy ?? 0),
  streak: useCountAnimation(() => props.stats.streak_days ?? 0),
  medals: useCountAnimation(() => props.stats.unlocked_achievements ?? 0),
};

const tiles = computed(() => [
  {
    label: "累计刷题",
    display: anim.total.display.value,
    suffix: "",
    sub: `完成单元 ${props.stats.completed_units ?? 0}/${props.stats.total_units ?? 61}`,
  },
  {
    label: "正确率",
    display: anim.accuracy.display.value,
    suffix: "%",
    sub: `错题本待征服 ${props.stats.wrong_questions ?? 0} 道`,
  },
  {
    label: "连续学习",
    display: anim.streak.display.value,
    suffix: "天",
    sub: "保持住,习惯正在养成",
  },
  {
    label: "勋章",
    display: anim.medals.display.value,
    suffix: `/${props.stats.total_achievements ?? 12}`,
    sub: "点亮整面勋章墙",
  },
]);
</script>
