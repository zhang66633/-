<template>
  <div class="flex flex-col h-full relative">
    <div ref="scrollRef" class="flex-1 overflow-y-auto px-4 sm:px-8 py-6 space-y-1">
      <slot name="progress" />

      <div v-if="messages.length === 0 && !isRunning" class="flex flex-col justify-center h-full max-w-md mx-auto px-4">
        <p class="font-display text-xl text-muted-foreground">{{ emptyText }}</p>
        <p class="text-sm text-muted-foreground/70 mt-1">{{ emptySubtext }}</p>
      </div>

      <div v-if="isConnecting" class="space-y-4">
        <div v-for="i in 3" :key="i" class="flex items-start gap-3 animate-pulse">
          <div class="h-8 w-8 rounded-sm border border-border" />
          <div class="space-y-2 flex-1">
            <div class="h-3 bg-muted rounded w-1/4" />
            <div class="h-3 bg-muted rounded w-3/4" />
          </div>
        </div>
      </div>

      <Bubble
        v-for="(msg, idx) in messages"
        :key="msg.id || idx"
        :message="msg"
        :is-last="idx === messages.length - 1"
      />

      <div v-if="isRunning" class="flex items-center gap-3 pl-1 py-2">
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border border-border">
          <Brain class="h-4 w-4 text-muted-foreground" />
        </div>
        <div class="flex items-center gap-1.5 rounded-md border border-border bg-background px-4 py-3">
          <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mr-2">思考中</span>
          <span class="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-bounce" style="animation-delay: 0ms" />
          <span class="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-bounce" style="animation-delay: 150ms" />
          <span class="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-bounce" style="animation-delay: 300ms" />
        </div>
        <button
          v-if="cancellable"
          class="ml-2 inline-flex h-7 items-center gap-1 rounded-md border border-border bg-background px-2.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground transition-colors disabled:opacity-50"
          :disabled="cancelling"
          @click="$emit('cancel')"
        >
          <Square class="h-3 w-3" />
          <span>{{ cancelling ? "停止中…" : "停止" }}</span>
        </button>
      </div>

      <div ref="bottomRef" />
    </div>

    <Transition name="fade">
      <button
        v-if="!isAtBottom"
        class="absolute bottom-24 right-6 h-9 w-9 rounded-md border border-border bg-background/80 backdrop-blur flex items-center justify-center hover:bg-accent transition-colors z-10"
        @click="scrollToBottom"
      >
        <ArrowDown class="h-4 w-4" />
      </button>
    </Transition>

    <div class="border-t border-border bg-background p-4">
      <!-- 附件预览 -->
      <div v-if="attachedFiles.length > 0" class="flex flex-wrap gap-2 mb-2">
        <div
          v-for="(f, i) in attachedFiles"
          :key="f.file_id"
          class="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted/40 px-2.5 py-1 text-xs"
        >
          <Paperclip class="h-3 w-3 text-muted-foreground" />
          <span class="max-w-[160px] truncate">{{ f.filename }}</span>
          <button
            class="ml-0.5 text-muted-foreground hover:text-foreground transition-colors"
            @click="removeFile(i)"
          >
            <X class="h-3 w-3" />
          </button>
        </div>
      </div>
      <div class="flex items-end gap-2">
        <!-- 附件按钮 -->
        <button
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-background hover:bg-accent transition-colors disabled:opacity-50"
          :disabled="isRunning || uploading"
          title="上传文件（CSV/Excel/TXT/PDF 等）"
          @click="triggerFileInput"
        >
          <Loader2 v-if="uploading" class="h-4 w-4 animate-spin" />
          <Paperclip v-else class="h-4 w-4" />
        </button>
        <input
          ref="fileInputRef"
          type="file"
          class="hidden"
          multiple
          accept=".csv,.xlsx,.xls,.txt,.md,.json,.pdf,.py,.dat,.tsv"
          @change="onFileSelected"
        />
        <!-- 导出按钮 -->
        <button
          v-if="messages.length > 0"
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-background hover:bg-accent transition-colors"
          title="导出对话 (Markdown)"
          @click="$emit('export')"
        >
          <Download class="h-4 w-4" />
        </button>
        <textarea
          v-model="inputText"
          class="flex min-h-10 max-h-40 w-full resize-none rounded-md border border-border bg-background px-4 py-2.5 text-sm leading-relaxed placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          :placeholder="inputPlaceholder"
          rows="1"
          :disabled="isRunning"
          @keydown.enter.exact.prevent="sendMessage"
          @input="autoResize"
          ref="textareaRef"
        />
        <button
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-foreground text-background hover:bg-foreground/90 transition-colors disabled:opacity-50"
          :disabled="(!inputText.trim() && attachedFiles.length === 0) || isRunning"
          @click="sendMessage"
        >
          <Send v-if="!isRunning" class="h-4 w-4" />
          <Loader2 v-else class="h-4 w-4 animate-spin" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick, computed, provide } from "vue";
import { Brain, ArrowDown, Send, Loader2, Square, Paperclip, X, Download } from "lucide-vue-next";
import { useTaskStore } from "@/stores/task";
import Bubble from "@/components/Bubble.vue";
import type { Message } from "@/types/response";
import { uploadChatFile, type ChatFileRef } from "@/apis/chatApi";

const props = withDefaults(defineProps<{
  messages: Message[];
  isRunning?: boolean;
  emptyText?: string;
  emptySubtext?: string;
  inputPlaceholder?: string;
  cancellable?: boolean;
  cancelling?: boolean;
}>(), {
  isRunning: false,
  emptyText: "开始对话",
  emptySubtext: "在下方输入你的问题",
  inputPlaceholder: "输入消息...",
  cancellable: false,
  cancelling: false,
});

const emit = defineEmits<{
  send: [text: string, files?: ChatFileRef[]];
  cancel: [];
  export: [];
}>();

// 提供给 ClarifyCard 注入的发送函数（澄清选项确认后直接发送）
provide("chatSendHandler", (text: string) => {
  emit("send", text);
});

const taskStore = useTaskStore();

const isConnecting = computed(() =>
  taskStore.wsStatus === "connecting" || taskStore.wsStatus === "reconnecting",
);

const inputText = ref("");
const scrollRef = ref<HTMLElement | null>(null);
const bottomRef = ref<HTMLElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);
const isAtBottom = ref(true);

// 附件状态
const attachedFiles = ref<ChatFileRef[]>([]);
const uploading = ref(false);

function triggerFileInput() {
  fileInputRef.value?.click();
}

async function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement;
  const files = input.files;
  if (!files || files.length === 0) return;

  uploading.value = true;
  try {
    for (const file of Array.from(files)) {
      if (file.size > 20 * 1024 * 1024) {
        alert(`文件 ${file.name} 超过 20MB 限制`);
        continue;
      }
      const ref = await uploadChatFile(file);
      attachedFiles.value.push(ref);
    }
  } catch (err: any) {
    alert(`文件上传失败: ${err?.message ?? err}`);
  } finally {
    uploading.value = false;
    // 清空 input 以允许重复选择同一文件
    input.value = "";
  }
}

function removeFile(index: number) {
  attachedFiles.value.splice(index, 1);
}

function autoResize() {
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 160) + "px";
}

function scrollToBottom() {
  bottomRef.value?.scrollIntoView({ behavior: "smooth" });
}

function sendMessage() {
  const text = inputText.value.trim();
  if ((!text && attachedFiles.value.length === 0) || props.isRunning) return;
  const files = attachedFiles.value.length > 0 ? [...attachedFiles.value] : undefined;
  emit("send", text, files);
  inputText.value = "";
  attachedFiles.value = [];
  nextTick(() => {
    const el = textareaRef.value;
    if (el) el.style.height = "auto";
  });
}

function onScroll() {
  const el = scrollRef.value;
  if (!el) return;
  const threshold = 100;
  isAtBottom.value = el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
}

watch(
  () => props.messages.length,
  () => {
    if (isAtBottom.value) {
      nextTick(() => scrollToBottom());
    }
  },
);

onMounted(() => {
  scrollRef.value?.addEventListener("scroll", onScroll);
});

onUnmounted(() => {
  scrollRef.value?.removeEventListener("scroll", onScroll);
});
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
