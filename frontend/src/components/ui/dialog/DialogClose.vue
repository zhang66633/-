<script setup lang="ts">
import { cn } from "@/lib/utils";
import { DialogClose, type DialogCloseProps } from "reka-ui";

const props = defineProps<DialogCloseProps & { class?: string }>();
</script>

<template>
  <DialogClose
    :class="
      cn(
        'absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground',
        props.class,
      )
    "
    v-bind="$attrs"
  >
    <slot>
      <X class="h-4 w-4" />
      <span class="sr-only">Close</span>
    </slot>
  </DialogClose>
</template>
