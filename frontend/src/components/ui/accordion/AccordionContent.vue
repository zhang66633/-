<script setup lang="ts">
import { cn } from "@/lib/utils";
import { AccordionContent } from "reka-ui";

interface Props {
  class?: string;
}

const props = defineProps<Props>();
</script>

<template>
  <AccordionContent
    :class="
      cn(
        'overflow-hidden text-sm',
        'data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down',
        props.class,
      )
    "
  >
    <div class="pb-4 pt-0">
      <slot />
    </div>
  </AccordionContent>
</template>
