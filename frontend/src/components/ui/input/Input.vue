<script setup lang="ts">
import { cn } from "@/lib/utils";

export interface InputProps {
  class?: string;
  type?: string;
  modelValue?: string | number;
}

const props = withDefaults(defineProps<InputProps>(), {
  type: "text",
});

const emit =
  defineEmits<(e: "update:modelValue", value: string | number) => void>();

function onInput(event: Event) {
  const target = event.target as HTMLInputElement;
  emit("update:modelValue", target.value);
}
</script>

<template>
  <input
    :type="type"
    :value="modelValue"
    @input="onInput"
    :class="
      cn(
        'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
        props.class,
      )
    "
  />
</template>
