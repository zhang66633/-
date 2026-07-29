<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import { DropdownMenuTrigger } from 'reka-ui'

interface Props extends PrimitiveProps {
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  as: 'button',
})
</script>

<template>
  <DropdownMenuTrigger as-child>
    <slot />
  </DropdownMenuTrigger>
</template>
