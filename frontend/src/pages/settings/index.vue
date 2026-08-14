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

        <!-- 沙箱执行模式 -->
        <div class="rounded-lg border p-5">
          <h2 class="font-medium mb-1">代码执行沙箱</h2>
          <p class="text-xs text-muted-foreground mb-3">当前执行 Python 代码的隔离模式</p>
          <div v-if="sandbox" class="flex items-center gap-2">
            <span
              class="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium"
              :class="sandbox.backend === 'docker'
                ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800'
                : 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800'"
              :title="sandbox.note"
            >
              <Box class="h-3.5 w-3.5" />
              {{ sandbox.backend === "docker" ? "Docker 硬隔离" : "subprocess 回退" }}
            </span>
            <span class="text-xs text-muted-foreground">{{ sandbox.note }}</span>
          </div>
          <p v-else class="text-xs text-muted-foreground">无法获取沙箱状态（后端未启动？）</p>
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
import { type SandboxStatus, getSandboxStatus } from "@/apis/sandboxApi";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/composables/useTheme";
import { ArrowLeft, Box, Key, Moon, Sun } from "lucide-vue-next";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const { isDark, setTheme } = useTheme();

const sandbox = ref<SandboxStatus | null>(null);

onMounted(async () => {
  try {
    sandbox.value = await getSandboxStatus();
  } catch {
    sandbox.value = null; // 后端不可用则隐藏，不打扰
  }
});
</script>
