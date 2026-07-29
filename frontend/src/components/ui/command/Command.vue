<script setup lang="ts">
import type { ComboboxRootEmits, ComboboxRootProps } from 'reka-ui'
import { ComboboxRoot, useForwardPropsEmits } from 'reka-ui'

interface Props extends ComboboxRootProps {
  class?: string
}

const props = defineProps<Props>()
const emits = defineEmits<ComboboxRootEmits>()

const forward = useForwardPropsEmits(props, emits)
</script>

<template>
  <ComboboxRoot v-bind="forward" :class="props.class">
    <slot />
  </ComboboxRoot>
</template>
