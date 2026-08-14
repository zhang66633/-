<script setup lang="ts">
import { cn } from "@/lib/utils";
import type { TabsContentProps } from "reka-ui";
import { TabsContent, useForwardProps } from "reka-ui";

interface Props extends TabsContentProps {
  class?: string;
}

const props = defineProps<Props>();

const forward = useForwardProps(props);
</script>

<template>
  <TabsContent
    v-bind="forward"
    :class="
      cn(
        'mt-2 ring-offset-background',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        props.class,
      )
    "
  >
    <slot />
  </TabsContent>
</template>
