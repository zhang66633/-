<script setup lang="ts">
import { cn } from "@/lib/utils";

interface CardProps {
  class?: string;
}

const props = defineProps<CardProps>();
</script>

<template>
  <div
    :class="
      cn(
        'rounded-lg border border-border bg-card text-card-foreground',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>
