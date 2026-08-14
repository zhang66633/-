<script setup lang="ts">
import { cn } from "@/lib/utils";
import { DialogTitle, type DialogTitleProps } from "reka-ui";

const props = defineProps<DialogTitleProps & { class?: string }>();
</script>

<template>
  <DialogTitle
    :class="cn('text-lg font-semibold leading-none tracking-tight', props.class)"
    v-bind="$attrs"
  >
    <slot />
  </DialogTitle>
</template>
