<script setup lang="ts">
import { HoverCardContent, HoverCardPortal } from 'reka-ui'
import { cn } from '@/lib/utils'

interface Props {
  class?: string
  side?: 'top' | 'right' | 'bottom' | 'left'
  align?: 'start' | 'center' | 'end'
}

const props = withDefaults(defineProps<Props>(), {
  side: 'bottom',
  align: 'center',
})
</script>

<template>
  <HoverCardPortal>
    <HoverCardContent
      :side="side"
      :align="align"
      :side-offset="4"
      :class="
        cn(
          'z-50 w-64 rounded-md border border-border bg-popover p-4 text-popover-foreground shadow-md outline-none',
          'data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95',
          props.class,
        )
      "
    >
      <slot />
    </HoverCardContent>
  </HoverCardPortal>
</template>
