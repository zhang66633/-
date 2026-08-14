<script setup lang="ts">
import type { HoverCardRootEmits, HoverCardRootProps } from "reka-ui";
import { HoverCardRoot, useForwardPropsEmits } from "reka-ui";

interface Props extends HoverCardRootProps {
  class?: string;
}

const props = defineProps<Props>();
const emits = defineEmits<HoverCardRootEmits>();

const forward = useForwardPropsEmits(props, emits);
</script>

<template>
  <HoverCardRoot v-bind="forward" :open-delay="200" :close-delay="100">
    <slot />
  </HoverCardRoot>
</template>
