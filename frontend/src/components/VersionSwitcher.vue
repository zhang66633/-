<template>
  <Popover>
    <PopoverTrigger>
      <button
        class="flex w-full items-center gap-2 rounded-sm border border-border px-3 py-2 text-sm hover:bg-accent/50 transition-colors"
      >
        <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground shrink-0">· 版本</span>
        <span class="flex-1 text-left truncate font-display text-xs">{{ selected }}</span>
        <ChevronDown class="h-3.5 w-3.5 text-muted-foreground shrink-0" />
      </button>
    </PopoverTrigger>
    <PopoverContent class="w-[240px] p-1">
      <button
        v-for="version in versions"
        :key="version"
        class="flex w-full items-center rounded-sm px-2 py-1.5 text-xs hover:bg-accent transition-colors"
        :class="version === selected ? 'bg-accent/60 font-medium' : 'text-muted-foreground'"
        @click="select(version)"
      >
        {{ version }}
      </button>
    </PopoverContent>
  </Popover>
</template>

<script setup lang="ts">
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ChevronDown } from "lucide-vue-next";
import { ref } from "vue";

const versions = ["MathModelAgent v0.2", "默认工作区"];

const selected = ref(versions[0]);

const emit = defineEmits<{
  change: [version: string];
}>();

function select(version: string) {
  selected.value = version;
  emit("change", version);
}
</script>
