<template>
  <div class="rounded-md border border-border bg-card p-5">
    <p class="font-display text-base font-medium mb-4">待复习提醒</p>
    <div v-if="items.length === 0" class="text-sm text-muted-foreground text-center py-6">
      暂无需要复习的单元，继续保持！
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="item in items"
        :key="item.id"
        class="flex cursor-pointer items-center justify-between py-2 px-3 rounded-md bg-muted/30 transition-colors hover:bg-accent/50"
        @click="$emit('open', item.id)"
      >
        <div class="min-w-0 flex-1">
          <p class="text-sm truncate">{{ item.name }}</p>
          <p class="text-[10px] text-muted-foreground">记忆保留率 {{ item.retention }}%</p>
        </div>
        <div class="shrink-0 ml-3">
          <div class="h-2 w-16 rounded-full bg-muted overflow-hidden">
            <div
              class="h-full rounded-full transition-all"
              :class="item.retention < 30 ? 'bg-destructive' : item.retention < 60 ? 'bg-amber-400' : 'bg-emerald-400'"
              :style="{ width: item.retention + '%' }"
            />
          </div>
        </div>
        <ArrowRight class="ml-2 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowRight } from "lucide-vue-next";

defineProps<{
  items: Array<{ id: string; name: string; retention: number }>;
}>();

defineEmits<{
  /** 点击某条待复习 → 跳到对应单元 */
  open: [id: string];
}>();
</script>