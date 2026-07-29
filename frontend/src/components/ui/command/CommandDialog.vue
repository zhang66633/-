<script setup lang="ts">
import { cn } from '@/lib/utils'

interface Props {
  class?: string
  shouldFilter?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  shouldFilter: true,
})
</script>

<template>
  <div :class="cn('flex h-full w-full flex-col overflow-hidden rounded-md bg-popover text-popover-foreground', props.class)">
    <slot />
  </div>
</template>
