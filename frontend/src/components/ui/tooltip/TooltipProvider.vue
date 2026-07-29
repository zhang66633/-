<script setup lang="ts">
import { TooltipProvider } from 'reka-ui'
</script>

<template>
  <TooltipProvider :delay-duration="200" :skip-delay-duration="300">
    <slot />
  </TooltipProvider>
</template>
