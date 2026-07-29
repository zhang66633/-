<script setup lang="ts">
import { computed, provide } from "vue";
import { DialogRoot, type DialogRootProps } from "reka-ui";
import type { SheetSide } from "./types";

export interface SheetProps {
  open?: DialogRootProps["defaultOpen"];
  onOpenChange?: (open: boolean) => void;
  side?: SheetSide;
}

const props = withDefaults(defineProps<SheetProps>(), {
  onOpenChange: undefined,
  side: "right",
});

const emit = defineEmits<{
  "update:open": [value: boolean];
}>();

const openModel = computed({
  get: () => props.open,
  set: (val) => {
    props.onOpenChange?.(val);
    emit("update:open", val);
  },
});

provide("sheetSide", props.side);
</script>

<template>
  <DialogRoot v-model:open="openModel" v-bind="$attrs">
    <slot />
  </DialogRoot>
</template>
