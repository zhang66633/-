<script setup lang="ts">
import { cn } from "@/lib/utils";
import { DialogClose, type DialogCloseProps } from "reka-ui";

const props = defineProps<DialogCloseProps & { class?: string }>();
</script>

<template>
  <DialogClose
    :class="cn(props.class)"
    v-bind="$attrs"
  >
    <slot />
  </DialogClose>
</template>
