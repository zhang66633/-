<template>
  <div class="mt-10 border-t pt-6">
    <p class="font-display text-lg font-medium mb-1">🧩 单元自测</p>
    <p class="mb-5 text-xs text-muted-foreground">
      学完本单元,来几道选择题检验一下 — 答错会自动进入训练场错题本
    </p>

    <div v-if="loading" class="flex items-center gap-2 py-6 text-sm text-muted-foreground">
      <Loader2 class="h-4 w-4 animate-spin" />自测题加载中…
    </div>
    <div v-else-if="error" class="rounded-md border border-destructive/30 bg-destructive/5 p-4 text-sm text-muted-foreground">
      <p>自测题加载失败: {{ error }}</p>
      <button
        class="mt-2 cursor-pointer rounded-md border border-border px-3 py-1 text-xs text-foreground transition-colors hover:bg-accent"
        @click="load"
      >
        重试
      </button>
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

      <!-- 全部答完的总结 -->
      <div v-if="allDone" class="rounded-md border border-primary/30 bg-primary/5 px-4 py-3 text-sm">
        <span class="font-medium">本轮自测: {{ correctCount }}/{{ questions.length }} 正确</span>
        <span v-if="correctCount === questions.length" class="ml-2 text-muted-foreground">🎉 全对,可以标记本单元完成了</span>
        <span v-else class="ml-2 text-muted-foreground">建议复习错题后再标记完成</span>
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
import { computed, onMounted, reactive, ref, watch } from "vue";

const props = defineProps<{
  unitId: string;
}>();

const emit = defineEmits<{
  /** 全部答完时触发 */
  complete: [payload: { correct: number; total: number }];
}>();

const loading = ref(false);
const error = ref("");
const questions = ref<QuizQuestion[]>([]);
const choices = reactive<(number | null)[]>([]);
interface QuizResult {
  correct: boolean;
  chosen: number;
  answerIndex: number;
  explanation: string;
}
const results = reactive<(QuizResult | null)[]>([]);

const answeredCount = computed(() => results.filter((r) => r !== null).length);
const correctCount = computed(() => results.filter((r) => r?.correct).length);
const allDone = computed(
  () =>
    questions.value.length > 0 &&
    answeredCount.value === questions.value.length,
);

// 全部答完 → 通知父页面(如 toast)
watch(allDone, (done) => {
  if (done) {
    emit("complete", {
      correct: correctCount.value,
      total: questions.value.length,
    });
  }
});

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

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const res = await fetchUnitQuiz(props.unitId);
    questions.value = res.data.questions;
    for (let i = 0; i < questions.value.length; i++) {
      choices[i] = null;
      results[i] = null;
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "网络异常";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>
