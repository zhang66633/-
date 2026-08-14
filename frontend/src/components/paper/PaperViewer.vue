<script setup lang="ts">
/**
 * PaperViewer — 全屏论文阅读器
 *
 * 左右两栏布局：左侧 TOC 导航 + 右侧论文正文
 * 顶部工具栏：导出/复制/下载/字体/模式
 * 滚动时自动高亮当前章节（IntersectionObserver）
 */
import { computed, ref, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import { X } from "lucide-vue-next";
import PaperToc from "./PaperToc.vue";
import PaperToolbar from "./PaperToolbar.vue";
import { renderMarkdownAsync } from "@/utils/markdown";
import "@/assets/paper.css";

const props = defineProps<{
  markdown: string;
  taskId?: string;
}>();

const emit = defineEmits<{
  close: [];
}>();

const renderedHtml = ref("");
const contentRef = ref<HTMLElement | null>(null);
const tocRef = ref<InstanceType<typeof PaperToc> | null>(null);

// 异步渲染：支持代码语法高亮
watch(
  () => props.markdown,
  async (md) => {
    renderedHtml.value = await renderMarkdownAsync(md);
    await nextTick();
    setupIntersectionObserver();
  },
  { immediate: true },
);

// ---- IntersectionObserver: 滚动时高亮当前章节 ----
let observer: IntersectionObserver | null = null;

function setupIntersectionObserver() {
  if (observer) observer.disconnect();
  if (!contentRef.value) return;

  observer = new IntersectionObserver(
    (entries) => {
      // 找到第一个可见的标题
      const visible = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);

      if (visible.length > 0) {
        const id = visible[0].target.id;
        tocRef.value?.setActiveId(id);
      }
    },
    { rootMargin: "-80px 0px -60% 0px" },
  );

  const headings = contentRef.value.querySelectorAll("h1[id], h2[id], h3[id]");
  headings.forEach((h) => observer!.observe(h));
}

onBeforeUnmount(() => {
  if (observer) observer.disconnect();
});

// 工具栏字体大小
const toolbarRef = ref<InstanceType<typeof PaperToolbar> | null>(null);
const fontSizeClass = computed(() => toolbarRef.value?.fontSizeClass ?? "text-base");
const fontSize = computed(() => toolbarRef.value?.fontSize ?? "md");

// ESC 关闭
function onKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") emit("close");
}

// 代码块复制：事件委托处理 data-code-id 按钮（onclick 会被 DOMPurify 剥离，故改用委托）
async function onContentClick(e: MouseEvent) {
  const btn = (e.target as Element | null)?.closest<HTMLElement>("[data-code-id]");
  if (!btn) return;
  const codeId = btn.dataset.codeId;
  if (!codeId) return;
  try {
    await navigator.clipboard.writeText(document.getElementById(codeId)?.textContent ?? "");
  } catch { /* 剪贴板不可用则忽略 */ }
}

onMounted(() => {
  document.addEventListener("keydown", onKeydown);
  document.body.style.overflow = "hidden";
});

onBeforeUnmount(() => {
  document.removeEventListener("keydown", onKeydown);
  document.body.style.overflow = "";
});
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex flex-col bg-background"
      role="dialog"
      aria-label="论文阅读器"
    >
      <!-- 顶部工具栏 -->
      <PaperToolbar
        ref="toolbarRef"
        :markdown="markdown"
        :task-id="taskId"
      />

      <!-- 主内容区：TOC + 正文 -->
      <div class="flex flex-1 min-h-0">
        <!-- 左侧目录 -->
        <PaperToc ref="tocRef" :html="renderedHtml" />

        <!-- 右侧正文 -->
        <div class="flex-1 overflow-y-auto">
          <div class="max-w-[820px] mx-auto px-6 py-8">
            <article
              ref="contentRef"
              :class="[
                'paper-content prose dark:prose-invert max-w-none',
                fontSizeClass,
                fontSize === 'sm' ? 'prose-sm' : fontSize === 'lg' ? 'prose-lg' : '',
              ]"
              v-html="renderedHtml"
              @click="onContentClick"
            />
          </div>
        </div>
      </div>

      <!-- 关闭按钮（右下角浮动） -->
      <button
        class="fixed bottom-6 right-6 z-50 inline-flex h-10 w-10 items-center justify-center rounded-full bg-card border border-border shadow-lg hover:bg-accent transition-colors"
        title="关闭 (Esc)"
        @click="emit('close')"
      >
        <X class="h-5 w-5" />
      </button>
    </div>
  </Teleport>
</template>