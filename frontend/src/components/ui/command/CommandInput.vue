<script setup lang="ts">
import { cn } from "@/lib/utils";
import { Search } from "lucide-vue-next";

interface Props {
  class?: string;
  placeholder?: string;
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: "搜索...",
});

const model = defineModel<string>();
</script>

<template>
  <div class="flex items-center border-b border-border px-3" cmdk-input-wrapper>
    <Search class="mr-2 h-4 w-4 shrink-0 opacity-50" />
    <input
      v-model="model"
      :placeholder="placeholder"
      :class="
        cn(
          'flex h-11 w-full rounded-md bg-transparent py-3 text-sm outline-none',
          'placeholder:text-muted-foreground',
          'disabled:cursor-not-allowed disabled:opacity-50',
          props.class,
        )
      "
    />
  </div>
</template>
