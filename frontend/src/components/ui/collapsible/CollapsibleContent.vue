<script setup lang="ts">
import { cn } from "@/lib/utils";
import { CollapsibleContent } from "reka-ui";

interface Props {
  class?: string;
}

const props = defineProps<Props>();
</script>

<template>
  <CollapsibleContent
    :class="
      cn(
        'overflow-hidden data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down',
        props.class,
      )
    "
  >
    <slot />
  </CollapsibleContent>
</template>
