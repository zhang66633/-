<script setup lang="ts">
import { cn } from "@/lib/utils";

interface Props {
  class?: string;
}

const props = defineProps<Props>();
</script>

<template>
  <span
    :class="
      cn(
        'ml-auto text-xs tracking-widest text-muted-foreground/60',
        props.class,
      )
    "
  >
    <slot />
  </span>
</template>
