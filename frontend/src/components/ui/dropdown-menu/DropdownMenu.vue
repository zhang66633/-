<script setup lang="ts">
import type { DropdownMenuRootEmits, DropdownMenuRootProps } from 'reka-ui'
import { DropdownMenuRoot, useForwardPropsEmits } from 'reka-ui'

interface Props extends DropdownMenuRootProps {
  class?: string
}

const props = defineProps<Props>()
const emits = defineEmits<DropdownMenuRootEmits>()

const forward = useForwardPropsEmits(props, emits)
</script>

<template>
  <DropdownMenuRoot v-bind="forward">
    <slot />
  </DropdownMenuRoot>
</template>
