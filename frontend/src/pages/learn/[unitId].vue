<template>
  <div class="flex h-full bg-background">
    <!-- 左侧栏: 可折叠 -->
    <div :class="leftOpen ? 'w-56' : 'w-10'" class="shrink-0 border-r flex flex-col transition-all duration-200">
      <!-- 折叠按钮 -->
      <button class="flex items-center justify-center py-2 border-b hover:bg-accent/50 transition-colors" @click="leftOpen = !leftOpen" :title="leftOpen ? '折叠侧栏' : '展开侧栏'">
        <PanelLeftOpen v-if="leftOpen" class="h-3.5 w-3.5 text-muted-foreground" />
        <PanelLeft v-else class="h-3.5 w-3.5 text-muted-foreground" />
      </button>

      <template v-if="leftOpen">
        <div class="flex-1 overflow-y-auto min-h-0">
          <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground px-3 py-2.5 border-b">📑 目录</p>
          <div class="py-1">
            <button v-for="h in headings" :key="h.id"
              class="block w-full text-left px-3 py-1 text-xs transition-colors hover:bg-accent/50 truncate"
              :class="activeHeading === h.id ? 'text-primary font-medium bg-primary/5' : 'text-muted-foreground'"
              :style="{ paddingLeft: (h.level * 8) + 'px' }" @click="scrollToHeading(h.id)">{{ h.text }}</button>
            <div v-if="headings.length === 0" class="px-3 py-4 text-[11px] text-muted-foreground text-center">暂无目录</div>
          </div>
        </div>
        <div class="h-52 shrink-0 border-t">
          <NotePanel :notes="notes" @add-blank="openNoteEditor('', '')" @update="updateNote" @remove="removeNote" @jump-to="scrollToHeading" />
        </div>
      </template>
    </div>

    <!-- 中间+右侧 -->
    <div class="flex-1 flex flex-col min-w-0 min-h-0">
      <div class="flex items-center justify-between border-b px-4 py-2 shrink-0 bg-muted/20">
        <div class="flex items-center gap-2">
          <button class="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground" @click="$router.push('/learn')"><ArrowLeft class="h-4 w-4" />返回</button>
          <span class="text-muted-foreground text-sm">/</span>
          <span class="font-display font-medium text-sm truncate">{{ unit?.title ?? '加载中...' }}</span>
          <span v-if="unit" class="font-mono text-[10px] px-1.5 py-0.5 rounded border shrink-0" :class="difficultyBadge">{{ difficultyLabel }}</span>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <span class="font-mono text-[10px] text-muted-foreground hidden sm:inline">⏱ {{ unit?.estimated_minutes ?? '--' }}分钟</span>
          <button class="font-mono text-[10px] text-muted-foreground hover:text-foreground" @click="chatOpen = !chatOpen">{{ chatOpen ? '收起助手' : '💬 助手' }}</button>
        </div>
      </div>

      <div v-if="store.loading" class="flex-1 flex items-center justify-center"><Loader2 class="h-6 w-6 animate-spin text-muted-foreground" /></div>
      <div v-else-if="store.error" class="flex-1 flex items-center justify-center"><p class="text-sm text-destructive">{{ store.error }}</p></div>

      <div v-else-if="unit" class="flex-1 flex min-h-0">
        <!-- 文档区 -->
        <div class="flex-1 min-w-0 min-h-0">
          <LearningDoc ref="docRef" :markdown="docMarkdown" :unit-id="unit.unit_id"
            :on-add-note="openNoteEditor" :on-ask-a-i="handleAskAI"
            @headings-change="headings = $event" @scroll-section="activeHeading = $event" />
        </div>

        <!-- 拖拽分隔条 -->
        <div
          v-if="chatOpen"
          class="w-1.5 shrink-0 cursor-col-resize hover:bg-primary/30 active:bg-primary/50 transition-colors relative group"
          @mousedown="startResize"
        >
          <div class="absolute inset-y-0 -left-1 -right-1" />
        </div>

        <!-- 聊天区 -->
        <div v-show="chatOpen" class="shrink-0 border-l flex flex-col min-h-0 overflow-hidden" :style="{ width: chatWidth + 'px' }">
          <ChatArea
            :messages="chatSession.activeLearningMessages"
            :is-running="chatSession.getIsRunning('learning')"
            :empty-text="`${agentName} 在此答疑`" :empty-subtext="'选中文档文字 → 点「问AI」快速提问'"
            :input-placeholder="`向${agentName}提问...`"
            :prefill-text="prefillText"
            :session-title="chatSession.activeLearningSession?.title"
            cancellable @send="handleSend" @cancel="cancelStream"
            @new-session="chatSession.newSession('learning')" />
        </div>
      </div>

      <div v-if="unit" class="flex items-center gap-2 border-t px-4 py-2 shrink-0 bg-card">
        <button class="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs hover:bg-accent" @click="markComplete"><CheckCircle class="h-3.5 w-3.5" />标记完成</button>
        <button class="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs hover:bg-accent" @click="openNoteEditor('', '')"><StickyNote class="h-3.5 w-3.5" />做笔记</button>
        <span class="flex-1" />
        <span class="font-mono text-[10px] text-muted-foreground">{{ agentEmoji }} {{ agentName }}</span>
      </div>
    </div>

    <!-- 笔记编辑器弹窗 -->
    <Teleport to="body">
      <div v-if="noteEditor.visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/20" @mousedown.self="closeNoteEditor">
        <div class="bg-card border border-border rounded-lg shadow-xl w-full max-w-md p-5">
          <div class="flex items-center justify-between mb-3">
            <span class="font-display font-medium text-sm">📝 {{ noteEditor.isNew ? '新建笔记' : '编辑笔记' }}</span>
            <button class="text-muted-foreground hover:text-foreground" @click="closeNoteEditor">✕</button>
          </div>
          <div v-if="noteEditor.quote" class="rounded-md bg-muted/50 p-2 mb-3">
            <p class="text-[10px] font-mono text-muted-foreground mb-0.5">引用原文</p>
            <p class="text-xs leading-relaxed">{{ noteEditor.quote }}</p>
          </div>
          <label class="block text-[10px] font-mono text-muted-foreground mb-1">标题</label>
          <input v-model="noteEditor.title" class="w-full text-sm border border-border rounded px-3 py-1.5 mb-3 bg-background" placeholder="给这条笔记起个标题" />
          <label class="block text-[10px] font-mono text-muted-foreground mb-1">我的想法</label>
          <textarea v-model="noteEditor.comment" class="w-full text-sm border border-border rounded px-3 py-2 mb-3 bg-background resize-none" rows="4" placeholder="写写你的理解和思考..." />
          <div class="flex justify-end gap-2">
            <button class="rounded-md border px-4 py-1.5 text-xs hover:bg-accent" @click="closeNoteEditor">取消</button>
            <button class="rounded-md bg-primary text-primary-foreground px-4 py-1.5 text-xs hover:bg-primary/90" @click="saveNote">保存笔记</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onBeforeUnmount } from "vue";
import { useRoute } from "vue-router";
import { ArrowLeft, Loader2, CheckCircle, StickyNote, PanelLeftOpen, PanelLeft } from "lucide-vue-next";
import ChatArea from "@/components/ChatArea.vue";
import LearningDoc from "@/components/LearningDoc.vue";
import NotePanel from "@/components/NotePanel.vue";
import type { NoteItem } from "@/components/NotePanel.vue";
import { useLearningStore } from "@/stores/learning";
import { useChatSessionStore } from "@/stores/chatSession";
import { useStreamChat } from "@/composables/useStreamChat";

const route = useRoute();
const store = useLearningStore();
const chatSession = useChatSessionStore();
const { handleUserSend, restoreLatestSession, cancelStream } = useStreamChat("learning", "learning");

const docRef = ref<InstanceType<typeof LearningDoc>>();
const chatOpen = ref(true);
const chatWidth = ref(400);
const leftOpen = ref(true);
const headings = ref<{ id: string; text: string; level: number }[]>([]);
const activeHeading = ref("");
const notes = ref<NoteItem[]>([]);
const prefillText = ref("");

// ── 拖拽调整聊天区宽度 ─────────────────────────────

let resizeStartX = 0;
let resizeStartWidth = 0;

function startResize(e: MouseEvent) {
  resizeStartX = e.clientX;
  resizeStartWidth = chatWidth.value;
  document.addEventListener("mousemove", onResize);
  document.addEventListener("mouseup", stopResize);
  document.body.style.cursor = "col-resize";
  document.body.style.userSelect = "none";
}

function onResize(e: MouseEvent) {
  const delta = resizeStartX - e.clientX;
  chatWidth.value = Math.max(280, Math.min(700, resizeStartWidth + delta));
}

function stopResize() {
  document.removeEventListener("mousemove", onResize);
  document.removeEventListener("mouseup", stopResize);
  document.body.style.cursor = "";
  document.body.style.userSelect = "";
}

onBeforeUnmount(() => {
  document.removeEventListener("mousemove", onResize);
  document.removeEventListener("mouseup", stopResize);
});

// ── 问AI ───────────────────────────────────────────

function handleAskAI(text: string, section: string) {
  chatOpen.value = true;
  prefillText.value = `关于「${section || unit.value?.title || ''}」中的这段话：\n\n> ${text}\n\n请帮我解释一下。`;
}

// ── 笔记 ───────────────────────────────────────────

const noteEditor = ref({ visible: false, isNew: true, title: "", quote: "", comment: "", section: "", headingId: "" });
function openNoteEditor(quote: string, section: string) { noteEditor.value = { visible: true, isNew: true, title: quote.slice(0, 30), quote, comment: "", section, headingId: activeHeading.value }; }
function closeNoteEditor() { noteEditor.value.visible = false; }
function saveNote() {
  const e = noteEditor.value;
  if (e.isNew) notes.value.push({ title: e.title || "未命名笔记", quote: e.quote, section: e.section, comment: e.comment, headingId: e.headingId });
  saveNotes(); noteEditor.value.visible = false;
}
function updateNote(i: number, note: NoteItem) { notes.value[i] = note; saveNotes(); }
function removeNote(i: number) { notes.value.splice(i, 1); saveNotes(); }
function saveNotes() { try { localStorage.setItem(`notes_${unitId.value}`, JSON.stringify(notes.value)); } catch {} }
function loadNotes() { try { const r = localStorage.getItem(`notes_${unitId.value}`); if (r) notes.value = JSON.parse(r); } catch {} }

// ── 其他 ───────────────────────────────────────────

const unit = computed(() => store.currentUnit);
const unitId = computed(() => route.params.unitId as string);
const agentMap: Record<string, { emoji: string; name: string }> = { analyst: { emoji: "🔍", name: "分析师" }, modeler: { emoji: "🧩", name: "建模师" }, solver: { emoji: "💻", name: "求解器" }, verifier: { emoji: "🔬", name: "检验员" }, editor: { emoji: "✍️", name: "编辑" } };
const agentInfo = computed(() => agentMap[unit.value?.primary_agent ?? ""] ?? { emoji: "🧭", name: "导航员" });
const agentEmoji = computed(() => agentInfo.value.emoji);
const agentName = computed(() => agentInfo.value.name);
const difficultyLabel = computed(() => ({ beginner: "入门", intermediate: "进阶", advanced: "高阶", competition: "竞赛" } as any)[unit.value?.difficulty ?? "beginner"]);
const difficultyBadge = computed(() => ({ beginner: "border-emerald-200 text-emerald-700 bg-emerald-50", intermediate: "border-amber-200 text-amber-700 bg-amber-50", advanced: "border-red-200 text-red-700 bg-red-50", competition: "border-purple-200 text-purple-700 bg-purple-50" } as any)[unit.value?.difficulty ?? "beginner"]);
const unitContext = computed(() => { const u = unit.value; if (!u) return undefined; return { title: u.title, unit_type: u.type === "knowledge" ? "知识讲解" : "练习", difficulty: u.difficulty, method_category: u.method_category || "通用", tags: u.tags?.join(", ") ?? "", primary_agent: u.primary_agent ?? "modeler", estimated_minutes: String(u.estimated_minutes ?? 30) }; });

function handleSend(text: string) { handleUserSend(text, undefined, unitContext.value); }
function markComplete() {
  if (!unit.value) return;
  store.markComplete(unit.value.unit_id).then(() => {
    alert("已标记完成！掌握度已更新。");
  }).catch(() => {
    alert("标记失败，请重试");
  });
}
function scrollToHeading(id: string) { docRef.value?.scrollToHeading(id); activeHeading.value = id; }

onMounted(() => { if (unitId.value) store.loadUnit(unitId.value); restoreLatestSession(); loadNotes(); });
watch(() => route.params.unitId, (id) => { if (id) { store.loadUnit(id as string); loadNotes(); headings.value = []; activeHeading.value = ""; } });

const docMarkdown = computed(() => {
  const id = unitId.value;
  if (id === "prog_py_01") return `# Python科学计算入门\n\n## 为什么学?\n数学建模竞赛中，编程手需要快速将数学模型转化为可执行的代码。Python 凭借其丰富的科学计算生态，已成为数学建模最主流的编程语言之一。\n\n**核心优势：**\n- NumPy 提供高性能数组运算\n- SciPy 封装了优化、积分、统计等常用算法\n- 语法简洁，学习曲线平缓\n\n## NumPy 基础\n\n### 创建数组\n\n\`\`\`python\nimport numpy as np\narr = np.array([1, 2, 3, 4, 5])\nzeros = np.zeros((3, 4))\nlinear = np.linspace(0, 1, 100)\n\`\`\`\n\n### 向量化运算\n\n\`\`\`python\na = np.array([1, 2, 3])\nb = np.array([4, 5, 6])\nprint(a + b)   # [5 7 9]\nprint(a * b)   # [4 10 18]\n\`\`\`\n\n### 矩阵运算\n\n\`\`\`python\nA = np.array([[1, 2], [3, 4]])\nB = np.array([[5, 6], [7, 8]])\nC = A @ B\ninv_A = np.linalg.inv(A)\n\`\`\`\n\n## 小结\nNumPy 是 Python 科学计算的基石。`;
  if (id === "prog_py_02") return `# NumPy数组操作实战\n\n## 创建与重塑\n\`\`\`python\narr = np.arange(12).reshape(3, 4)\nprint(arr[:, 1])  # 第2列\n\`\`\`\n\n## 广播机制\n广播是 NumPy 最强大的特性：\n\`\`\`python\narr = np.array([1, 2, 3])\nprint(arr + 10)  # [11 12 13]\n\`\`\`\n\n## 实战\n用 NumPy 实现 $\\sum x_i^2$ 的向量化版本。`;
  if (id === "modeler_ahp_01") return `# 层次分析法(AHP)\n\n## 什么是 AHP？\n把主观判断量化，用数学方法做决策。\n\n## 三步走\n1. 建立层次结构\n2. 构造成对比较矩阵\n3. 计算权重+一致性检验\n\n## 比较标度\n| 标度 | 含义 |\n|------|------|\n| 1 | 同等重要 |\n| 3 | 稍微重要 |\n| 5 | 明显重要 |\n\n当 $CR < 0.1$ 时，判断矩阵一致性可接受。`;
  return `# ${unit.value?.title || '学习内容'}\n\n## 概述\n本节介绍核心概念和应用场景。\n\n## 核心内容\n学习资料正在准备中。你可以先通过右侧智能助手提问。`;
});
</script>
