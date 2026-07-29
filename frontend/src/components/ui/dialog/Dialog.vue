<script setup lang="ts">
import { computed } from "vue";
import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
  type DialogRootProps,
} from "reka-ui";
import { cn } from "@/lib/utils";
import { X } from "lucide-vue-next";

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
