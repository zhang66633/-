<template>
  <div class="space-y-4 min-w-[220px] max-w-full">
    <div v-for="(q, qi) in questions" :key="qi" class="space-y-2">
      <p class="text-sm font-medium text-foreground">{{ q.question }}</p>
      <div class="flex flex-col gap-1.5">
        <button
          v-for="(opt, oi) in q.options"
          :key="oi"
          type="button"
          class="relative flex cursor-pointer items-start gap-2 rounded-lg border px-3.5 py-2.5 text-left transition-all duration-150"
          :class="isSelected(qi, oi)
            ? 'border-primary bg-primary/5 ring-1 ring-primary/30'
            : answered
              ? 'border-border bg-card opacity-60'
              : 'border-border bg-card hover:border-muted-foreground/30 hover:bg-accent/40'"
          :disabled="answered"
          @click="toggleSelect(qi, oi, q.multiSelect)"
        >
          <span
            v-if="isSelected(qi, oi)"
            class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground"
          >
            <Check class="h-3 w-3" />
          </span>
          <span class="min-w-0">
            <span class="block text-sm font-medium text-foreground">{{ opt.label }}</span>
            <span v-if="opt.description" class="mt-0.5 block text-[11px] leading-4 text-muted-foreground">{{ opt.description }}</span>
          </span>
        </button>
      </div>
    </div>
    <button
      v-if="!answered"
      :disabled="!allAnswered"
      class="h-10 cursor-pointer rounded-lg bg-primary px-5 text-sm font-medium text-primary-foreground transition-all duration-150 hover:bg-primary/90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
      @click="confirm"
    >
      确认选择
    </button>
    <div v-else class="text-xs font-mono text-muted-foreground">已回答</div>
  </div>
</template>

<script setup lang="ts">
import type { ClarifyQuestion } from "@/types/response";
import { Check } from "lucide-vue-next";
import { computed, inject, ref } from "vue";

const props = withDefaults(
  defineProps<{
    questions: ClarifyQuestion[];
    answered?: boolean;
  }>(),
  { answered: false },
);

// 注入 ChatArea 提供的发送函数
const sendHandler = inject<((text: string) => void) | null>(
  "chatSendHandler",
  null,
);

// 每个问题的选中状态: Map<questionIndex, Set<optionIndex>>
const selections = ref<Map<number, Set<number>>>(new Map());

function isSelected(qi: number, oi: number): boolean {
  return selections.value.get(qi)?.has(oi) ?? false;
}

function toggleSelect(qi: number, oi: number, multiSelect?: boolean) {
  if (props.answered) return;
  const s = new Map(selections.value);
  if (!s.has(qi)) s.set(qi, new Set());
  const opts = new Set(s.get(qi) ?? []);
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
  return props.questions.every(
    (_, qi) => (selections.value.get(qi)?.size ?? 0) > 0,
  );
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
    lines.push(`${q.question}:${labels.join("、")}`);
  }
  const text = lines.join(";");

  // 通过注入的 send handler 发送消息(ChatArea 已正确 provide)
  if (sendHandler) {
    sendHandler(text);
  }
}
</script>
