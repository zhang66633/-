<script setup lang="ts">
import { cn } from "@/lib/utils";
import {
  ScrollAreaCorner,
  ScrollAreaRoot,
  ScrollAreaScrollbar,
  ScrollAreaThumb,
  ScrollAreaViewport,
} from "reka-ui";

interface ScrollAreaProps {
  class?: string;
  viewportClass?: string;
}

const props = defineProps<ScrollAreaProps>();
</script>

<template>
  <ScrollAreaRoot
    :class="
      cn(
        'relative overflow-hidden',
        props.class,
      )
    "
  >
    <ScrollAreaViewport
      :class="cn('h-full w-full rounded-[inherit]', props.viewportClass)"
    >
      <slot />
    </ScrollAreaViewport>
    <ScrollAreaScrollbar
      orientation="vertical"
      class="flex touch-none select-none transition-colors h-full w-1.5 border-l border-l-transparent p-px"
    >
      <ScrollAreaThumb class="relative flex-1 rounded-full bg-border" />
    </ScrollAreaScrollbar>
    <ScrollAreaScrollbar
      orientation="horizontal"
      class="flex touch-none select-none transition-colors h-1.5 flex-col border-t border-t-transparent p-px"
    >
      <ScrollAreaThumb class="relative flex-1 rounded-full bg-border" />
    </ScrollAreaScrollbar>
    <ScrollAreaCorner />
  </ScrollAreaRoot>
</template>
