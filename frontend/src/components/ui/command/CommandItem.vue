<script setup lang="ts">
import { cn } from "@/lib/utils";
import type { ComboboxItemEmits, ComboboxItemProps } from "reka-ui";
import { ComboboxItem, useForwardPropsEmits } from "reka-ui";

interface Props extends ComboboxItemProps {
  class?: string;
}

const props = defineProps<Props>();
const emits = defineEmits<ComboboxItemEmits>();

const forward = useForwardPropsEmits(props, emits);
</script>

<template>
  <ComboboxItem
    v-bind="forward"
    :class="
      cn(
        'relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none',
        'data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground',
        'data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
        props.class,
      )
    "
  >
    <div class="flex items-center gap-2">
      <slot />
    </div>
  </ComboboxItem>
</template>
