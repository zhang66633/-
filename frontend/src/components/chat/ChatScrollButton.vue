<script setup lang="ts">
import { ArrowDown } from "lucide-vue-next";

defineEmits<{
  click: [];
}>();
</script>

<template>
  <Transition name="fade">
    <button
      class="absolute bottom-24 right-6 h-9 w-9 rounded-md border border-border bg-background/80 backdrop-blur flex items-center justify-center hover:bg-accent transition-colors z-10"
      @click="$emit('click')"
    >
      <ArrowDown class="h-4 w-4" />
    </button>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
