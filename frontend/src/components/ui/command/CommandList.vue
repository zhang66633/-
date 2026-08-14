<script setup lang="ts">
import { cn } from "@/lib/utils";

interface Props {
  class?: string;
}

const props = defineProps<Props>();
</script>

<template>
  <div :class="cn('max-h-[300px] overflow-y-auto overflow-x-hidden', props.class)">
    <slot />
  </div>
</template>
