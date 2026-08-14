<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ChevronRight, List } from "lucide-vue-next";
import type { TocEntry } from "@/utils/markdown";
import { extractToc } from "@/utils/markdown";

const props = defineProps<{
  html: string;
}>();

const entries = ref<TocEntry[]>([]);
const activeId = ref<string>("");
const collapsed = ref(false);

watch(
  () => props.html,
  (html) => {
    entries.value = extractToc(html);
  },
  { immediate: true },
);

function scrollTo(id: string) {
  activeId.value = id;
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

defineExpose({ setActiveId: (id: string) => (activeId.value = id) });
</script>

<template>
  <aside
    :class="[
      'flex flex-col border-r border-border bg-background/50 transition-all duration-300',
      collapsed ? 'w-10' : 'w-56',
    ]"
  >
    <!-- 折叠按钮 -->
    <div class="flex items-center justify-between px-3 py-2.5 border-b border-border shrink-0">
      <span v-if="!collapsed" class="text-xs font-semibold text-foreground">目录</span>
      <button
        class="inline-flex h-7 w-7 items-center justify-center rounded-md hover:bg-accent transition-colors shrink-0"
        :title="collapsed ? '展开目录' : '折叠目录'"
        @click="collapsed = !collapsed"
      >
        <List v-if="collapsed" class="h-3.5 w-3.5 text-muted-foreground" />
        <ChevronRight v-else class="h-3.5 w-3.5 text-muted-foreground" />
      </button>
    </div>

    <!-- 目录列表 -->
    <nav
      v-show="!collapsed"
      class="flex-1 overflow-y-auto py-2 px-2 space-y-0.5"
    >
      <template v-for="(entry, i) in entries" :key="i">
        <button
          :class="[
            'block w-full text-left rounded px-2 py-1 text-xs transition-colors hover:bg-accent truncate',
            entry.level === 1 ? 'font-semibold text-foreground' : '',
            entry.level === 2 ? 'pl-4 text-foreground/80' : '',
            entry.level === 3 ? 'pl-6 text-muted-foreground' : '',
            activeId === entry.id ? 'bg-accent text-foreground font-medium' : '',
          ]"
          :title="entry.text"
          @click="scrollTo(entry.id)"
        >
          {{ entry.text }}
        </button>
      </template>
      <div v-if="entries.length === 0" class="px-2 py-3 text-[11px] text-muted-foreground">
        暂无章节
      </div>
    </nav>
  </aside>
</template>