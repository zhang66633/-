<template>
  <div class="rounded-md border border-border bg-card p-5">
    <p class="font-display text-base font-medium mb-4">技能掌握度</p>
    <div class="flex items-center justify-center py-2">
      <svg viewBox="-50 -50 100 100" class="w-48 h-48">
        <!-- 背景网格 -->
        <circle v-for="r in 3" :key="r" :r="r * 16" fill="none" stroke="var(--border)" stroke-width="0.5" />
        <line v-for="a in 3" :key="a" :x1="0" :y1="0" :x2="Math.cos((a * 120 - 90) * Math.PI / 180) * 48" :y2="Math.sin((a * 120 - 90) * Math.PI / 180) * 48" stroke="var(--border)" stroke-width="0.5" />

        <!-- 数据多边形 -->
        <polygon
          :points="polygonPoints"
          fill="var(--primary)"
          fill-opacity="0.15"
          stroke="var(--primary)"
          stroke-width="1.5"
        />

        <!-- 数据点 -->
        <circle
          v-for="(p, i) in points"
          :key="i"
          :cx="p.x"
          :cy="p.y"
          r="3"
          fill="var(--primary)"
        />

        <!-- 标签 -->
        <text
          v-for="(s, i) in skills"
          :key="s.name"
          :x="Math.cos((i * 120 - 90) * Math.PI / 180) * 56"
          :y="Math.sin((i * 120 - 90) * Math.PI / 180) * 56"
          text-anchor="middle"
          dominant-baseline="middle"
          fill="currentColor"
          font-size="10"
          class="fill-muted-foreground"
        >
          {{ s.name }} {{ s.value }}%
        </text>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  skills: Array<{ name: string; value: number }>;
}>();

const points = computed(() =>
  props.skills.map((s, i) => {
    const angle = ((i * 120 - 90) * Math.PI) / 180;
    const r = (s.value / 100) * 48;
    return { x: Math.cos(angle) * r, y: Math.sin(angle) * r };
  }),
);

const polygonPoints = computed(() =>
  points.value.map((p) => `${p.x},${p.y}`).join(" "),
);
</script>