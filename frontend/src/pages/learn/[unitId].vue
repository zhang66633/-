<template>
  <div class="flex h-full bg-background">
    <!-- 左侧 -->
    <div class="w-56 shrink-0 border-r flex flex-col">
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
    </div>

    <!-- 中间+右侧 -->
    <div class="flex-1 flex flex-col min-w-0 min-h-0">
      <div class="flex items-center justify-between border-b px-6 py-2.5 shrink-0 bg-muted/20">
        <div class="flex items-center gap-3">
          <button class="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors" @click="$router.push('/learn')">
            <ArrowLeft class="h-4 w-4" />返回
          </button>
          <span class="text-muted-foreground text-sm">/</span>
          <span class="font-display font-medium text-sm">{{ unit?.title ?? '加载中...' }}</span>
          <span v-if="unit" class="font-mono text-[10px] px-2 py-0.5 rounded border" :class="difficultyBadge">{{ difficultyLabel }}</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="font-mono text-[10px] text-muted-foreground">⏱ {{ unit?.estimated_minutes ?? '--' }}分钟</span>
          <button class="font-mono text-[10px] text-muted-foreground hover:text-foreground" @click="chatOpen = !chatOpen">{{ chatOpen ? '收起助手 →' : '💬 助手' }}</button>
        </div>
      </div>

      <div v-if="store.loading" class="flex-1 flex items-center justify-center"><Loader2 class="h-6 w-6 animate-spin text-muted-foreground" /></div>
      <div v-else-if="store.error" class="flex-1 flex items-center justify-center"><div class="text-center"><p class="text-sm text-destructive">{{ store.error }}</p><button class="mt-3 text-sm text-primary hover:underline" @click="retry">重试</button></div></div>

      <div v-else-if="unit" class="flex-1 flex min-h-0">
        <div class="flex-1 min-w-0 min-h-0">
          <LearningDoc ref="docRef" :markdown="docMarkdown" :highlights="highlights" :unit-id="unit.unit_id"
            @add-note="openNoteEditor" @toggle-highlight="handleToggleHighlight" @ask-ai="openAskPanel"
            @headings-change="headings = $event" @scroll-section="activeHeading = $event" />
        </div>
        <div v-show="chatOpen" class="w-80 shrink-0 border-l flex flex-col min-h-0 overflow-hidden">
          <!-- 问AI 输入面板 -->
          <div v-if="askPanel.visible" class="border-b px-3 py-2 bg-amber-50/50 shrink-0">
            <div class="flex items-center justify-between mb-1.5">
              <span class="font-mono text-[10px] text-amber-700">💬 基于选中文字提问</span>
              <button class="text-[10px] text-muted-foreground hover:text-foreground" @click="askPanel.visible = false">✕</button>
            </div>
            <p class="text-[11px] text-muted-foreground mb-2 line-clamp-2 italic">"{{ askPanel.quote.slice(0, 80) }}"</p>
            <textarea ref="askInputRef" v-model="askPanel.question"
              class="w-full text-xs border border-border rounded px-2 py-1.5 resize-none bg-background"
              rows="3" placeholder="输入你的问题..."
              @keydown.ctrl.enter="sendAskPanel" />
            <button class="mt-1.5 w-full rounded bg-primary text-primary-foreground text-xs py-1.5 hover:bg-primary/90"
              @click="sendAskPanel">发送提问</button>
          </div>
          <ChatArea
            :messages="chatSession.activeLearningMessages"
            :is-running="chatSession.getIsRunning('learning')"
            :empty-text="`${agentName} 在此答疑`" :empty-subtext="'选中文档文字 → 点「问AI」快速提问'"
            :input-placeholder="`向${agentName}提问...`"
            cancellable @send="handleSend" @cancel="cancelStream" />
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
import { ref, computed, onMounted, watch, nextTick } from "vue";
import { useRoute } from "vue-router";
import { ArrowLeft, Loader2, CheckCircle, StickyNote } from "lucide-vue-next";
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
const headings = ref<{ id: string; text: string; level: number }[]>([]);
const activeHeading = ref("");
const highlights = ref<{ text: string; color: string }[]>([]);
const notes = ref<NoteItem[]>([]);

// ── 问AI 面板 ──────────────────────────────────────
const askPanel = ref({ visible: false, quote: "", question: "", section: "" });
const askInputRef = ref<HTMLTextAreaElement>();

function openAskPanel(text: string, section: string) {
  chatOpen.value = true;
  askPanel.value = { visible: true, quote: text, question: `关于「${text.slice(0, 50)}」`, section };
  nextTick(() => askInputRef.value?.focus());
}
function sendAskPanel() {
  if (!askPanel.value.question.trim()) return;
  handleUserSend(askPanel.value.question, undefined, unitContext.value);
  askPanel.value.visible = false;
}

// ── 笔记编辑器 ──────────────────────────────────────
const noteEditor = ref({ visible: false, isNew: true, editIndex: -1, title: "", quote: "", comment: "", section: "", headingId: "" });

function openNoteEditor(quote: string, section: string) {
  noteEditor.value = { visible: true, isNew: true, editIndex: -1, title: quote.slice(0, 30), quote, comment: "", section, headingId: activeHeading.value };
}
function closeNoteEditor() { noteEditor.value.visible = false; }
function saveNote() {
  const e = noteEditor.value;
  if (e.isNew) {
    notes.value.push({ title: e.title || "未命名笔记", quote: e.quote, section: e.section, comment: e.comment, headingId: e.headingId });
  } else if (e.editIndex >= 0) {
    notes.value[e.editIndex] = { ...notes.value[e.editIndex], title: e.title, comment: e.comment };
  }
  saveNotes();
  noteEditor.value.visible = false;
}

// ── 高亮 ───────────────────────────────────────────
function handleToggleHighlight(text: string, color: string) {
  const idx = highlights.value.findIndex(h => h.text === text);
  if (idx === -1) { highlights.value.push({ text, color }); } else { highlights.value.splice(idx, 1); }
  saveHighlights();
}
function saveHighlights() { try { localStorage.setItem(`hl_${unitId.value}`, JSON.stringify(highlights.value)); } catch {} }
function loadHighlights() { try { const r = localStorage.getItem(`hl_${unitId.value}`); if (r) highlights.value = JSON.parse(r); } catch {} }

// ── 笔记存储 ───────────────────────────────────────
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
const unitContext = computed(() => { const u = unit.value; if (!u) return undefined; return { title: u.title, unit_type: u.type === "knowledge" ? "知识讲解" : u.type === "practice" ? "练习" : "综合项目", difficulty: u.difficulty, method_category: u.method_category || "通用", tags: u.tags?.join(", ") ?? "", primary_agent: u.primary_agent ?? "modeler", estimated_minutes: String(u.estimated_minutes ?? 30) }; });

function handleSend(text: string) { handleUserSend(text, undefined, unitContext.value); }
function markComplete() { alert("已标记完成！"); }
function scrollToHeading(id: string) { docRef.value?.scrollToHeading(id); activeHeading.value = id; }
function retry() { if (unitId.value) store.loadUnit(unitId.value); }

onMounted(() => { if (unitId.value) store.loadUnit(unitId.value); restoreLatestSession(); loadNotes(); loadHighlights(); });
watch(() => route.params.unitId, (id) => { if (id) { store.loadUnit(id as string); loadNotes(); loadHighlights(); headings.value = []; activeHeading.value = ""; } });

// ── 临时文档 ──────────────────────────────────────
const docMarkdown = computed(() => {
  const id = unitId.value;
  if (id === "prog_py_01") return `# Python科学计算入门\n\n## 为什么学?\n数学建模竞赛中，编程手需要快速将数学模型转化为可执行的代码。Python 凭借其丰富的科学计算生态，已成为数学建模最主流的编程语言之一。\n\n**核心优势：**\n- NumPy 提供高性能数组运算\n- SciPy 封装了优化、积分、统计等常用算法\n- 语法简洁，学习曲线平缓\n\n## NumPy 基础\n\n### 创建数组\n\n\`\`\`python\nimport numpy as np\narr = np.array([1, 2, 3, 4, 5])\nzeros = np.zeros((3, 4))\nlinear = np.linspace(0, 1, 100)\n\`\`\`\n\n### 向量化运算\n\n\`\`\`python\na = np.array([1, 2, 3])\nb = np.array([4, 5, 6])\nprint(a + b)   # [5 7 9]\nprint(a * b)   # [4 10 18]\n\`\`\`\n\n### 矩阵运算\n\n\`\`\`python\nA = np.array([[1, 2], [3, 4]])\nB = np.array([[5, 6], [7, 8]])\nC = A @ B\ninv_A = np.linalg.inv(A)\n\`\`\`\n\n## 小结\nNumPy 是 Python 科学计算的基石。掌握数组创建、向量化运算和矩阵操作，是成为合格编程手的第一步。`;
  if (id === "prog_py_02") return `# NumPy数组操作实战\n\n## 创建与重塑\n\`\`\`python\narr = np.arange(12).reshape(3, 4)\nprint(arr[:, 1])  # 第2列\n\`\`\`\n\n## 广播机制\n广播是 NumPy 最强大的特性之一：\n\`\`\`python\narr = np.array([1, 2, 3])\nprint(arr + 10)  # [11 12 13]\n\`\`\`\n\n## 实战练习\n用 NumPy 实现 $\\sum_{i=1}^{n} x_i^2$ 的向量化版本。`;
  if (id === "modeler_ahp_01") return `# 层次分析法(AHP)原理\n\n## 什么是 AHP？\n把主观判断量化，用数学方法做决策。\n\n## 三步走\n1. 建立层次结构\n2. 构造成对比较矩阵\n3. 计算权重+一致性检验\n\n## 比较标度\n| 标度 | 含义 |\n|------|------|\n| 1 | 同等重要 |\n| 3 | 稍微重要 |\n| 5 | 明显重要 |\n\n$$CR = CI / RI$$\n\n当 $CR < 0.1$ 时，判断矩阵一致性可接受。`;
  return `# ${unit.value?.title || '学习内容'}\n\n## 概述\n本节介绍核心概念和应用场景。\n\n## 核心内容\n学习资料正在准备中。你可以先通过右侧智能助手提问。\n\n## 实践要点\n- 理论与实践结合\n- 遇到不懂选中文字点「问AI」\n- 做好笔记方便复习`;
});
</script>
