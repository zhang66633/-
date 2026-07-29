<script setup lang="ts">
import type { CollapsibleRootEmits, CollapsibleRootProps } from 'reka-ui'
import { CollapsibleRoot, useForwardPropsEmits } from 'reka-ui'

interface Props extends CollapsibleRootProps {
  class?: string
}

const props = defineProps<Props>()
const emits = defineEmits<CollapsibleRootEmits>()

const forward = useForwardPropsEmits(props, emits)
</script>

<template>
  <CollapsibleRoot v-bind="forward" :class="props.class">
    <slot />
  </CollapsibleRoot>
</template>
