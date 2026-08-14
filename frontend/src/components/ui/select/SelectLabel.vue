<script setup lang="ts">
import { cn } from "@/lib/utils";
import { SelectLabel } from "reka-ui";

interface Props {
  class?: string;
}

const props = defineProps<Props>();
</script>

<template>
  <SelectLabel :class="cn('py-1.5 pl-8 pr-2 text-xs font-medium text-muted-foreground', props.class)">
    <slot />
  </SelectLabel>
</template>
