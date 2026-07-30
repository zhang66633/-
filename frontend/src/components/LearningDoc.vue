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
        <button class="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-accent" @mousedown.prevent="doAskAI">
          <MessageCircleQuestion class="h-3.5 w-3.5" />问AI
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { StickyNote, MessageCircleQuestion } from "lucide-vue-next";
import { marked } from "marked";
import DOMPurify from "dompurify";

const props = defineProps<{ markdown: string; unitId: string }>();

const emit = defineEmits<{
  addNote: [text: string, sectionTitle: string];
  askAI: [text: string, sectionTitle: string];
  headingsChange: [headings: { id: string; text: string; level: number }[]];
  scrollSection: [id: string];
}>();

const docRoot = ref<HTMLElement>();
const contentRef = ref<HTMLElement>();
const progressPercent = ref(0);

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

// ── 选区 + Toolbar ──────────────────────────────────

const toolbar = ref({ visible: false, x: 0, y: 0 });
let selectedText = "";
let selectedSection = "";

function onDocMouseDown() { toolbar.value.visible = false; }

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
    const rc = sel.getRangeAt(0).getBoundingClientRect();
    toolbar.value = { visible: true, x: Math.max(10, rc.left + rc.width / 2 - 70), y: Math.max(10, rc.top - 44) };
  }, 10);
}

function doAddNote() { if (selectedText) emit("addNote", selectedText, selectedSection); clearSelection(); }
function doAskAI() { if (selectedText) emit("askAI", selectedText, selectedSection); clearSelection(); }
function clearSelection() { toolbar.value.visible = false; window.getSelection()?.removeAllRanges(); }

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
