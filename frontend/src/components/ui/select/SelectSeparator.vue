<script setup lang="ts">
import { cn } from "@/lib/utils";
import { SelectSeparator } from "reka-ui";

interface Props {
  class?: string;
}

const props = defineProps<Props>();
</script>

<template>
  <SelectSeparator :class="cn('-mx-1 my-1 h-px bg-muted', props.class)" />
</template>
