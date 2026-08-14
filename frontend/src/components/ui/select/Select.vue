<script setup lang="ts">
import type { SelectRootEmits, SelectRootProps } from "reka-ui";
import { SelectRoot, useForwardPropsEmits } from "reka-ui";

interface Props extends SelectRootProps {
  class?: string;
}

const props = defineProps<Props>();
const emits = defineEmits<SelectRootEmits>();

const forward = useForwardPropsEmits(props, emits);
</script>

<template>
  <SelectRoot v-bind="forward">
    <slot />
  </SelectRoot>
</template>
