<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between">
      <span v-if="label" class="text-sm font-medium">{{ label }}</span>
      <button class="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground" @click="add">
        <Plus class="h-3 w-3" /> 添加
      </button>
    </div>
    <div v-for="(item, i) in items" :key="i" class="flex gap-2 items-start">
      <!-- 简单模式：每行一个输入框 -->
      <template v-if="!fields">
        <Input :model-value="item" :placeholder="placeholder" class="flex-1 h-8 text-sm" @update:model-value="(v) => updateItem(i, v)" />
      </template>
      <!-- 结构化模式：每行多字段 -->
      <div v-else class="flex-1 flex flex-wrap gap-2 p-2 border border-border rounded-md">
        <template v-for="f in fields" :key="f.key">
          <Input v-if="f.type !== 'textarea'" :model-value="item[f.key]" :placeholder="f.placeholder || f.label" class="h-8 text-sm" :class="fields.length <= 2 ? 'flex-1 min-w-[120px]' : 'w-full'" @update:model-value="(v) => updateField(i, f.key, v)" />
          <Textarea v-else :model-value="item[f.key]" :placeholder="f.placeholder || f.label" class="text-sm w-full" rows="3" @update:model-value="(v) => updateField(i, f.key, v)" />
        </template>
      </div>
      <button class="mt-0.5 shrink-0 text-muted-foreground hover:text-destructive" @click="remove(i)">
        <Trash2 class="h-3.5 w-3.5" />
      </button>
    </div>
    <p v-if="!items.length" class="text-xs text-muted-foreground italic">暂无，点击「添加」新增</p>
  </div>
</template>

<script setup lang="ts">
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Trash2 } from "lucide-vue-next";
import { computed } from "vue";

interface FieldDef {
  key: string;
  label: string;
  placeholder?: string;
  type?: "text" | "textarea";
}

const props = withDefaults(
  defineProps<{
    modelValue: any[];
    fields?: FieldDef[]; // 提供则结构化模式，不提供则简单模式
    label?: string;
    placeholder?: string;
    emptyValue?: any;
  }>(),
  { emptyValue: "" },
);

const emit = defineEmits<{ "update:modelValue": [v: any[]] }>();

const items = computed(() => props.modelValue);

function add() {
  const empty =
    props.fields && props.fields.length > 0
      ? Object.fromEntries(props.fields.map((f) => [f.key, ""]))
      : props.emptyValue;
  emit("update:modelValue", [...items.value, empty]);
}

function remove(i: number) {
  const next = [...items.value];
  next.splice(i, 1);
  emit("update:modelValue", next);
}

function updateItem(i: number, value: any) {
  const next = [...items.value];
  next[i] = value;
  emit("update:modelValue", next);
}

function updateField(i: number, key: string, value: any) {
  const next = [...items.value];
  next[i] = { ...next[i], [key]: value };
  emit("update:modelValue", next);
}
</script>
