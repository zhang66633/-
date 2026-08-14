<script setup lang="ts">
import { cn } from "@/lib/utils";
import { DialogTitle, type DialogTitleProps } from "reka-ui";

const props = defineProps<DialogTitleProps & { class?: string }>();
</script>

<template>
  <DialogTitle
    :class="cn('text-lg font-semibold text-foreground', props.class)"
    v-bind="$attrs"
  >
    <slot />
  </DialogTitle>
</template>
