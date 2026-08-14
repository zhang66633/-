<template>
  <button
    type="button"
    class="inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    :aria-label="theme === 'dark' ? '切换到明亮模式' : '切换到暗色模式'"
    @click="toggle"
  >
    <Sun v-if="theme === 'dark'" class="h-4 w-4" />
    <Moon v-else class="h-4 w-4" />
  </button>
</template>

<script setup lang="ts">
import { useTheme } from "@/composables/useTheme";
import { Moon, Sun } from "lucide-vue-next";

const { theme, toggle } = useTheme();
</script>
