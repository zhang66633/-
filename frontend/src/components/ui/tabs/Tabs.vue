<script setup lang="ts">
import type { TabsRootEmits, TabsRootProps } from 'reka-ui'
import { TabsRoot, useForwardPropsEmits } from 'reka-ui'

interface Props extends TabsRootProps {
  class?: string
}

const props = defineProps<Props>()
const emits = defineEmits<TabsRootEmits>()

const forward = useForwardPropsEmits(props, emits)
</script>

<template>
  <TabsRoot v-bind="forward" :class="props.class">
    <slot />
  </TabsRoot>
</template>
