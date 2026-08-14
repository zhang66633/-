<template>
  <div class="flex flex-col h-full">
    <!-- 标题栏 -->
    <div class="flex items-center justify-between px-3 py-2 border-b shrink-0">
      <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        🔖 我的笔记 ({{ notes.length }})
      </span>
      <button
        class="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
        @click="$emit('addBlank')"
      >
        + 新建
      </button>
    </div>

    <!-- 笔记列表 -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="notes.length === 0" class="px-3 py-6 text-center text-[11px] text-muted-foreground">
        选中学习文档中的文字，<br />点击「笔记」即可记录
      </div>

      <div v-for="(note, i) in notes" :key="i" class="border-b border-border/50">
        <!-- 编辑模式 -->
        <div v-if="editingIndex === i" class="p-2">
          <input
            v-model="editTitle"
            class="w-full text-xs font-medium bg-transparent border-b border-primary/30 px-1 py-0.5 mb-1 outline-none"
            placeholder="笔记标题"
            @keyup.enter="saveEdit(i)"
            @keyup.escape="editingIndex = -1"
          />
          <textarea
            v-model="editComment"
            class="w-full text-xs bg-transparent border border-border rounded px-2 py-1 mt-1 resize-none outline-none"
            rows="3"
            placeholder="补充你的想法..."
          />
          <div class="flex gap-1 mt-1.5">
            <button class="text-[10px] px-2 py-0.5 rounded bg-primary text-primary-foreground" @click="saveEdit(i)">保存</button>
            <button class="text-[10px] px-2 py-0.5 rounded border" @click="editingIndex = -1">取消</button>
          </div>
        </div>

        <!-- 浏览模式 -->
        <button
          v-else
          class="w-full text-left p-2 hover:bg-accent/30 transition-colors group"
          @click="jumpToNote(note)"
        >
          <div class="flex items-start justify-between gap-1">
            <p class="text-xs font-medium truncate flex-1">{{ note.title || '未命名笔记' }}</p>
            <div class="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
              <button class="p-0.5 hover:bg-accent rounded" @click.stop="startEdit(i)" title="编辑">
                <Pencil class="h-3 w-3 text-muted-foreground" />
              </button>
              <button class="p-0.5 hover:bg-destructive/10 rounded" @click.stop="removeNote(i)" title="删除">
                <X class="h-3 w-3 text-muted-foreground" />
              </button>
            </div>
          </div>
          <p class="text-[10px] text-muted-foreground mt-0.5 line-clamp-2">{{ note.quote }}</p>
          <p v-if="note.section" class="text-[9px] text-muted-foreground/60 mt-0.5">📍 {{ note.section }}</p>
          <p v-if="note.comment" class="text-[10px] text-primary/80 mt-0.5 italic">{{ note.comment }}</p>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Pencil, X } from "lucide-vue-next";
import { ref } from "vue";

export interface NoteItem {
  title: string;
  quote: string;
  section: string;
  comment: string;
  headingId: string;
}

const props = defineProps<{
  notes: NoteItem[];
}>();

const emit = defineEmits<{
  addBlank: [];
  update: [index: number, note: NoteItem];
  remove: [index: number];
  jumpTo: [headingId: string];
}>();

const editingIndex = ref(-1);
const editTitle = ref("");
const editComment = ref("");

function startEdit(i: number) {
  editingIndex.value = i;
  editTitle.value = props.notes[i].title;
  editComment.value = props.notes[i].comment;
}

function saveEdit(i: number) {
  emit("update", i, {
    ...props.notes[i],
    title: editTitle.value || props.notes[i].title,
    comment: editComment.value,
  });
  editingIndex.value = -1;
}

function removeNote(i: number) {
  emit("remove", i);
}

function jumpToNote(note: NoteItem) {
  if (note.headingId) emit("jumpTo", note.headingId);
}
</script>
