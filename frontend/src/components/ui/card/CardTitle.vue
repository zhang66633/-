<script setup lang="ts">
import { cn } from "@/lib/utils";

interface CardTitleProps {
  class?: string;
}

const props = defineProps<CardTitleProps>();
</script>

<template>
  <h3
    :class="
      cn(
        'font-display text-lg font-medium leading-none tracking-tight',
        props.class,
      )
    "
  >
    <slot />
  </h3>
</template>
