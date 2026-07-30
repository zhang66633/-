<template>
  <div class="flex h-full bg-background">
    <!-- 左侧: 目录 + 笔记面板 -->
    <div class="w-56 shrink-0 border-r flex flex-col">
      <!-- 目录 -->
      <div class="flex-1 overflow-y-auto min-h-0">
        <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground px-3 py-2.5 border-b">📑 目录</p>
        <div class="py-1">
          <button
            v-for="h in headings"
            :key="h.id"
            class="block w-full text-left px-3 py-1 text-xs transition-colors hover:bg-accent/50 truncate"
            :class="activeHeading === h.id ? 'text-primary font-medium bg-primary/5' : 'text-muted-foreground'"
            :style="{ paddingLeft: (h.level * 8) + 'px' }"
            @click="scrollToHeading(h.id)"
          >
            {{ h.text }}
          </button>
          <div v-if="headings.length === 0" class="px-3 py-4 text-[11px] text-muted-foreground text-center">
            暂无目录
          </div>
        </div>
      </div>

      <!-- 笔记面板 -->
      <div class="h-52 shrink-0 border-t">
        <NotePanel
          :notes="notes"
          @add-blank="addBlankNote"
          @update="updateNote"
          @remove="removeNote"
          @jump-to="scrollToHeading"
        />
      </div>
    </div>

    <!-- 中间: 学习文档 -->
    <div class="flex-1 flex flex-col min-w-0 min-h-0">
      <!-- 顶部信息栏 -->
      <div class="flex items-center justify-between border-b px-6 py-2.5 shrink-0 bg-muted/20">
        <div class="flex items-center gap-3">
          <button
            class="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            @click="$router.push('/learn')"
          >
            <ArrowLeft class="h-4 w-4" />
            返回
          </button>
          <span class="text-muted-foreground text-sm">/</span>
          <span class="font-display font-medium text-sm">{{ unit?.title ?? '加载中...' }}</span>
          <span v-if="unit" class="font-mono text-[10px] px-2 py-0.5 rounded border" :class="difficultyBadge">
            {{ difficultyLabel }}
          </span>
        </div>
        <div class="flex items-center gap-3">
          <span class="font-mono text-[10px] text-muted-foreground">⏱ {{ unit?.estimated_minutes ?? '--' }}分钟</span>
          <button class="font-mono text-[10px] text-muted-foreground hover:text-foreground transition-colors" @click="chatOpen = !chatOpen">
            {{ chatOpen ? '收起助手 →' : '💬 助手' }}
          </button>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="store.loading" class="flex-1 flex items-center justify-center">
        <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
      </div>

      <!-- 错误 -->
      <div v-else-if="store.error" class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <p class="text-sm text-destructive">{{ store.error }}</p>
          <button class="mt-3 text-sm text-primary hover:underline" @click="retry">重试</button>
        </div>
      </div>

      <!-- 主体: 文档 + 聊天 -->
      <div v-else-if="unit" class="flex-1 flex min-h-0">
        <!-- 学习文档区 -->
        <div class="flex-1 min-w-0 min-h-0">
          <LearningDoc
            ref="docRef"
            :markdown="docMarkdown"
            :highlights="highlights"
            :unit-id="unit.unit_id"
            @add-note="handleAddNote"
            @toggle-highlight="handleToggleHighlight"
            @ask-ai="handleAskAI"
            @headings-change="headings = $event"
            @scroll-section="activeHeading = $event"
          />
        </div>

        <!-- 右侧聊天区 (可折叠) -->
        <div
          v-show="chatOpen"
          class="w-80 shrink-0 border-l flex flex-col min-h-0"
        >
          <ChatArea
            :messages="chatSession.activeLearningMessages"
            :is-running="chatSession.getIsRunning('learning')"
            :empty-text="`${agentName} 在此答疑`"
            :empty-subtext="'选中文档文字 → 点「问AI」快速提问'"
            :input-placeholder="`向${agentName}提问...`"
            cancellable
            @send="handleSend"
            @cancel="cancelStream"
          />
        </div>
      </div>

      <!-- 底部工具栏 -->
      <div v-if="unit" class="flex items-center gap-2 border-t px-4 py-2 shrink-0 bg-card">
        <button class="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs hover:bg-accent transition-colors" @click="markComplete">
          <CheckCircle class="h-3.5 w-3.5" />
          标记完成
        </button>
        <button class="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs hover:bg-accent transition-colors" @click="addBlankNote">
          <StickyNote class="h-3.5 w-3.5" />
          做笔记
        </button>
        <button
          class="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs hover:bg-accent transition-colors"
          :class="{ 'opacity-30': !lastSelectedText }"
          :disabled="!lastSelectedText"
          @click="askAIAboutSelection"
        >
          <MessageCircleQuestion class="h-3.5 w-3.5" />
          问AI
        </button>
        <span class="flex-1" />
        <span class="font-mono text-[10px] text-muted-foreground">{{ agentEmoji }} {{ agentName }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { ArrowLeft, Loader2, CheckCircle, StickyNote, MessageCircleQuestion } from "lucide-vue-next";
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
const highlights = ref<string[]>([]);
const notes = ref<NoteItem[]>([]);
const lastSelectedText = ref("");
const lastSelectedSection = ref("");

const unit = computed(() => store.currentUnit);
const unitId = computed(() => route.params.unitId as string);

// ── 学习文档内容 (AI生成占位 + 后续可扩展) ────────────

const docMarkdown = computed(() => {
  if (!unit.value) return "";
  return getMockContent(unit.value.unit_id, unit.value.title);
});

// ── 智能体信息 ────────────────────────────────────────

const agentMap: Record<string, { emoji: string; name: string }> = {
  analyst: { emoji: "🔍", name: "分析师" },
  modeler: { emoji: "🧩", name: "建模师" },
  solver: { emoji: "💻", name: "求解器" },
  verifier: { emoji: "🔬", name: "检验员" },
  editor: { emoji: "✍️", name: "编辑" },
};
const agentInfo = computed(() => agentMap[unit.value?.primary_agent ?? ""] ?? { emoji: "🧭", name: "导航员" });
const agentEmoji = computed(() => agentInfo.value.emoji);
const agentName = computed(() => agentInfo.value.name);

const difficultyLabel = computed(() => {
  const m: Record<string, string> = { beginner: "入门", intermediate: "进阶", advanced: "高阶", competition: "竞赛" };
  return m[unit.value?.difficulty ?? "beginner"] ?? "入门";
});
const difficultyBadge = computed(() => {
  const m: Record<string, string> = {
    beginner: "border-emerald-200 text-emerald-700 bg-emerald-50",
    intermediate: "border-amber-200 text-amber-700 bg-amber-50",
    advanced: "border-red-200 text-red-700 bg-red-50",
    competition: "border-purple-200 text-purple-700 bg-purple-50",
  };
  return m[unit.value?.difficulty ?? "beginner"] ?? "";
});

const unitContext = computed(() => {
  const u = unit.value;
  if (!u) return undefined;
  return {
    title: u.title,
    unit_type: u.type === "knowledge" ? "知识讲解" : u.type === "practice" ? "练习" : "综合项目",
    difficulty: u.difficulty,
    method_category: u.method_category || "通用",
    tags: u.tags?.join(", ") ?? "",
    primary_agent: u.primary_agent ?? "modeler",
    estimated_minutes: String(u.estimated_minutes ?? 30),
  };
});

// ── 笔记逻辑 ──────────────────────────────────────────

function handleAddNote(text: string, section: string) {
  notes.value.push({
    title: text.slice(0, 30) + (text.length > 30 ? "..." : ""),
    quote: text,
    section,
    comment: "",
    headingId: activeHeading.value,
  });
  saveNotes();
}

function addBlankNote() {
  notes.value.push({
    title: "新笔记",
    quote: "",
    section: "",
    comment: "",
    headingId: activeHeading.value,
  });
  saveNotes();
}

function updateNote(i: number, note: NoteItem) {
  notes.value[i] = note;
  saveNotes();
}

function removeNote(i: number) {
  notes.value.splice(i, 1);
  saveNotes();
}

function saveNotes() {
  try {
    localStorage.setItem(`notes_${unitId.value}`, JSON.stringify(notes.value));
  } catch {}
}

function loadNotes() {
  try {
    const raw = localStorage.getItem(`notes_${unitId.value}`);
    if (raw) notes.value = JSON.parse(raw);
  } catch {}
}

// ── 高亮逻辑 ──────────────────────────────────────────

function handleToggleHighlight(text: string) {
  const idx = highlights.value.indexOf(text);
  if (idx === -1) {
    highlights.value.push(text);
  } else {
    highlights.value.splice(idx, 1);
  }
  try {
    localStorage.setItem(`hl_${unitId.value}`, JSON.stringify(highlights.value));
  } catch {}
}

function loadHighlights() {
  try {
    const raw = localStorage.getItem(`hl_${unitId.value}`);
    if (raw) highlights.value = JSON.parse(raw);
  } catch {}
}

// ── 问AI ─────────────────────────────────────────────

function handleAskAI(text: string, section: string) {
  lastSelectedText.value = text;
  lastSelectedSection.value = section;
  chatOpen.value = true;
  handleUserSend(
    `关于「${section || unit.value?.title}」中的这段话：\n\n> ${text}\n\n请帮我解释一下。`,
    undefined,
    unitContext.value,
  );
}

function askAIAboutSelection() {
  if (!lastSelectedText.value) return;
  handleAskAI(lastSelectedText.value, lastSelectedSection.value);
}

// ── 发送消息 ──────────────────────────────────────────

function handleSend(text: string) {
  handleUserSend(text, undefined, unitContext.value);
}

// ── 标记完成 ──────────────────────────────────────────

function markComplete() {
  // TODO: 调用后端 API
  alert("已标记完成！");
}

// ── 目录跳转 ──────────────────────────────────────────

function scrollToHeading(id: string) {
  docRef.value?.scrollToHeading(id);
  activeHeading.value = id;
}

// ── 生命周期 ──────────────────────────────────────────

onMounted(() => {
  const id = route.params.unitId as string;
  if (id) {
    store.loadUnit(id);
  }
  restoreLatestSession();
  loadNotes();
  loadHighlights();
});

watch(() => route.params.unitId, (newId) => {
  if (newId) {
    store.loadUnit(newId as string);
    loadNotes();
    loadHighlights();
    headings.value = [];
    activeHeading.value = "";
  }
});

function retry() {
  const id = route.params.unitId as string;
  if (id) store.loadUnit(id);
}

// ── 临时学习文档内容 (后续改为后端生成) ──────────────────

function getMockContent(id: string, title: string): string {
  const contents: Record<string, string> = {
    "prog_py_01": `# ${title}

## 为什么学 Python 科学计算？

数学建模竞赛中，编程手需要快速将数学模型转化为可执行的代码。Python 凭借其丰富的科学计算生态，已成为数学建模最主流的编程语言之一。

**核心优势：**
- NumPy 提供高性能数组运算，速度接近 C
- SciPy 封装了优化、积分、统计等常用算法
- 语法简洁，学习曲线平缓

## NumPy 基础

### 创建数组

\`\`\`python
import numpy as np

# 从列表创建
arr = np.array([1, 2, 3, 4, 5])
print(arr)  # [1 2 3 4 5]

# 创建全零/全一数组
zeros = np.zeros((3, 4))
ones = np.ones((2, 5))

# 创建等差数组
linear = np.linspace(0, 1, 100)  # 0到1之间100个点
\`\`\`

### 数组运算

NumPy 的核心优势是**向量化运算**——无需写 for 循环：

\`\`\`python
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

# 逐元素运算
print(a + b)   # [5 7 9]
print(a * b)   # [4 10 18]
print(a ** 2)  # [1 4 9]

# 数学函数
print(np.sin(a))    # 每个元素求正弦
print(np.sum(a))    # 求和: 6
print(np.mean(a))   # 均值: 2.0
\`\`\`

### 矩阵运算

\`\`\`python
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

# 矩阵乘法
C = A @ B           # 或 np.dot(A, B)
print(C)            # [[19 22], [43 50]]

# 转置
print(A.T)          # [[1 3], [2 4]]

# 求逆
inv_A = np.linalg.inv(A)
\`\`\`

## 小结

NumPy 是 Python 科学计算的基石。掌握数组创建、向量化运算和矩阵操作，是成为合格编程手的第一步。
`,

    "prog_py_02": `# ${title}

## 创建与重塑

NumPy 数组的形状操作是数据处理的核心技能。

\`\`\`python
import numpy as np

# reshape: 改变形状
arr = np.arange(12)           # [0 1 2 ... 11]
mat = arr.reshape(3, 4)       # 3行4列的矩阵

# 索引与切片
print(mat[1, 2])              # 第2行第3列
print(mat[:, 1])              # 第2列所有行
print(mat[0:2, 1:3])          # 子矩阵
\`\`\`

## 广播机制

广播是 NumPy 最强大的特性之一——不同形状的数组也能运算：

\`\`\`python
# 标量广播
arr = np.array([1, 2, 3])
print(arr + 10)  # [11 12 13]

# 行列广播
mat = np.ones((3, 4))
row = np.array([1, 2, 3, 4])
print(mat + row)  # 每行都加row
\`\`\`

## 实战练习

用 NumPy 实现 $\sum_{i=1}^{n} x_i^2$ 的向量化版本。
`,

    "modeler_ahp_01": `# ${title}

## 什么是 AHP？

层次分析法（Analytic Hierarchy Process）是一种将复杂决策问题分解为层次结构的评价方法。

**核心思想：** 把主观判断量化，用数学方法做决策。

### 什么时候用 AHP？

- 多个可选方案，多个评价指标
- 指标之间难以直接量化比较
- 需要综合主观判断和客观数据

### 三步走

1. **建立层次结构** — 目标层 → 准则层 → 方案层
2. **构造成对比较矩阵** — 两两比较指标/方案的相对重要性
3. **计算权重 + 一致性检验** — 用特征值法求权重，检验判断的一致性

## 成对比较矩阵

假设有 3 个评价指标：价格、性能、外观。

比较矩阵 $A = [a_{ij}]$ 中，$a_{ij}$ 表示指标 $i$ 相对于指标 $j$ 的重要程度：

| 标度 | 含义 |
|------|------|
| 1 | 同等重要 |
| 3 | 稍微重要 |
| 5 | 明显重要 |
| 7 | 强烈重要 |
| 9 | 极端重要 |

**互反性：** $a_{ji} = 1 / a_{ij}$

## 一致性检验

如果 A 比 B 重要 3 倍，B 比 C 重要 2 倍，那么 A 应该比 C 重要 6 倍。
当判断矩阵不满足这种传递性时，就需要一致性检验。

**一致性比率：** $CR = CI / RI$

当 $CR < 0.1$ 时，判断矩阵的一致性可以接受。

## 小结

AHP 的关键在于**合理构造判断矩阵**和**通过一致性检验**。下一步将通过实际案例来练习。
`,
  };

  // 默认文档
  return contents[id] || `# ${title}

## 概述

本节介绍 ${title} 的核心概念和应用场景。

## 核心内容

学习资料正在准备中。你可以先通过右侧的智能助手提问，了解相关知识。

## 实践要点

- 理论与实践结合，每学完一个概念就动手练习
- 遇到不懂的地方，选中文字点「问AI」获取即时解答
- 做好笔记，方便复习时查阅
`;
}
</script>
