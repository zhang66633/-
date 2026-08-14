<script setup lang="ts">
import { cn } from "@/lib/utils";
import { DialogTrigger, type DialogTriggerProps } from "reka-ui";

const props = defineProps<DialogTriggerProps & { class?: string }>();
</script>

<template>
  <DialogTrigger
    :as="props.as"
    :as-child="props.asChild"
    :class="cn(props.class)"
    v-bind="$attrs"
  >
    <slot />
  </DialogTrigger>
</template>
