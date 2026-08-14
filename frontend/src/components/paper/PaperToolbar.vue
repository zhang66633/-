<script setup lang="ts">
import { Clipboard, FileDown, Moon, Printer, Sun, Type } from "lucide-vue-next";
import { ref } from "vue";

const props = defineProps<{
  markdown: string;
  taskId?: string;
}>();

const emit = defineEmits<{
  close: [];
}>();

const fontSize = ref<"sm" | "md" | "lg">("md");
const isDark = ref(document.documentElement.classList.contains("dark"));

const fontSizeClass = {
  sm: "text-sm",
  md: "text-base",
  lg: "text-lg",
} as const;

function toggleDark() {
  isDark.value = !isDark.value;
  document.documentElement.classList.toggle("dark", isDark.value);
}

function cycleFontSize() {
  const sizes: Array<"sm" | "md" | "lg"> = ["sm", "md", "lg"];
  const idx = sizes.indexOf(fontSize.value);
  fontSize.value = sizes[(idx + 1) % sizes.length];
}

const fontLabel = { sm: "小", md: "中", lg: "大" } as const;

const copied = ref(false);
async function copyMarkdown() {
  try {
    await navigator.clipboard.writeText(props.markdown);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 1500);
  } catch {
    /* ignore */
  }
}

function exportPdf() {
  import("@/utils/exportPaper").then(({ exportPaperAsPDF }) => {
    exportPaperAsPDF({ title: "数学建模论文", markdown: props.markdown });
  });
}

function downloadMd() {
  const blob = new Blob([props.markdown], {
    type: "text/markdown;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "paper.md";
  a.click();
  URL.revokeObjectURL(url);
}

async function downloadDocx() {
  if (!props.taskId) return;
  try {
    const { default: request } = await import("@/utils/request");
    const resp = await request.get(`/tasks/${props.taskId}/export`, {
      params: { format: "docx" },
      responseType: "blob",
    });
    const blob = new Blob([resp.data]);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "paper.docx";
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    console.error("下载 DOCX 失败:", e);
  }
}

defineExpose({ fontSizeClass, fontSize });
</script>

<template>
  <div class="flex items-center gap-1.5 px-3 py-2 border-b border-border bg-background/80 backdrop-blur shrink-0">
    <!-- 导出 PDF -->
    <button
      class="inline-flex h-7 items-center gap-1 rounded-md border border-border bg-background px-2.5 text-xs hover:bg-accent transition-colors"
      title="在新窗口中打开论文并打印为 PDF"
      @click="exportPdf"
    >
      <Printer class="h-3 w-3" />
      <span class="hidden sm:inline">PDF</span>
    </button>

    <!-- 复制 Markdown -->
    <button
      class="inline-flex h-7 items-center gap-1 rounded-md border border-border bg-background px-2.5 text-xs hover:bg-accent transition-colors"
      title="复制论文 Markdown 源"
      @click="copyMarkdown"
    >
      <Clipboard class="h-3 w-3" />
      <span class="hidden sm:inline">{{ copied ? "已复制" : "复制" }}</span>
    </button>

    <!-- 下载 .md -->
    <button
      class="inline-flex h-7 items-center gap-1 rounded-md border border-border bg-background px-2.5 text-xs hover:bg-accent transition-colors"
      title="下载 Markdown 文件"
      @click="downloadMd"
    >
      <FileDown class="h-3 w-3" />
      <span class="hidden sm:inline">.md</span>
    </button>

    <!-- 下载 .docx -->
    <button
      v-if="taskId"
      class="inline-flex h-7 items-center gap-1 rounded-md border border-border bg-background px-2.5 text-xs hover:bg-accent transition-colors"
      title="下载 Word 文档"
      @click="downloadDocx"
    >
      <FileDown class="h-3 w-3" />
      <span class="hidden sm:inline">.docx</span>
    </button>

    <div class="flex-1" />

    <!-- 字体大小切换 -->
    <button
      class="inline-flex h-7 w-7 items-center justify-center rounded-md border border-border bg-background hover:bg-accent transition-colors"
      :title="`字体大小: ${fontLabel[fontSize]}`"
      @click="cycleFontSize"
    >
      <Type class="h-3 w-3" />
      <span class="text-[10px] ml-0.5">{{ fontLabel[fontSize] }}</span>
    </button>

    <!-- 深色/浅色切换 -->
    <button
      class="inline-flex h-7 w-7 items-center justify-center rounded-md border border-border bg-background hover:bg-accent transition-colors"
      :title="isDark ? '切换到浅色模式' : '切换到深色模式'"
      @click="toggleDark"
    >
      <Sun v-if="isDark" class="h-3 w-3" />
      <Moon v-else class="h-3 w-3" />
    </button>
  </div>
</template>