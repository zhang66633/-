<script setup lang="ts">
import { cn } from "@/lib/utils";
import type { TooltipRootEmits, TooltipRootProps } from "reka-ui";
import {
  TooltipArrow,
  TooltipContent,
  TooltipPortal,
  TooltipRoot,
  TooltipTrigger,
  useForwardPropsEmits,
} from "reka-ui";

interface Props extends TooltipRootProps {
  content?: string;
  class?: string;
}

const props = defineProps<Props>();
const emits = defineEmits<TooltipRootEmits>();

const forward = useForwardPropsEmits(props, emits);
</script>

<template>
  <TooltipRoot v-bind="forward">
    <TooltipTrigger as-child>
      <slot />
    </TooltipTrigger>
    <TooltipPortal>
      <TooltipContent
        side="top"
        align="center"
        :class="
          cn(
            'z-50 overflow-hidden rounded-md border border-border bg-popover px-3 py-1.5 text-xs text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95',
            'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
            props.class,
          )
        "
      >
        <template v-if="content">
          {{ content }}
        </template>
        <slot v-else name="content" />
        <TooltipArrow :width="11" :height="5" class="fill-popover" />
      </TooltipContent>
    </TooltipPortal>
  </TooltipRoot>
</template>
