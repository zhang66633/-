<script setup lang="ts">
import { cn } from '@/lib/utils'

interface AvatarFallbackProps {
  class?: string
  delayMs?: number
}

const props = withDefaults(defineProps<AvatarFallbackProps>(), {
  delayMs: 0,
})
</script>

<template>
  <span
    :class="
      cn(
        'flex h-full w-full items-center justify-center rounded-sm bg-muted font-display text-sm text-muted-foreground',
        props.class,
      )
    "
  >
    <slot />
  </span>
</template>
