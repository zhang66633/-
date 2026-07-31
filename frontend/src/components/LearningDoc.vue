<template>
  <div ref="docRoot" class="learning-doc relative h-full overflow-y-auto" @scroll="onScroll" @mousedown="onDocMouseDown" @contextmenu.prevent>
    <div class="sticky top-0 left-0 right-0 h-0.5 bg-border z-10">
      <div class="h-full bg-primary transition-all duration-150" :style="{ width: progressPercent + '%' }" />
    </div>
    <div class="px-8 py-6 max-w-2xl mx-auto">
      <div ref="contentRef" class="prose prose-sm prose-gray dark:prose-invert max-w-none" v-html="renderedHtml" />
    </div>
    <div class="h-64" />

    <!-- 仿浏览器蓝色选区覆盖层 -->
    <Teleport to="body">
      <div v-if="fakeSel.visible" class="fixed inset-0 pointer-events-none z-40">
        <div v-for="(r, i) in fakeSel.rects" :key="i"
          class="absolute" style="background: rgba(0,102,204,0.25);"
          :style="{ left: r.left + 'px', top: r.top + window.scrollY + 'px', width: r.width + 'px', height: r.height + 'px' }" />
      </div>
    </Teleport>

    <!-- Mini Toolbar -->
    <Teleport to="body">
      <div v-if="toolbar.visible" class="fixed z-50 flex items-center gap-0.5 rounded-md border border-border bg-card shadow-lg px-1.5 py-1.5" :style="{ left: toolbar.x + 'px', top: toolbar.y + 'px' }">
        <button class="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-accent" @mousedown.stop.prevent="doAddNote">
          <StickyNote class="h-3.5 w-3.5" />笔记
        </button>
        <button class="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-accent" @mousedown.stop.prevent="doAskAI">
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

const props = defineProps<{
  markdown: string; unitId: string;
  onAddNote?: (text: string, section: string) => void;
  onAskAI?: (text: string, section: string) => void;
}>();

const emit = defineEmits<{
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

function extractHeadings() {
  if (!contentRef.value) return;
  const hs = contentRef.value.querySelectorAll("h1, h2, h3");
  const r: { id: string; text: string; level: number }[] = [];
  let n = 0;
  hs.forEach((h) => { h.id = `h-${n++}`; r.push({ id: h.id, text: h.textContent || "", level: +h.tagName[1] }); });
  emit("headingsChange", r);
}
watch(renderedHtml, () => setTimeout(extractHeadings, 0));

// ── 选区 ────────────────────────────────────────────

const toolbar = ref({ visible: false, x: 0, y: 0 });
const fakeSel = ref<{ visible: boolean; rects: DOMRect[] }>({ visible: false, rects: [] });
let selectedText = "";
let selectedSection = "";
const window = { scrollY: 0 };

function updateScrollY() { window.scrollY = globalThis.scrollY || 0; }

function onDocMouseDown() {
  setTimeout(() => { toolbar.value.visible = false; fakeSel.value.visible = false; }, 200);
}

function onGlobalMouseUp() {
  updateScrollY();
  const sel = document.getSelection ? document.getSelection() : null;
  if (!sel || sel.isCollapsed) return;
  if (!contentRef.value) return;
  const an = sel.anchorNode;
  const fn = sel.focusNode;
  if (!an || !fn || !contentRef.value.contains(an) || !contentRef.value.contains(fn)) return;
  const t = sel.toString().trim();
  if (t.length < 1) return;

  selectedText = t;
  let n = an;
  while (n && n !== contentRef.value) {
    if (n.nodeName?.match(/^H[1-4]$/)) { selectedSection = n.textContent || ""; break; }
    n = n.parentElement as any;
  }

  // 保存选区矩形 → 仿蓝色高亮
  const rects: DOMRect[] = [];
  try {
    for (let i = 0; i < sel.rangeCount; i++) {
      const r = sel.getRangeAt(i).getClientRects();
      for (let j = 0; j < r.length; j++) rects.push(r[j].toJSON());
    }
  } catch {}
  fakeSel.value = { visible: true, rects };

  // 用第一个矩形定位 toolbar
  const rc = sel.getRangeAt(0).getBoundingClientRect();
  toolbar.value = { visible: true, x: Math.max(10, rc.left + rc.width / 2 - 70), y: Math.max(10, rc.top - 44) };

  // 清浏览器选区 → 蓝高亮由 fakeSel 维持
  sel.removeAllRanges();
}

function doAddNote() { if (selectedText && props.onAddNote) props.onAddNote(selectedText, selectedSection); toolbar.value.visible = false; fakeSel.value.visible = false; }
function doAskAI() { if (selectedText && props.onAskAI) props.onAskAI(selectedText, selectedSection); toolbar.value.visible = false; fakeSel.value.visible = false; }

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

  // 滚动时隐藏仿高亮
  fakeSel.value.visible = false;
}
function scrollToHeading(id: string) { contentRef.value?.querySelector(`#${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" }); }
defineExpose({ scrollToHeading });

onMounted(() => {
  document.addEventListener("mouseup", onGlobalMouseUp);
  globalThis.addEventListener("scroll", updateScrollY, true);
});
onBeforeUnmount(() => {
  document.removeEventListener("mouseup", onGlobalMouseUp);
  globalThis.removeEventListener("scroll", updateScrollY, true);
});
</script>

<style scoped>
.prose :deep(h1), .prose :deep(h2), .prose :deep(h3) { scroll-margin-top: 80px; }
.prose :deep(pre) { background: #1e1e2e; color: #cdd6f4; border-radius: 0.5rem; padding: 1rem; overflow-x: auto; }
.prose :deep(pre code) { color: #cdd6f4; font-size: 0.875em; }
.prose :deep(code) { font-size: 0.875em; }
.prose :deep(.katex) { font-size: 1.1em; }
</style>
