<script setup lang="ts">
import { Brain, Square } from "lucide-vue-next";

withDefaults(defineProps<{
  cancellable?: boolean;
  cancelling?: boolean;
}>(), {
  cancellable: false,
  cancelling: false,
});

defineEmits<{
  cancel: [];
}>();
</script>

<template>
  <div class="flex items-center gap-3 pl-1 py-2">
    <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border border-border">
      <Brain class="h-4 w-4 text-muted-foreground" />
    </div>
    <div class="flex items-center gap-1.5 rounded-md border border-border bg-background px-4 py-3">
      <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mr-2">思考中</span>
      <span class="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-bounce" style="animation-delay: 0ms" />
      <span class="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-bounce" style="animation-delay: 150ms" />
      <span class="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-bounce" style="animation-delay: 300ms" />
    </div>
    <button
      v-if="cancellable"
      class="ml-2 inline-flex h-7 items-center gap-1 rounded-md border border-border bg-background px-2.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground transition-colors disabled:opacity-50"
      :disabled="cancelling"
      @click="$emit('cancel')"
    >
      <Square class="h-3 w-3" />
      <span>{{ cancelling ? "停止中…" : "停止" }}</span>
    </button>
  </div>
</template>
