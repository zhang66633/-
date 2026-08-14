<script setup lang="ts">
import type { PrimitiveProps } from "reka-ui";
import { PopoverTrigger } from "reka-ui";

interface Props extends PrimitiveProps {
  class?: string;
}

const props = withDefaults(defineProps<Props>(), {
  as: "button",
});
</script>

<template>
  <PopoverTrigger as-child>
    <slot />
  </PopoverTrigger>
</template>
