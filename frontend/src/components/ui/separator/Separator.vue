<script setup lang="ts">
import { cn } from '@/lib/utils'

interface SeparatorProps {
  orientation?: 'horizontal' | 'vertical'
  decorative?: boolean
  label?: string
  class?: string
}

const props = withDefaults(defineProps<SeparatorProps>(), {
  orientation: 'horizontal',
  decorative: true,
})
</script>

<template>
  <div
    :class="
      cn(
        'shrink-0 bg-border',
        orientation === 'horizontal' ? 'h-px w-full' : 'h-full w-px',
        props.class,
      )
    "
    :role="decorative ? undefined : 'separator'"
    :aria-orientation="decorative ? undefined : orientation"
  >
    <span
      v-if="label"
      class="section-rule font-mono text-[10px] uppercase tracking-wider text-muted-foreground"
    >
      {{ label }}
    </span>
  </div>
</template>
