<template>
  <div class="mt-10 border-t pt-6">
    <p class="font-display text-lg font-medium mb-1">🧩 单元自测</p>
    <p class="mb-5 text-xs text-muted-foreground">
      学完本单元,来几道选择题检验一下 — 答错会自动进入训练场错题本
    </p>

    <div v-if="loading" class="flex items-center gap-2 py-6 text-sm text-muted-foreground">
      <Loader2 class="h-4 w-4 animate-spin" />自测题加载中…
    </div>
    <div v-else-if="questions.length === 0" class="rounded-md border border-border bg-card p-4 text-sm text-muted-foreground">
      本单元的自测题正在编写中,稍后再来看看吧。
    </div>
    <div v-else class="space-y-8">
      <div v-for="(q, qi) in questions" :key="q.id">
        <p class="mb-1 text-xs text-muted-foreground">
          第 {{ qi + 1 }} 题
          <span
            v-if="results[qi]"
            class="ml-2 font-medium"
            :class="results[qi].correct ? 'text-emerald-500' : 'text-red-500'"
          >
            {{ results[qi].correct ? "✓ 回答正确" : "✗ 回答错误" }}
          </span>
        </p>
        <div class="mb-3 text-sm leading-relaxed" v-html="renderMarkdown(q.question)" />
        <GuidedCardSelection
          v-model="choices[qi]"
          mode="quiz"
          :options="q.options.map((label) => ({ label }))"
          :disabled="!!results[qi]"
          :reveal="results[qi] ? { answerIndex: results[qi].answerIndex, chosenIndex: results[qi].chosen } : null"
          @confirm="(i: number) => onAnswer(qi, i)"
        />
        <div v-if="results[qi]" class="mt-3 rounded-md border border-border bg-card p-3.5 text-sm leading-relaxed">
          <p class="mb-1.5 text-xs font-medium text-muted-foreground">📖 解析</p>
          <div v-html="renderMarkdown(results[qi].explanation)" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  type QuizQuestion,
  fetchUnitQuiz,
  submitQuizAnswer,
} from "@/apis/learningApi";
import { renderMarkdown } from "@/utils/markdown";
import { Loader2 } from "lucide-vue-next";
import { onMounted, reactive, ref } from "vue";

const props = defineProps<{
  unitId: string;
}>();

const loading = ref(false);
const questions = ref<QuizQuestion[]>([]);
const choices = reactive<(number | null)[]>([]);
interface QuizResult {
  correct: boolean;
  chosen: number;
  answerIndex: number;
  explanation: string;
}
const results = reactive<(QuizResult | null)[]>([]);

async function onAnswer(qi: number, choice: number) {
  const q = questions.value[qi];
  if (!q || results[qi]) return;
  const res = await submitQuizAnswer(q.id, choice);
  results[qi] = {
    correct: res.data.correct,
    chosen: choice,
    answerIndex: res.data.answer_index,
    explanation: res.data.explanation,
  };
}

onMounted(async () => {
  loading.value = true;
  try {
    const res = await fetchUnitQuiz(props.unitId);
    questions.value = res.data.questions;
    for (let i = 0; i < questions.value.length; i++) {
      choices[i] = null;
      results[i] = null;
    }
  } finally {
    loading.value = false;
  }
});
</script>
