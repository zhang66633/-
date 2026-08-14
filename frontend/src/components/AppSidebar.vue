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

    <!-- 展开态: 完整导航(主区域,可滚动,学习入口优先) -->
    <nav v-if="!collapsed" class="flex-1 overflow-y-auto py-3 min-h-0">
      <button :class="[NAV_ITEM, isNavActive('/') ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground hover:bg-accent/30']" @click="navigate('/')">
        <span v-if="isNavActive('/')" class="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-px bg-primary" />
        <Home class="h-4 w-4 shrink-0" />
        <span :class="isNavActive('/') ? 'font-display font-medium' : ''">首页</span>
      </button>
      <div v-for="group in visibleGroups" :key="group.label" class="mt-1">
        <!-- 静态小节标签(图标+汉字,不支持折叠,组内条目始终可见) -->
        <p class="flex items-center gap-2 w-full px-5 py-1.5 font-mono text-[10px] uppercase tracking-wider"
          :class="activeGroup === group.label ? 'text-primary' : 'text-muted-foreground/60'">
          <component :is="group.icon" class="h-3.5 w-3.5 shrink-0" />
          {{ group.label }}
        </p>
        <div class="space-y-0.5">
          <button v-for="(item, i) in group.items" :key="item.path"
            :class="[NAV_ITEM, isNavActive(item.path) ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground hover:bg-accent/30']" @click="navigate(item.path)">
            <span v-if="isNavActive(item.path)" class="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-px bg-primary" />
            <component :is="item.icon" class="h-4 w-4 shrink-0 opacity-60" />
            <span :class="isNavActive(item.path) ? 'font-display font-medium' : ''">{{ item.label }}</span>
          </button>
        </div>
      </div>
    </nav>

    <!-- 聊天记录(跨模式汇总,固定位置,空时占位保持布局稳定) -->
    <div v-if="!collapsed" class="border-t py-2 shrink-0 max-h-40 overflow-y-auto min-h-0">
      <p class="px-5 py-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">AI 聊天记录</p>
      <p v-if="sessionList.length === 0" class="px-5 py-2 text-[11px] text-muted-foreground/50">
        暂无聊天记录
      </p>
      <TransitionGroup name="session-list">
        <div
          v-for="s in sessionList"
          :key="s.session.id"
          class="group relative flex w-full items-center gap-2 py-1 pr-2 pl-5 text-sm cursor-pointer transition-all duration-200"
          :class="isActiveSession(s) ? 'text-foreground bg-accent/50' : 'text-muted-foreground hover:text-foreground hover:bg-accent/30'"
          @click="switchTo(s)"
        >
          <Transition name="indicator">
            <div
              v-if="isActiveSession(s)"
              class="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 bg-primary rounded-r"
            />
          </Transition>
          <template v-if="editing?.id === s.session.id">
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
            <span class="shrink-0 rounded bg-muted px-1 py-px font-mono text-[9px] text-muted-foreground/80">
              {{ modeBadge[s.mode] }}
            </span>
            <span class="truncate flex-1 text-xs">{{ s.session.title }}</span>
          </template>
          <div class="flex items-center gap-1 shrink-0">
            <button
              v-if="editing?.id !== s.session.id"
              class="flex h-5 w-5 shrink-0 items-center justify-center rounded-sm opacity-0 group-hover:opacity-100 hover:bg-primary/10 hover:text-primary transition-all"
              @click.stop="startRename(s)"
              title="重命名"
            >
              <Pencil class="h-3 w-3" />
            </button>
            <button
              v-if="editing?.id === s.session.id"
              class="flex h-5 w-5 shrink-0 items-center justify-center rounded-sm opacity-100 hover:bg-primary/10 hover:text-primary transition-all"
              @click.stop="confirmRename"
              title="确认"
            >
              <Check class="h-3 w-3" />
            </button>
            <button
              class="flex h-5 w-5 shrink-0 items-center justify-center rounded-sm opacity-0 group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive transition-all"
              @click.stop="removeSession(s)"
              title="删除"
            >
              <X class="h-3 w-3" />
            </button>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <!-- 折叠态: 仅图标 -->
    <nav v-else class="flex-1 py-4 flex flex-col items-center gap-2">
      <button v-for="item in collapsedNavItems" :key="item.path"
        class="flex h-8 w-8 items-center justify-center rounded-md transition-colors"
        :class="isNavActive(item.path) ? 'text-primary bg-primary/10' : 'text-muted-foreground hover:text-foreground hover:bg-accent/30'"
        :title="item.label" @click="navigate(item.path)">
        <component :is="item.icon" class="h-4 w-4" />
      </button>
    </nav>

    <!-- 底部固定项(技术配置降权: 小字+弱化) -->
    <div v-if="!collapsed" class="border-t py-1.5 shrink-0">
      <button v-for="item in bottomItems" :key="item.path"
        class="group relative flex w-full items-center gap-3 py-1.5 pr-4 pl-5 text-xs transition-colors"
        :class="isNavActive(item.path) ? 'text-foreground font-medium' : 'text-muted-foreground/70 hover:text-foreground hover:bg-accent/30'" @click="navigate(item.path)">
        <span v-if="isNavActive(item.path)" class="absolute left-0 top-1/2 -translate-y-1/2 h-4 w-px bg-primary" />
        <component :is="item.icon" class="h-3.5 w-3.5 shrink-0 opacity-60" />
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
import {
  type ChatSession,
  type SessionMode,
  useChatSessionStore,
} from "@/stores/chatSession";
import { APP_NAME } from "@/types/const";
import {
  Check,
  Home,
  PanelLeftClose,
  PanelLeftOpen,
  Pencil,
  X,
} from "lucide-vue-next";
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

const router = useRouter();
const route = useRoute();
const chatSession = useChatSessionStore();

const editing = ref<{ id: string; mode: SessionMode } | null>(null);
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

// 当前页面属于哪个组(仅用于学习中心组标题高亮;分组不再折叠)
const activeGroup = computed(() => {
  const path = route.path;
  if (path === "/") return null;
  for (const p of paperPaths) {
    if (path.startsWith(p)) return paperGroup.label;
  }
  for (const p of learnPaths) {
    if (path.startsWith(p)) return learnGroup.label;
  }
  return null;
});

const visibleGroups = computed(() => allGroups);

// ── 会话逻辑(跨模式汇总,不再随页面切换) ──────────────

const MODES: SessionMode[] = ["chat", "solution", "learning", "practice"];
const modeBadge: Record<SessionMode, string> = {
  chat: "对话",
  solution: "方案",
  learning: "学习",
  practice: "练习",
};
const modeRoute: Record<SessionMode, string> = {
  chat: "/chat",
  solution: "/solution",
  learning: "/learn",
  practice: "/practice",
};

interface SessionRow {
  session: ChatSession;
  mode: SessionMode;
}

const sessionList = computed<SessionRow[]>(() => {
  const all: SessionRow[] = [];
  for (const m of MODES) {
    for (const s of chatSession.getSessions(m).value) {
      all.push({ session: s, mode: m });
    }
  }
  return all
    .sort(
      (a, b) =>
        new Date(b.session.updatedAt).getTime() -
        new Date(a.session.updatedAt).getTime(),
    )
    .slice(0, 12);
});

function isActiveSession(row: SessionRow): boolean {
  return chatSession.getActiveId(row.mode).value === row.session.id;
}

/** 点击: 激活该模式会话;当前不在该模式页面时跳转过去 */
function switchTo(row: SessionRow) {
  chatSession.switchSession(row.mode, row.session.id);
  const path = route.path;
  const onModePage =
    row.mode === "learning"
      ? path.startsWith("/learn")
      : path.startsWith(modeRoute[row.mode]);
  if (!onModePage) router.push(modeRoute[row.mode]);
}

function removeSession(row: SessionRow) {
  const wasActive = isActiveSession(row);
  chatSession.deleteSession(row.mode, row.session.id);
  if (wasActive) {
    chatSession.clearActive(row.mode);
  }
}

function startRename(row: SessionRow) {
  editing.value = { id: row.session.id, mode: row.mode };
  editingTitle.value = row.session.title;
}

function confirmRename() {
  if (editing.value) {
    chatSession.renameSession(
      editing.value.mode,
      editing.value.id,
      editingTitle.value,
    );
    editing.value = null;
    editingTitle.value = "";
  }
}

function cancelRename() {
  editing.value = null;
  editingTitle.value = "";
}

function isNavActive(path: string): boolean {
  if (path === "/") return route.path === "/";
  // 精确匹配避免 /learn 匹配到 / 等
  if (path.startsWith("/learn")) return route.path.startsWith("/learn");
  if (path.startsWith("/practice")) return route.path.startsWith("/practice");
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
