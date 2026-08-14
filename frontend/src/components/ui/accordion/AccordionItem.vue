<script setup lang="ts">
import { cn } from "@/lib/utils";
import type { AccordionItemProps } from "reka-ui";
import { AccordionItem, useForwardProps } from "reka-ui";

interface Props extends AccordionItemProps {
  class?: string;
}

const props = defineProps<Props>();
const forwarded = useForwardProps(props);
</script>

<template>
  <AccordionItem v-bind="forwarded" :class="cn('border-b border-border', props.class)">
    <slot />
  </AccordionItem>
</template>
