<script setup lang="ts">
/**
 * PaperCard — 在聊天中显示论文摘要卡片，替代全文渲染。
 * 点击"阅读全文"打开 PaperViewer。
 */
import { computed } from "vue";
import { BookOpen, FileText, Clock } from "lucide-vue-next";

const props = defineProps<{
  markdown: string;
}>();

const emit = defineEmits<{
  open: [];
}>();

/** 提取标题（第一个 # 开头行） */
const title = computed(() => {
  const m = props.markdown.match(/^#\s+(.+)$/m);
  return m ? m[1].trim() : "数学建模论文";
});

/** 提取摘要（"## 摘要" 之后的内容，截取前 200 字） */
const abstract = computed(() => {
  const m = props.markdown.match(/##\s*摘要\s*\n([\s\S]*?)(?=\n##\s|$)/i);
  if (!m) return "";
  const text = m[1].replace(/[#*`$\\[\]()>]/g, "").trim();
  return text.length > 200 ? text.slice(0, 200) + "…" : text;
});

const wordCount = computed(() => props.markdown.length);
</script>

<template>
  <div class="rounded-lg border border-border bg-card p-4 space-y-3 hover:border-primary/30 transition-colors">
    <!-- 标题行 -->
    <div class="flex items-start gap-2">
      <BookOpen class="h-4 w-4 text-primary mt-0.5 shrink-0" />
      <div class="flex-1 min-w-0">
        <h3 class="text-sm font-semibold text-foreground leading-snug line-clamp-2">
          {{ title }}
        </h3>
      </div>
    </div>

    <!-- 摘要预览 -->
    <p v-if="abstract" class="text-xs text-muted-foreground leading-relaxed line-clamp-3">
      {{ abstract }}
    </p>

    <!-- 元信息 + 按钮 -->
    <div class="flex items-center justify-between gap-2">
      <div class="flex items-center gap-3 text-[11px] text-muted-foreground">
        <span class="flex items-center gap-1">
          <FileText class="h-3 w-3" />
          {{ wordCount.toLocaleString() }} 字
        </span>
        <span class="flex items-center gap-1">
          <Clock class="h-3 w-3" />
          已生成
        </span>
      </div>
      <button
        class="inline-flex h-8 items-center gap-1.5 rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        @click="emit('open')"
      >
        <BookOpen class="h-3 w-3" />
        阅读全文
      </button>
    </div>
  </div>
</template>