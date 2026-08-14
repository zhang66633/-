<template>
  <div class="flex items-center justify-between border-b px-4 py-2 shrink-0 bg-muted/20">
    <div class="flex items-center gap-2 min-w-0">
      <span
        v-if="!editing"
        class="text-sm font-medium truncate"
        :class="title ? 'text-foreground' : 'text-muted-foreground'"
        @dblclick="startEdit"
      >
        {{ title || "新对话" }}
      </span>
      <input
        v-else
        ref="editInput"
        v-model="editValue"
        class="text-sm font-medium bg-background border border-primary/30 rounded px-1.5 py-0.5 outline-none min-w-0"
        @keyup.enter="confirmEdit"
        @keyup.escape="cancelEdit"
        @blur="confirmEdit"
      />
    </div>
    <div class="flex items-center gap-1 shrink-0">
      <button
        class="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
        title="新建对话"
        @click="$emit('new-session')"
      >
        <Plus class="h-4 w-4" />
      </button>
      <button
        v-if="(messagesCount ?? 0) > 0"
        class="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
        title="导出"
        @click="$emit('export')"
      >
        <Download class="h-3.5 w-3.5" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Download, Plus } from "lucide-vue-next";
import { nextTick, ref } from "vue";

defineProps<{
  title?: string;
  messagesCount?: number;
}>();

defineEmits<{
  "new-session": [];
  export: [];
  "update:title": [title: string];
}>();

const editing = ref(false);
const editValue = ref("");
const editInput = ref<HTMLInputElement>();

function startEdit() {
  editValue.value = "";
  editing.value = true;
  nextTick(() => editInput.value?.focus());
}

function confirmEdit() {
  editing.value = false;
  // emit title change
}

function cancelEdit() {
  editing.value = false;
}
</script>