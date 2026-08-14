<script setup lang="ts">
import { type ToastType, useToast } from "@/composables/useToast";
import { AlertCircle, CheckCircle2, Info } from "lucide-vue-next";

const { toasts } = useToast();

const iconOf: Record<ToastType, typeof Info> = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};
const barOf: Record<ToastType, string> = {
  success: "bg-emerald-500",
  error: "bg-destructive",
  info: "bg-primary",
};
</script>

<template>
  <Teleport to="body">
    <div class="pointer-events-none fixed bottom-6 right-6 z-[60] flex flex-col items-end gap-2">
      <TransitionGroup name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="pointer-events-auto flex items-center gap-2.5 rounded-md border border-border bg-card px-4 py-2.5 text-sm text-foreground shadow-md"
        >
          <span class="h-4 w-1 shrink-0 rounded-full" :class="barOf[t.type]" />
          <component :is="iconOf[t.type]" class="h-4 w-4 shrink-0 text-muted-foreground" />
          <span>{{ t.message }}</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(4px);
}
.toast-leave-to {
  opacity: 0;
}
@media (prefers-reduced-motion: reduce) {
  .toast-enter-active,
  .toast-leave-active {
    transition: none;
  }
}
</style>
