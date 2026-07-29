<script setup lang="ts">
import type { PopoverRootEmits, PopoverRootProps } from 'reka-ui'
import { PopoverRoot, useForwardPropsEmits } from 'reka-ui'

interface Props extends PopoverRootProps {
  class?: string
}

const props = defineProps<Props>()
const emits = defineEmits<PopoverRootEmits>()

const forward = useForwardPropsEmits(props, emits)
</script>

<template>
  <PopoverRoot v-bind="forward">
    <slot />
  </PopoverRoot>
</template>
