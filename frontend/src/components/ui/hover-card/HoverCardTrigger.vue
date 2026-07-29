<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import { HoverCardTrigger } from 'reka-ui'

interface Props extends PrimitiveProps {
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  as: 'a',
})
</script>

<template>
  <HoverCardTrigger as-child>
    <slot />
  </HoverCardTrigger>
</template>
