<script setup lang="ts">
import { cn } from "@/lib/utils";
import type { PrimitiveProps } from "reka-ui";
import { CollapsibleTrigger } from "reka-ui";

interface Props extends PrimitiveProps {
  class?: string;
}

const props = withDefaults(defineProps<Props>(), {
  as: "button",
});
</script>

<template>
  <CollapsibleTrigger as-child>
    <slot />
  </CollapsibleTrigger>
</template>
