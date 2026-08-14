<script setup lang="ts">
import { cn } from "@/lib/utils";
import { TabsList } from "reka-ui";

interface Props {
  class?: string;
}

const props = defineProps<Props>();
</script>

<template>
  <TabsList
    :class="
      cn(
        'inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground',
        props.class,
      )
    "
  >
    <slot />
  </TabsList>
</template>
