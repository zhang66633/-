<template>
  <router-view v-slot="{ Component, route }">
    <Transition name="page" mode="out-in">
      <component :is="Component" :key="route.path" />
    </Transition>
  </router-view>
</template>

<script setup lang="ts">
// Root component — delegates to router with enhanced page transitions
</script>

<style>
/* 页面过渡 — 翻书感：新页面淡入微上移，旧页面微缩小淡出 */
.page-enter-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.page-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-enter-from {
  opacity: 0;
  transform: translateY(8px) scale(0.995);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.985);
}

/* 减少动效偏好 */
@media (prefers-reduced-motion: reduce) {
  .page-enter-active,
  .page-leave-active {
    transition: none;
  }
  .page-enter-from,
  .page-leave-to {
    opacity: 1;
    transform: none;
  }
}
</style>
