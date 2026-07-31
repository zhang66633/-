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
        class="flex items-center justify-between py-2 px-3 rounded-md bg-muted/30"
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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  items: Array<{ id: string; name: string; retention: number }>;
}>();
</script>