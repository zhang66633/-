<template>
  <div class="flex items-center justify-between border-b px-4 py-2 shrink-0 bg-muted/20">
    <span
      class="min-w-0 truncate text-sm font-medium"
      :class="title ? 'text-foreground' : 'text-muted-foreground'"
    >
      {{ title || "新对话" }}
    </span>
    <div class="flex shrink-0 items-center gap-1">
      <button
        v-if="(messagesCount ?? 0) > 0"
        class="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
        title="清空当前会话"
        @click="$emit('clear')"
      >
        <Eraser class="h-4 w-4" />
      </button>
      <button
        class="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
        title="新建对话"
        @click="$emit('new-session')"
      >
        <Plus class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Eraser, Plus } from "lucide-vue-next";

defineProps<{
  title?: string;
  messagesCount?: number;
}>();

defineEmits<{
  clear: [];
  "new-session": [];
}>();
</script>
