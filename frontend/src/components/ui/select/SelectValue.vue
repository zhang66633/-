<script setup lang="ts">
import type { PrimitiveProps } from "reka-ui";
import { Primitive, SelectValue } from "reka-ui";

interface Props extends PrimitiveProps {
  placeholder?: string;
}

const props = withDefaults(defineProps<Props>(), {
  as: "span",
});
</script>

<template>
  <SelectValue as-child>
    <Primitive :as="as" :as-child="asChild" :placeholder="placeholder">
      <slot />
    </Primitive>
  </SelectValue>
</template>
