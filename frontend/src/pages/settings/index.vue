<template>
  <div class="flex h-full flex-col overflow-hidden">
    <header class="flex items-center gap-3 border-b px-6 py-4 shrink-0">
      <Button variant="ghost" size="icon" @click="router.back()">
        <ArrowLeft class="h-4 w-4" />
      </Button>
      <div>
        <h1 class="text-lg font-semibold">设置</h1>
        <p class="text-xs text-muted-foreground">个性化配置</p>
      </div>
    </header>

    <div class="flex-1 overflow-y-auto overflow-x-hidden p-6">
      <div class="max-w-2xl space-y-6">
        <!-- 主题 -->
        <div class="rounded-lg border p-5">
          <h2 class="font-medium mb-1">主题</h2>
          <p class="text-xs text-muted-foreground mb-4">切换界面外观</p>
          <div class="grid grid-cols-2 gap-3">
            <button
              class="flex items-center gap-3 rounded-md border p-3 hover:bg-accent/50 transition-colors"
              :class="!isDark && 'border-primary'"
              @click="setTheme('light')"
            >
              <Sun class="h-4 w-4" />
              <span class="text-sm">浅色</span>
            </button>
            <button
              class="flex items-center gap-3 rounded-md border p-3 hover:bg-accent/50 transition-colors"
              :class="isDark && 'border-primary'"
              @click="setTheme('dark')"
            >
              <Moon class="h-4 w-4" />
              <span class="text-sm">深色</span>
            </button>
          </div>
        </div>

        <!-- API Key 快捷入口 -->
        <div class="rounded-lg border p-5">
          <h2 class="font-medium mb-1">API Key</h2>
          <p class="text-xs text-muted-foreground mb-4">管理大模型调用凭证</p>
          <Button variant="outline" @click="router.push('/apikeys')">
            <Key class="h-4 w-4 mr-1" />
            前往管理
          </Button>
        </div>

        <!-- 关于 -->
        <div class="rounded-lg border p-5">
          <h2 class="font-medium mb-1">关于</h2>
          <p class="text-xs text-muted-foreground">MathModelAgent — 数学建模多智能体辅助系统</p>
          <p class="text-xs text-muted-foreground mt-1">Version 0.1.0</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { useTheme } from "@/composables/useTheme";
import { ArrowLeft, Key, Moon, Sun } from "lucide-vue-next";
import { useRouter } from "vue-router";

const router = useRouter();
const { isDark, setTheme } = useTheme();
</script>
