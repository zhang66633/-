<script setup lang="ts">
import { cn } from '@/lib/utils'

interface SkeletonProps {
  class?: string
}

const props = defineProps<SkeletonProps>()
</script>

<template>
  <div
    :class="
      cn(
        'animate-pulse rounded-md bg-muted',
        'relative overflow-hidden',
        // shimmer 扫光效果
        'after:absolute after:inset-0 after:translate-x-[-100%]',
        'after:animate-[shimmer_1.5s_infinite]',
        'after:bg-gradient-to-r after:from-transparent after:via-white/5 after:to-transparent',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>
