<script setup lang="ts">
import { cn } from "@/lib/utils";

interface AvatarImageProps {
  src: string;
  alt?: string;
  class?: string;
}

const props = withDefaults(defineProps<AvatarImageProps>(), {
  alt: "",
});
</script>

<template>
  <img
    :src="src"
    :alt="alt"
    :class="cn('aspect-square h-full w-full object-cover', props.class)"
    @error="($event.target as HTMLImageElement).style.display = 'none'"
  />
</template>
