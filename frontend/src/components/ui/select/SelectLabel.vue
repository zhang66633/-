<script setup lang="ts">
import { SelectLabel } from 'reka-ui'
import { cn } from '@/lib/utils'

interface Props {
  class?: string
}

const props = defineProps<Props>()
</script>

<template>
  <SelectLabel :class="cn('py-1.5 pl-8 pr-2 text-xs font-medium text-muted-foreground', props.class)">
    <slot />
  </SelectLabel>
</template>
