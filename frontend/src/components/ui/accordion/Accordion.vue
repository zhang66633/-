<script setup lang="ts">
import type { AccordionRootEmits, AccordionRootProps } from 'reka-ui'
import { AccordionRoot, useForwardPropsEmits } from 'reka-ui'

interface Props extends AccordionRootProps {
  class?: string
}

const props = defineProps<Props>()
const emits = defineEmits<AccordionRootEmits>()

const forward = useForwardPropsEmits(props, emits)
</script>

<template>
  <AccordionRoot v-bind="forward" :class="props.class">
    <slot />
  </AccordionRoot>
</template>
