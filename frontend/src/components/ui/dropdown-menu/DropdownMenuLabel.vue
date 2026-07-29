<script setup lang="ts">
import { DropdownMenuLabel } from 'reka-ui'
import { cn } from '@/lib/utils'

interface Props {
  class?: string
  inset?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  inset: false,
})
</script>

<template>
  <DropdownMenuLabel
    :class="
      cn(
        'px-2 py-1.5 text-xs font-medium text-muted-foreground',
        props.inset && 'pl-8',
        props.class,
      )
    "
  >
    <slot />
  </DropdownMenuLabel>
</template>
