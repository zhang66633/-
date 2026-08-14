<script setup lang="ts">
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-vue-next";
import type { PrimitiveProps } from "reka-ui";
import { Primitive, SelectIcon, SelectTrigger, useForwardProps } from "reka-ui";

interface Props extends PrimitiveProps {
  class?: string;
}

const props = withDefaults(defineProps<Props>(), {
  as: "button",
});

const forwarded = useForwardProps(props);
</script>

<template>
  <SelectTrigger as-child>
    <Primitive
      v-bind="forwarded"
      :class="
        cn(
          'flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
          'placeholder:text-muted-foreground',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
          'disabled:cursor-not-allowed disabled:opacity-50',
          '[&>span]:line-clamp-1',
          props.class,
        )
      "
    >
      <slot />
      <SelectIcon as-child>
        <ChevronDown class="h-4 w-4 shrink-0 opacity-50" />
      </SelectIcon>
    </Primitive>
  </SelectTrigger>
</template>
