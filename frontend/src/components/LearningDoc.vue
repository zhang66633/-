<template>
  <div ref="docRoot" class="learning-doc relative h-full overflow-y-auto" @scroll="onScroll" @mousedown="onDocMouseDown">
    <div class="sticky top-0 left-0 right-0 h-0.5 bg-border z-10">
      <div class="h-full bg-primary transition-all duration-150" :style="{ width: progressPercent + '%' }" />
    </div>

    <div class="px-8 py-6 max-w-2xl mx-auto">
      <div ref="contentRef" class="prose prose-sm prose-gray dark:prose-invert max-w-none" v-html="renderedHtml" />
    </div>
    <div class="h-64" />

    <!-- Mini Toolbar -->
    <Teleport to="body">
      <div
        v-if="toolbar.visible"
        class="fixed z-50 flex items-center gap-0.5 rounded-md border border-border bg-card shadow-lg px-1.5 py-1.5"
        :style="{ left: toolbar.x + 'px', top: toolbar.y + 'px' }"
      >
        <button class="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-accent" @mousedown.prevent="doAddNote">
          <StickyNote class="h-3.5 w-3.5" />笔记
        </button>
        <div class="relative" @mousedown.prevent>
          <button class="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-accent" @mousedown.prevent="showColorPicker = !showColorPicker">
            <Highlighter class="h-3.5 w-3.5" />高亮
            <span class="ml-0.5 h-2.5 w-2.5 rounded-full inline-block" :style="{ background: selectedColor }" />
          </button>
          <div v-if="showColorPicker" class="absolute top-full left-0 mt-1 flex gap-1 rounded-md border border-border bg-card shadow-lg p-1.5 z-50">
            <button v-for="c in highlightColors" :key="c" class="h-5 w-5 rounded-full border-2 hover:scale-110 transition-all"
              :class="selectedColor === c ? 'border-primary' : 'border-transparent'"
              :style="{ background: c }" @mousedown.prevent="doHighlight(c)" />
          </div>
        </div>
        <button class="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-accent" @mousedown.prevent="doAskAI">
          <MessageCircleQuestion class="h-3.5 w-3.5" />问AI
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
  highlights: { text: string; color: string }[];
  unitId: string;
}>();

const emit = defineEmits<{
  addNote: [text: string, sectionTitle: string];
  toggleHighlight: [text: string, color: string];
  askAI: [text: string, sectionTitle: string];
  headingsChange: [headings: { id: string; text: string; level: number }[]];
  scrollSection: [id: string];
}>();

const docRoot = ref<HTMLElement>();
const contentRef = ref<HTMLElement>();
const progressPercent = ref(0);
const selectedColor = ref("#fde047");
const showColorPicker = ref(false);
const highlightColors = ["#fde047", "#fca5a5", "#86efac", "#93c5fd", "#d8b4fe", "#fdba74"];

// ── Markdown ────────────────────────────────────────

const renderedHtml = computed(() => {
  if (!props.markdown) return "<p class='text-muted-foreground'>暂无学习资料</p>";
  return DOMPurify.sanitize(marked.parse(props.markdown) as string);
});

// ── 标题 ────────────────────────────────────────────

function extractHeadings() {
  if (!contentRef.value) return;
  const hs = contentRef.value.querySelectorAll("h1, h2, h3");
  const r: { id: string; text: string; level: number }[] = [];
  let n = 0;
  hs.forEach((h) => { h.id = `h-${n++}`; r.push({ id: h.id, text: h.textContent || "", level: +h.tagName[1] }); });
  emit("headingsChange", r);
}
watch(renderedHtml, () => setTimeout(extractHeadings, 0));

// ── 高亮渲染 (文本搜索, 渲染后回填) ─────────────────

watch(() => [renderedHtml.value, props.highlights] as const, () => setTimeout(applyHighlights, 100));

function applyHighlights() {
  if (!contentRef.value || !props.highlights.length) return;
  const walker = document.createTreeWalker(contentRef.value, NodeFilter.SHOW_TEXT);
  const texts: Text[] = [];
  while (walker.nextNode()) texts.push(walker.currentNode as Text);
  for (const hl of props.highlights) {
    for (const tn of texts) {
      if (!tn.textContent) continue;
      const i = tn.textContent.indexOf(hl.text);
      if (i === -1) continue;
      const s = document.createElement("span");
      s.style.cssText = `background:${hl.color};border-radius:2px;`;
      s.textContent = hl.text;
      const after = tn.splitText(i);
      after.splitText(hl.text.length);
      after.parentNode?.replaceChild(s, after);
      break;
    }
  }
}

// ── 选区 + Toolbar ──────────────────────────────────

const toolbar = ref({ visible: false, x: 0, y: 0 });
let selectedText = "";
let selectedSection = "";

function onDocMouseDown() { toolbar.value.visible = false; showColorPicker.value = false; }

function onGlobalMouseUp() {
  setTimeout(() => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return;
    const t = sel.toString().trim();
    if (t.length < 1) return;
    selectedText = t;

    let n = sel.anchorNode;
    while (n && n !== contentRef.value) {
      if (n.nodeName?.match(/^H[1-4]$/)) { selectedSection = n.textContent || ""; break; }
      n = n.parentElement as any;
    }
    const r = sel.getRangeAt(0).getBoundingClientRect();
    toolbar.value = { visible: true, x: Math.max(10, r.left + r.width / 2 - 90), y: Math.max(10, r.top - 44) };
  }, 10);
}

function doHighlight(color: string) {
  if (!selectedText) return;
  // 用 Range 直接包裹
  const sel = window.getSelection();
  if (sel && !sel.isCollapsed) {
    const r = sel.getRangeAt(0);
    if (r.collapsed) return;
    try {
      const span = document.createElement("span");
      span.style.cssText = `background:${color};border-radius:2px;`;
      r.surroundContents(span);
    } catch { /* 跨元素选区可能失败, fallback 到 emit */ }
  }
  emit("toggleHighlight", selectedText, color);
  clearSelection();
}

function doAddNote() { if (selectedText) emit("addNote", selectedText, selectedSection); clearSelection(); }
function doAskAI() { if (selectedText) emit("askAI", selectedText, selectedSection); clearSelection(); }

function clearSelection() { toolbar.value.visible = false; showColorPicker.value = false; window.getSelection()?.removeAllRanges(); }

// ── 滚动 ────────────────────────────────────────────

function onScroll() {
  if (!docRoot.value) return;
  const { scrollTop, scrollHeight, clientHeight } = docRoot.value;
  const p = Math.round((scrollTop / (scrollHeight - clientHeight)) * 100);
  progressPercent.value = isNaN(p) ? 0 : Math.min(100, Math.max(0, p));
  if (!contentRef.value) return;
  let id = "";
  contentRef.value.querySelectorAll("h1,h2,h3").forEach((h) => { if (h.getBoundingClientRect().top <= 120) id = h.id; });
  if (id) emit("scrollSection", id);
}
function scrollToHeading(id: string) { contentRef.value?.querySelector(`#${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" }); }
defineExpose({ scrollToHeading });

onMounted(() => document.addEventListener("mouseup", onGlobalMouseUp));
onBeforeUnmount(() => document.removeEventListener("mouseup", onGlobalMouseUp));
</script>

<style scoped>
.prose :deep(h1), .prose :deep(h2), .prose :deep(h3) { scroll-margin-top: 80px; }
.prose :deep(pre) { background: #1e1e2e; border-radius: 0.5rem; padding: 1rem; overflow-x: auto; }
.prose :deep(code) { font-size: 0.875em; }
.prose :deep(.katex) { font-size: 1.1em; }
</style>
