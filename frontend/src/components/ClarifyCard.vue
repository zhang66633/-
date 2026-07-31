<template>
  <div class="space-y-4 min-w-[300px] max-w-lg">
    <div v-for="(q, qi) in questions" :key="qi" class="space-y-2">
      <p class="text-sm font-medium text-foreground">{{ q.question }}</p>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="(opt, oi) in q.options"
          :key="oi"
          :class="[
            'inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs transition-colors',
            isSelected(qi, oi)
              ? 'border-foreground bg-foreground text-background'
              : 'border-border bg-background text-foreground hover:bg-accent',
            answered ? 'pointer-events-none opacity-60' : 'cursor-pointer',
          ]"
          @click="toggleSelect(qi, oi, q.multiSelect)"
        >
          <span>{{ opt.label }}</span>
          <span v-if="opt.description" class="text-[10px] opacity-60 hidden sm:inline">({{ opt.description }})</span>
        </button>
      </div>
    </div>
    <button
      v-if="!answered"
      :disabled="!allAnswered"
      class="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-background px-4 text-xs font-medium hover:bg-accent transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      @click="confirm"
    >
      确认选择
    </button>
    <div v-else class="text-xs text-muted-foreground font-mono">已回答</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject } from "vue";
import type { ClarifyQuestion } from "@/types/response";

const props = withDefaults(
  defineProps<{
    questions: ClarifyQuestion[];
    answered?: boolean;
  }>(),
  { answered: false },
);

// 注入 ChatArea 提供的发送函数
const sendHandler = inject<((text: string) => void) | null>("chatSendHandler", null);

// 每个问题的选中状态: Map<questionIndex, Set<optionIndex>>
const selections = ref<Map<number, Set<number>>>(new Map());

function isSelected(qi: number, oi: number): boolean {
  return selections.value.get(qi)?.has(oi) ?? false;
}

function toggleSelect(qi: number, oi: number, multiSelect?: boolean) {
  if (props.answered) return;
  const s = new Map(selections.value);
  if (!s.has(qi)) s.set(qi, new Set());
  const opts = new Set(s.get(qi)!);
  if (multiSelect) {
    if (opts.has(oi)) opts.delete(oi);
    else opts.add(oi);
  } else {
    opts.clear();
    opts.add(oi);
  }
  s.set(qi, opts);
  selections.value = s;
}

const allAnswered = computed(() => {
  return props.questions.every((_, qi) => (selections.value.get(qi)?.size ?? 0) > 0);
});

function confirm() {
  if (!allAnswered.value || props.answered) return;

  // 格式化为自然语言
  const lines: string[] = [];
  for (let qi = 0; qi < props.questions.length; qi++) {
    const q = props.questions[qi];
    const selected = selections.value.get(qi);
    if (!selected || selected.size === 0) continue;
    const labels = [...selected].map((oi) => q.options[oi].label);
    lines.push(`${q.question}：${labels.join("、")}`);
  }
  const text = lines.join("；");

  // 通过注入的 send handler 发送消息（ChatArea 已正确 provide）
  if (sendHandler) {
    sendHandler(text);
  }
}
</script>
