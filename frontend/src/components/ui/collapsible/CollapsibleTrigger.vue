<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import { CollapsibleTrigger } from 'reka-ui'
import { cn } from '@/lib/utils'

interface Props extends PrimitiveProps {
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  as: 'button',
})
</script>

<template>
  <CollapsibleTrigger as-child>
    <slot />
  </CollapsibleTrigger>
</template>
