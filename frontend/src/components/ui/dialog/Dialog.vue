<script setup lang="ts">
import { cn } from "@/lib/utils";
import { X } from "lucide-vue-next";
import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  type DialogRootProps,
  DialogTitle,
  DialogTrigger,
} from "reka-ui";
import { computed } from "vue";

export interface DialogProps {
  /** Whether the dialog is open. Use with v-model:open */
  open?: DialogRootProps["defaultOpen"];
  /** Called when open state changes */
  onOpenChange?: (open: boolean) => void;
  /** Override default modal behavior */
  modal?: boolean;
}

const props = withDefaults(defineProps<DialogProps>(), {
  onOpenChange: undefined,
  modal: true,
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
</script>

<template>
  <DialogRoot v-model:open="openModel" :modal="props.modal" v-bind="$attrs">
    <slot />
  </DialogRoot>
</template>
