<template>
  <div class="flex h-full bg-background">
    <div class="flex-1 flex flex-col">
      <!-- 顶部 -->
      <div class="flex items-center justify-between border-b px-6 py-3">
        <div class="flex items-center gap-3">
          <span class="font-display text-lg font-medium">训练场</span>
          <span class="font-mono text-[10px] text-muted-foreground">· 智能体出题 + 批改</span>
        </div>
      </div>

      <!-- Tab 切换 -->
      <div class="flex items-center gap-6 border-b px-6">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          class="relative py-3 text-sm transition-colors"
          :class="activeTab === tab.value ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground'"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
          <span v-if="activeTab === tab.value" class="absolute left-0 right-0 -bottom-px h-px bg-primary" />
        </button>
      </div>

      <!-- 内容区 -->
      <div class="flex-1 overflow-y-auto p-6">
        <!-- 每日推荐 -->
        <div v-if="activeTab === 'daily'" class="max-w-2xl mx-auto">
          <div class="rounded-lg border border-border p-6">
            <div class="flex items-center gap-2 mb-4">
              <span class="text-lg">🔬</span>
              <span class="font-display font-medium">检验员 今日推荐</span>
            </div>
            <p class="text-sm text-muted-foreground mb-4">
              基于你当前的学习进度，今天为你准备了 3 道练习题。
              完成练习后智能体会给出评估和建议。
            </p>
            <div class="space-y-3">
              <div v-for="i in 3" :key="i" class="rounded-md border border-border p-4 cursor-pointer hover:border-primary/40 transition-colors">
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-mono text-[10px] text-primary">练习 {{ i }}</span>
                  <span class="font-mono text-[10px] text-muted-foreground">· 建模题</span>
                </div>
                <p class="text-sm">[题目占位] 基于你刚学的知识点，智能体将生成一道针对性练习题</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 错题回顾 -->
        <div v-if="activeTab === 'mistakes'" class="max-w-2xl mx-auto">
          <div class="text-center py-16 text-muted-foreground text-sm">
            暂无错题记录。完成练习后，错题会自动出现在这里。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const activeTab = ref("daily");
const tabs = [
  { label: "每日推荐", value: "daily" },
  { label: "错题回顾", value: "mistakes" },
];
</script>
