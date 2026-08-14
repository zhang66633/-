<template>
  <div class="flex items-center gap-2 text-sm">
    <span class="relative flex h-2.5 w-2.5" :title="statusText">
      <span
        v-if="backendStatus === 'connecting'"
        class="absolute inline-flex h-full w-full rounded-sm opacity-75 animate-ping bg-primary/50"
      />
      <span
        class="relative inline-flex h-2.5 w-2.5 rounded-sm border"
        :class="backendStatus === 'connected' ? 'border-primary bg-primary' : 'border-border bg-muted'"
      />
    </span>
    <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
      {{ statusText }}
    </span>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, onUnmounted, ref } from "vue";

const backendStatus = ref<"connected" | "disconnected" | "connecting">(
  "connecting",
);

const statusText = computed(() => {
  const map = {
    connected: "已连接",
    connecting: "连接中",
    disconnected: "未连接",
  };
  return map[backendStatus.value];
});

let timer: ReturnType<typeof setInterval> | null = null;

async function checkHealth() {
  try {
    const res = await axios.get("/api/health", { timeout: 3000 });
    backendStatus.value =
      res.data?.status === "ok" ? "connected" : "disconnected";
  } catch {
    backendStatus.value = "disconnected";
  }
}

onMounted(() => {
  checkHealth();
  timer = setInterval(checkHealth, 15000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>
