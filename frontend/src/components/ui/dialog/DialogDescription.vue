<script setup lang="ts">
import { cn } from "@/lib/utils";
import { DialogDescription, type DialogDescriptionProps } from "reka-ui";

const props = defineProps<DialogDescriptionProps & { class?: string }>();
</script>

<template>
  <DialogDescription
    :class="cn('text-sm text-muted-foreground', props.class)"
    v-bind="$attrs"
  >
    <slot />
  </DialogDescription>
</template>
