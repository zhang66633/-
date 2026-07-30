<template>
  <div ref="docRoot" class="learning-doc relative h-full overflow-y-auto" @scroll="onScroll">
    <!-- 顶部进度条 -->
    <div class="sticky top-0 left-0 right-0 h-0.5 bg-border z-10">
      <div class="h-full bg-primary transition-all duration-150" :style="{ width: progressPercent + '%' }" />
    </div>

    <!-- 文档内容 -->
    <div class="px-8 py-6 max-w-2xl mx-auto">
      <div ref="contentRef" class="prose prose-sm prose-gray dark:prose-invert max-w-none" v-html="renderedHtml" @mouseup="onTextSelect" />
    </div>

    <!-- 底部占位 -->
    <div class="h-64" />

    <!-- Mini Toolbar: 选中文字后弹出 -->
    <Teleport to="body">
      <div
        v-if="toolbar.visible"
        class="fixed z-50 flex items-center gap-0.5 rounded-md border border-border bg-card shadow-lg px-1 py-1"
        :style="{ left: toolbar.x + 'px', top: toolbar.y + 'px' }"
      >
        <button class="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-accent transition-colors" @click="addNote">
          <StickyNote class="h-3.5 w-3.5" />
          笔记
        </button>
        <button class="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-accent transition-colors" @click="toggleHighlight">
          <Highlighter class="h-3.5 w-3.5" />
          高亮
        </button>
        <button class="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-accent transition-colors" @click="askAI">
          <MessageCircleQuestion class="h-3.5 w-3.5" />
          问AI
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { StickyNote, Highlighter, MessageCircleQuestion } from "lucide-vue-next";
import { marked } from "marked";
import DOMPurify from "dompurify";

const props = defineProps<{
  markdown: string;
  highlights: string[];  // 已高亮的文本片段
  unitId: string;
}>();

const emit = defineEmits<{
  addNote: [text: string, sectionTitle: string];
  toggleHighlight: [text: string];
  askAI: [text: string, sectionTitle: string];
  headingsChange: [headings: { id: string; text: string; level: number }[]];
  scrollSection: [id: string];
}>();

const docRoot = ref<HTMLElement>();
const contentRef = ref<HTMLElement>();
const progressPercent = ref(0);

// ── Markdown 渲染 ───────────────────────────────────

const renderedHtml = computed(() => {
  if (!props.markdown) return "<p class='text-muted-foreground'>暂无学习资料</p>";
  const raw = marked.parse(props.markdown) as string;
  // 给标题加 id 用于目录跳转
  const withIds = raw.replace(/<(h[1-4])>/g, (_, tag) => {
    return `<${tag}>`;
  });
  return DOMPurify.sanitize(withIds);
});

// ── 标题提取 ────────────────────────────────────────

function extractHeadings() {
  if (!contentRef.value) return;
  const headings = contentRef.value.querySelectorAll("h1, h2, h3");
  const result: { id: string; text: string; level: number }[] = [];
  let counter = 0;
  headings.forEach((h) => {
    const id = `heading-${counter++}`;
    h.id = id;
    result.push({ id, text: h.textContent || "", level: parseInt(h.tagName[1]) });
  });
  emit("headingsChange", result);
}

watch(renderedHtml, () => {
  setTimeout(extractHeadings, 0);
});

// ── 高亮渲染 ────────────────────────────────────────

watch(
  () => [renderedHtml.value, props.highlights] as const,
  () => {
    setTimeout(() => {
      if (!contentRef.value || !props.highlights.length) return;
      applyHighlights();
    }, 100);
  },
);

function applyHighlights() {
  if (!contentRef.value) return;
  const walker = document.createTreeWalker(contentRef.value, NodeFilter.SHOW_TEXT);
  const texts: Text[] = [];
  while (walker.nextNode()) texts.push(walker.currentNode as Text);

  for (const hl of props.highlights) {
    for (const textNode of texts) {
      if (!textNode.textContent) continue;
      const idx = textNode.textContent.indexOf(hl);
      if (idx !== -1) {
        const span = document.createElement("span");
        span.className = "bg-amber-200 dark:bg-amber-800/40 rounded-sm";
        span.textContent = hl;
        const after = textNode.splitText(idx);
        after.splitText(hl.length);
        after.parentNode?.replaceChild(span, after);
        break;
      }
    }
  }
}

// ── 文本选择 + Toolbar ──────────────────────────────

const toolbar = ref({ visible: false, x: 0, y: 0 });
let selectedText = "";
let selectedSection = "";

function onTextSelect() {
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed || !sel.toString().trim()) {
    toolbar.value.visible = false;
    return;
  }
  selectedText = sel.toString().trim();

  // 找最近的标题作为章节上下文
  let node = sel.anchorNode;
  while (node && node !== contentRef.value) {
    if (node.nodeName?.match(/^H[1-4]$/)) {
      selectedSection = node.textContent || "";
      break;
    }
    node = node.parentElement as any;
  }

  const range = sel.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  toolbar.value = {
    visible: true,
    x: rect.left + rect.width / 2 - 60,
    y: rect.top - 40,
  };
}

function hideToolbar() {
  toolbar.value.visible = false;
}

function addNote() {
  if (selectedText) emit("addNote", selectedText, selectedSection);
  hideToolbar();
  window.getSelection()?.removeAllRanges();
}

function toggleHighlight() {
  if (selectedText) emit("toggleHighlight", selectedText);
  hideToolbar();
  window.getSelection()?.removeAllRanges();
}

function askAI() {
  if (selectedText) emit("askAI", selectedText, selectedSection);
  hideToolbar();
  window.getSelection()?.removeAllRanges();
}

// ── 滚动 ────────────────────────────────────────────

function onScroll() {
  if (!docRoot.value) return;
  const { scrollTop, scrollHeight, clientHeight } = docRoot.value;
  progressPercent.value = Math.round((scrollTop / (scrollHeight - clientHeight)) * 100);

  // 检测当前可见的标题
  if (!contentRef.value) return;
  const headings = contentRef.value.querySelectorAll("h1, h2, h3");
  let currentId = "";
  headings.forEach((h) => {
    const rect = h.getBoundingClientRect();
    if (rect.top <= 120) currentId = h.id;
  });
  if (currentId) emit("scrollSection", currentId);
}

// ── 外部跳转到指定标题 ──────────────────────────────

function scrollToHeading(id: string) {
  const el = contentRef.value?.querySelector(`#${id}`);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

defineExpose({ scrollToHeading });

// 点击其他地方关闭 toolbar
onMounted(() => {
  document.addEventListener("click", (e) => {
    if (!(e.target as HTMLElement).closest(".learning-doc")) {
      hideToolbar();
    }
  });
});
</script>

<style scoped>
.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3) {
  scroll-margin-top: 80px;
}
.prose :deep(pre) {
  background: #1e1e2e;
  border-radius: 0.5rem;
  padding: 1rem;
  overflow-x: auto;
}
.prose :deep(code) {
  font-size: 0.875em;
}
.prose :deep(.katex) {
  font-size: 1.1em;
}
</style>
