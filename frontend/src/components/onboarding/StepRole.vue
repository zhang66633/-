<template>
  <div>
    <h2 class="text-[19px] font-semibold leading-snug tracking-tight text-foreground">选择你的角色</h2>
    <p class="mt-1.5 text-sm text-muted-foreground">数模竞赛三人团队,你想担任哪个角色?</p>
    <div class="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
      <button
        v-for="r in roles"
        :key="r.value"
        type="button"
        class="relative cursor-pointer rounded-xl border p-4 text-left transition-all duration-150"
        :class="modelValue === r.value
          ? 'border-primary bg-primary/5 ring-1 ring-primary/30'
          : 'border-border bg-card hover:border-muted-foreground/30 hover:bg-accent/40'"
        @click="$emit('update:modelValue', r.value)"
      >
        <span
          v-if="modelValue === r.value"
          class="absolute right-2.5 top-2.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-primary-foreground"
        >
          <Check class="h-3 w-3" />
        </span>
        <span class="block text-2xl leading-none">{{ r.emoji }}</span>
        <span class="mt-2.5 block text-sm font-medium" :class="modelValue === r.value ? 'text-foreground' : 'text-foreground'">{{ r.label }}</span>
        <span class="mt-1 block text-xs leading-relaxed text-muted-foreground">{{ r.desc }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AgentRole } from "@/stores/onboarding";
import { Check } from "lucide-vue-next";

defineProps<{ modelValue: AgentRole }>();
defineEmits<{ "update:modelValue": [value: AgentRole] }>();

const roles = [
  {
    value: "modeler" as AgentRole,
    label: "建模手",
    emoji: "🧮",
    desc: "将实际问题转化为数学模型,选择合适的方法",
  },
  {
    value: "programmer" as AgentRole,
    label: "编程手",
    emoji: "💻",
    desc: "用代码实现模型,处理数据,计算结果",
  },
  {
    value: "writer" as AgentRole,
    label: "论文手",
    emoji: "✍️",
    desc: "撰写摘要、组织论文、设计图表",
  },
];
</script>
