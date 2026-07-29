<script setup lang="ts">
import { SelectContent as RekaSelectContent, SelectPortal } from 'reka-ui'
import { cn } from '@/lib/utils'

interface Props {
  class?: string
}

const props = defineProps<Props>()
</script>

<template>
  <SelectPortal>
    <RekaSelectContent
      :class="
        cn(
          'z-50 max-h-96 min-w-[8rem] overflow-hidden rounded-md border border-border bg-popover text-popover-foreground shadow-md',
          'data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95',
          'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
          props.class,
        )
      "
      :side-offset="4"
      align="start"
    >
      <slot />
    </RekaSelectContent>
  </SelectPortal>
</template>
