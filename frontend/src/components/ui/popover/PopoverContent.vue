<script setup lang="ts">
import { cn } from "@/lib/utils";
import {
  PopoverAnchor,
  PopoverArrow,
  PopoverClose,
  PopoverContent,
  PopoverPortal,
} from "reka-ui";

interface Props {
  class?: string;
  side?: "top" | "right" | "bottom" | "left";
  align?: "start" | "center" | "end";
  sideOffset?: number;
  showArrow?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  side: "bottom",
  align: "center",
  sideOffset: 4,
  showArrow: false,
});
</script>

<template>
  <PopoverPortal>
    <PopoverContent
      :side="side"
      :align="align"
      :side-offset="sideOffset"
      :class="
        cn(
          'z-50 w-72 rounded-md border border-border bg-popover p-4 text-popover-foreground shadow-md outline-none',
          'data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95',
          'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
          props.class,
        )
      "
    >
      <slot />
      <PopoverClose
        class="absolute right-2 top-2 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
      >
        <slot name="close" />
      </PopoverClose>
      <PopoverArrow v-if="showArrow" class="fill-popover" />
    </PopoverContent>
  </PopoverPortal>
</template>
