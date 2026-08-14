<template>
  <aside :class="collapsed ? 'w-12' : 'w-64'" class="flex flex-col border-r bg-background h-screen sticky top-0 shrink-0 transition-all duration-200">
    <div v-if="!collapsed" class="flex h-14 items-center border-b px-5 shrink-0">
      <div class="flex items-center gap-2.5">
        <div class="flex h-7 w-7 items-center justify-center border border-border rounded-sm">
          <span class="font-display text-sm font-medium leading-none">M</span>
        </div>
        <span class="font-display text-sm font-medium tracking-tight">{{ APP_NAME }}</span>
      </div>
    </div>
    <div v-else class="flex h-14 items-center justify-center border-b shrink-0">
      <div class="flex h-7 w-7 items-center justify-center border border-border rounded-sm">
        <span class="font-display text-sm font-medium leading-none">M</span>
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

    <!-- 展开态: 完整导航 -->
    <nav v-if="!collapsed" :class="sessionList.length > 0 ? 'py-3 shrink-0' : 'flex-1 py-6'">
      <button :class="[NAV_ITEM, isNavActive('/') ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground hover:bg-accent/30']" @click="navigate('/')">
        <span v-if="isNavActive('/')" class="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-px bg-primary" />
        <Home class="h-4 w-4 shrink-0" />
        <span :class="isNavActive('/') ? 'font-display font-medium' : ''">首页</span>
      </button>
      <div v-for="group in visibleGroups" :key="group.label" class="mt-1">
        <button class="flex items-center gap-2 w-full px-5 py-1.5 text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60 hover:text-muted-foreground transition-colors" @click="toggleGroup(group.label)">
          <ChevronRight class="h-3 w-3 shrink-0 transition-transform" :class="{ 'rotate-90': expandedGroups.has(group.label) }" />
          <component :is="group.icon" class="h-3.5 w-3.5 shrink-0" />
          {{ group.label }}
        </button>
        <div v-show="expandedGroups.has(group.label)" class="space-y-0.5">
          <button v-for="(item, i) in group.items" :key="item.path"
            :class="[NAV_ITEM, isNavActive(item.path) ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground hover:bg-accent/30']" @click="navigate(item.path)">
            <span v-if="isNavActive(item.path)" class="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-px bg-primary" />
            <component :is="item.icon" class="h-4 w-4 shrink-0 opacity-60" />
            <span :class="isNavActive(item.path) ? 'font-display font-medium' : ''">{{ item.label }}</span>
          </button>
        </div>
      </div>
    </nav>

    <!-- 折叠态: 仅图标 -->
    <nav v-else class="flex-1 py-4 flex flex-col items-center gap-2">
      <button v-for="item in collapsedNavItems" :key="item.path"
        class="flex h-8 w-8 items-center justify-center rounded-md transition-colors"
        :class="isNavActive(item.path) ? 'text-primary bg-primary/10' : 'text-muted-foreground hover:text-foreground hover:bg-accent/30'"
        :title="item.label" @click="navigate(item.path)">
        <component :is="item.icon" class="h-4 w-4" />
      </button>
    </nav>

    <!-- 底部固定项 -->
    <div v-if="!collapsed" class="border-t py-2 shrink-0">
      <button v-for="item in bottomItems" :key="item.path"
        :class="[NAV_ITEM, isNavActive(item.path) ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground hover:bg-accent/30']" @click="navigate(item.path)">
        <span v-if="isNavActive(item.path)" class="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-px bg-primary" />
        <component :is="item.icon" class="h-4 w-4 shrink-0 opacity-60" />
        <span :class="isNavActive(item.path) ? 'font-display font-medium' : ''">{{ item.label }}</span>
      </button>
    </div>

    <div v-if="!collapsed" class="border-t px-3 py-3 shrink-0">
      <VersionSwitcher />
    </div>

    <!-- 折叠/展开按钮 -->
    <div class="border-t py-2 shrink-0 flex justify-center">
      <button class="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors" :title="collapsed ? '展开侧栏' : '折叠侧栏'" @click="collapsed = !collapsed">
        <PanelLeftOpen v-if="!collapsed" class="h-3.5 w-3.5" />
        <PanelLeftClose v-else class="h-3.5 w-3.5" />
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import VersionSwitcher from "@/components/VersionSwitcher.vue";
import {
  bottomItems,
  learnGroup,
  learnPaths,
  paperGroup,
  paperPaths,
} from "@/config/navItems";
import { NAV_ITEM } from "@/config/styles";
import { type SessionMode, useChatSessionStore } from "@/stores/chatSession";
import { APP_NAME } from "@/types/const";
import {
  Check,
  ChevronRight,
  Home,
  PanelLeftClose,
  PanelLeftOpen,
  Pencil,
  X,
} from "lucide-vue-next";
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

const router = useRouter();
const route = useRoute();
const chatSession = useChatSessionStore();

const editingId = ref<string | null>(null);
const editingTitle = ref("");
const collapsed = ref(false);

// ── 折叠态导航项（所有页面入口） ──────────────────────
const collapsedNavItems = computed(() => {
  const items: { label: string; path: string; icon: any }[] = [
    { label: "首页", path: "/", icon: Home },
    ...paperGroup.items,
    ...learnGroup.items,
  ];
  return items;
});

// ── 导航分组逻辑 ─────────────────────────────────────

const allGroups = [paperGroup, learnGroup];

// 当前页面属于哪个组
const activeGroup = computed(() => {
  const path = route.path;
  if (path === "/") return null; // 首页两个组都展开
  for (const p of paperPaths) {
    if (path.startsWith(p)) return paperGroup.label;
  }
  for (const p of learnPaths) {
    if (path.startsWith(p)) return learnGroup.label;
  }
  return null;
});

const expandedGroups = ref<Set<string>>(
  new Set([paperGroup.label, learnGroup.label]),
);

// 路由变化时自动展开当前组、折叠另一个组（首页两个都展开）
watch(
  activeGroup,
  (group) => {
    if (!group) {
      // 首页: 两个都展开
      expandedGroups.value = new Set([paperGroup.label, learnGroup.label]);
    } else {
      expandedGroups.value = new Set([group]);
    }
  },
  { immediate: true },
);

function toggleGroup(label: string) {
  const next = new Set(expandedGroups.value);
  if (next.has(label)) {
    next.delete(label);
  } else {
    next.add(label);
  }
  expandedGroups.value = next;
}

const visibleGroups = computed(() => allGroups);

// ── 会话逻辑 ─────────────────────────────────────────

const currentMode = computed<SessionMode>(() => {
  if (route.path.startsWith("/solution")) return "solution";
  if (route.path.startsWith("/learn")) return "learning";
  if (route.path.startsWith("/practice")) return "practice";
  if (route.path.startsWith("/qa")) return "qa";
  return "chat";
});

const sessionListTitle = computed(() => {
  const titles: Record<SessionMode, string> = {
    chat: "最近对话",
    solution: "最近方案",
    learning: "学习对话",
    qa: "答疑记录",
    practice: "练习记录",
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
    chatSession.renameSession(
      currentMode.value,
      editingId.value,
      editingTitle.value,
    );
    editingId.value = null;
    editingTitle.value = "";
  }
}

function cancelRename() {
  editingId.value = null;
  editingTitle.value = "";
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
