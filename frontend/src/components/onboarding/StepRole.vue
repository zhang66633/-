<template>
  <div>
    <h2 class="font-display text-xl font-medium mb-1">选择你的角色</h2>
    <p class="text-sm text-muted-foreground mb-5">数模竞赛三人团队，你想担任哪个角色？</p>
    <div class="grid grid-cols-3 gap-3">
      <button
        v-for="r in roles"
        :key="r.value"
        class="flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-all"
        :class="modelValue === r.value
          ? 'border-primary bg-primary/5 shadow-sm'
          : 'border-border hover:border-muted-foreground/30 hover:bg-accent/30'"
        @click="$emit('update:modelValue', r.value)"
      >
        <span class="text-3xl">{{ r.emoji }}</span>
        <span class="text-sm font-medium">{{ r.label }}</span>
        <span class="text-[10px] text-muted-foreground text-center leading-relaxed">{{ r.desc }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AgentRole } from "@/stores/onboarding";

defineProps<{ modelValue: AgentRole }>();
defineEmits<{ "update:modelValue": [value: AgentRole] }>();

const roles = [
  {
    value: "modeler" as AgentRole,
    label: "建模手",
    emoji: "🧮",
    desc: "将实际问题转化为数学模型，选择合适的方法",
  },
  {
    value: "programmer" as AgentRole,
    label: "编程手",
    emoji: "💻",
    desc: "用代码实现模型，处理数据，计算结果",
  },
  {
    value: "writer" as AgentRole,
    label: "论文手",
    emoji: "✍️",
    desc: "撰写摘要、组织论文、设计图表",
  },
];
</script>