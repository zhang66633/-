<template>
  <aside class="flex flex-col border-r bg-background h-screen sticky top-0 w-64 shrink-0">
    <div class="flex h-14 items-center border-b px-5 shrink-0">
      <div class="flex items-center gap-2.5">
        <div class="flex h-7 w-7 items-center justify-center border border-border rounded-sm">
          <span class="font-display text-sm font-medium leading-none">M</span>
        </div>
        <span class="font-display text-sm font-medium tracking-tight">{{ APP_NAME }}</span>
      </div>
    </div>

    <div v-if="sessionList.length > 0" class="border-b py-2 flex-1 overflow-y-auto min-h-0">
      <p class="px-5 py-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">{{ sessionListTitle }}</p>
      <TransitionGroup name="session-list">
        <div
          v-for="s in sessionList"
          :key="s.id"
          class="group relative flex w-full items-center gap-2 py-1.5 pr-2 pl-5 text-sm cursor-pointer transition-all duration-200"
          :class="isActiveSession(s.id) ? 'text-foreground bg-accent/50' : 'text-muted-foreground hover:text-foreground hover:bg-accent/30'"
          @click="switchTo(s.id)"
        >
          <Transition name="indicator">
            <div
              v-if="isActiveSession(s.id)"
              class="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 bg-primary rounded-r"
            />
          </Transition>
          <template v-if="editingId === s.id">
            <input
              v-model="editingTitle"
              class="flex-1 text-xs bg-background border border-primary/30 rounded px-1.5 py-0.5 outline-none"
              @keyup.enter="confirmRename"
              @keyup.esc="cancelRename"
              @click.stop
              autofocus
            />
          </template>
          <template v-else>
            <span class="truncate flex-1 text-xs">{{ s.title }}</span>
          </template>
          <div class="flex items-center gap-1 shrink-0">
            <button
              v-if="editingId !== s.id"
              class="flex h-5 w-5 shrink-0 items-center justify-center rounded-sm opacity-0 group-hover:opacity-100 hover:bg-primary/10 hover:text-primary transition-all"
              @click.stop="startRename(s.id, s.title)"
              title="重命名"
            >
              <Pencil class="h-3 w-3" />
            </button>
            <button
              v-if="editingId === s.id"
              class="flex h-5 w-5 shrink-0 items-center justify-center rounded-sm opacity-100 hover:bg-primary/10 hover:text-primary transition-all"
              @click.stop="confirmRename"
              title="确认"
            >
              <Check class="h-3 w-3" />
            </button>
            <button
              class="flex h-5 w-5 shrink-0 items-center justify-center rounded-sm opacity-0 group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive transition-all"
              @click.stop="removeSession(s.id)"
              title="删除"
            >
              <X class="h-3 w-3" />
            </button>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <div class="border-b py-2 shrink-0">
      <div class="flex items-center justify-between px-5 py-1.5">
        <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">归档</p>
        <span class="font-mono text-[9px] text-muted-foreground/40">{{ archiveCount }}</span>
      </div>
      <div class="flex items-center gap-0.5 px-4 pb-1.5">
        <button
          v-for="tab in archiveTabs"
          :key="tab.value"
          class="font-mono text-[10px] px-2.5 py-1 rounded transition-colors"
          :class="activeArchiveTab === tab.value
            ? 'bg-accent text-foreground'
            : 'text-muted-foreground/60 hover:text-muted-foreground'"
          @click="activeArchiveTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="overflow-y-auto" style="max-height: 200px;">
        <div v-if="currentArchiveList.length === 0" class="px-5 py-3">
          <p class="text-[10px] text-muted-foreground/50 font-mono">暂无归档</p>
        </div>
        <div
          v-for="item in currentArchiveList"
          :key="item.id"
          class="group relative flex w-full items-center gap-2 py-1.5 pr-2 pl-5 text-sm cursor-pointer transition-all duration-200"
          :class="isActiveArchive(item.id) ? 'text-foreground bg-accent/50' : 'text-muted-foreground hover:text-foreground hover:bg-accent/30'"
          @click="openArchive(item.id)"
        >
          <Transition name="indicator">
            <div
              v-if="isActiveArchive(item.id)"
              class="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 bg-primary rounded-r"
            />
          </Transition>
          <span class="truncate flex-1 text-xs">{{ item.title }}</span>
          <button
            class="flex h-5 w-5 shrink-0 items-center justify-center rounded-sm opacity-0 group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive transition-all"
            @click.stop="archiveStore.deleteArchive(item.id)"
            title="删除归档"
          >
            <X class="h-3 w-3" />
          </button>
        </div>
      </div>
    </div>

    <nav :class="sessionList.length > 0 ? 'py-3 shrink-0' : 'flex-1 py-6'">
      <button
        v-for="(item, i) in navItems"
        :key="item.path"
        :class="[NAV_ITEM, isNavActive(item.path) ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground hover:bg-accent/30']"
        @click="navigate(item.path)"
      >
        <span
          v-if="isNavActive(item.path)"
          class="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-px bg-primary"
          aria-hidden="true"
        />
        <span class="font-mono text-[10px] text-muted-foreground/70 w-5 shrink-0">§{{ i + 1 }}</span>
        <span :class="isNavActive(item.path) ? 'font-display font-medium' : ''">{{ item.label }}</span>
      </button>
    </nav>

    <div class="border-t px-3 py-3 shrink-0">
      <VersionSwitcher />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { X, Pencil, Check } from "lucide-vue-next";
import { APP_NAME } from "@/types/const";
import { navItems } from "@/config/navItems";
import { NAV_ITEM } from "@/config/styles";
import VersionSwitcher from "@/components/VersionSwitcher.vue";
import { useChatSessionStore, type SessionMode } from "@/stores/chatSession";
import { useArchiveStore } from "@/stores/archive";

const router = useRouter();
const route = useRoute();
const chatSession = useChatSessionStore();
const archiveStore = useArchiveStore();

const editingId = ref<string | null>(null);
const editingTitle = ref("");

const currentMode = computed<SessionMode>(() => {
  if (route.path.startsWith("/teach")) return "teach";
  if (route.path.startsWith("/solution")) return "solution";
  return "chat";
});

const sessionListTitle = computed(() => {
  const titles: Record<SessionMode, string> = {
    chat: "最近对话",
    teach: "最近学习",
    solution: "最近方案",
  };
  return titles[currentMode.value];
});

const sessionList = computed(() => {
  const sorted = chatSession.getSortedSessions(currentMode.value).value;
  return sorted.slice(0, 20);
});

function isActiveSession(id: string): boolean {
  return chatSession.getActiveId(currentMode.value).value === id;
}

function switchTo(id: string) {
  chatSession.switchSession(currentMode.value, id);
}

function removeSession(id: string) {
  const wasActive = isActiveSession(id);
  chatSession.deleteSession(currentMode.value, id);
  if (wasActive) {
    chatSession.clearActive(currentMode.value);
  }
}

function startRename(id: string, title: string) {
  editingId.value = id;
  editingTitle.value = title;
}

function confirmRename() {
  if (editingId.value) {
    chatSession.renameSession(currentMode.value, editingId.value, editingTitle.value);
    editingId.value = null;
    editingTitle.value = "";
  }
}

function cancelRename() {
  editingId.value = null;
  editingTitle.value = "";
}

const activeArchiveTab = ref<"solution" | "teaching">("solution");
const archiveTabs = [
  { label: "方案", value: "solution" as const },
  { label: "教学", value: "teaching" as const },
];

const archiveCount = computed(() => archiveStore.sortedItems.length);

const currentArchiveList = computed(() =>
  activeArchiveTab.value === "solution"
    ? archiveStore.solutionItems.slice(0, 20)
    : archiveStore.teachingItems.slice(0, 20),
);

function isActiveArchive(id: string): boolean {
  return route.path === `/archive/${id}`;
}

function openArchive(id: string) {
  router.push(`/archive/${id}`);
}

function isNavActive(path: string): boolean {
  if (path === "/") return route.path === "/";
  // 精确匹配避免 /learn 匹配到 / 等
  if (path.startsWith("/learn")) return route.path.startsWith("/learn");
  if (path.startsWith("/practice")) return route.path.startsWith("/practice");
  if (path.startsWith("/qa")) return route.path.startsWith("/qa");
  if (path.startsWith("/progress")) return route.path.startsWith("/progress");
  if (path.startsWith("/knowledge")) return route.path.startsWith("/knowledge");
  if (path.startsWith("/archive")) return route.path.startsWith("/archive");
  if (path.startsWith("/apikeys")) return route.path.startsWith("/apikeys");
  if (path.startsWith("/settings")) return route.path.startsWith("/settings");
  // 以下路由需要在精确匹配之前做前缀匹配（/chat 不会与 / 冲突）
  if (path === "/chat") return route.path.startsWith("/chat");
  if (path === "/teach") return route.path.startsWith("/teach");
  if (path === "/solution") return route.path.startsWith("/solution");
  return false;
}

function navigate(path: string) {
  router.push(path);
}
</script>

<style scoped>
.session-list-move {
  transition: transform 0.3s ease;
}

.session-list-enter-active,
.session-list-leave-active {
  transition: opacity 0.25s ease, height 0.3s ease, margin 0.3s ease, padding 0.3s ease;
}

.session-list-enter-from {
  opacity: 0;
  transform: translateX(-8px);
}

.session-list-leave-to {
  opacity: 0;
  height: 0 !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  overflow: hidden;
}

.indicator-enter-active,
.indicator-leave-active {
  transition: all 0.2s ease;
}

.indicator-enter-from,
.indicator-leave-to {
  opacity: 0;
  transform: translateX(-4px) scaleY(0.5);
}
</style>
