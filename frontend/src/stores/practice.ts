import {
  type QuizQuestion,
  addToMistakes,
  discardQuizRound,
  fetchQuizBank,
  fetchQuizMistakes,
  removeFromMistakes,
  startQuizPractice,
  submitQuizAnswer,
} from "@/apis/learningApi";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

export interface AnswerRecord {
  question: QuizQuestion;
  chosen: number;
  correct: boolean;
  answer_index: number;
  explanation: string;
}

export const usePracticeStore = defineStore("practice", () => {
  // ── 题库浏览 ────────────────────────────────────────
  const bank = ref<QuizQuestion[]>([]);
  const categories = ref<{ name: string; count: number }[]>([]);
  const bankTotal = ref(0);
  const bankLoading = ref(false);
  const bankError = ref("");

  // 筛选条件
  const filterRole = ref("");
  const filterCategory = ref("");
  const filterDifficulty = ref("");
  const filterStatus = ref("");
  const searchText = ref("");

  // 勾选
  const selectedIds = ref<Set<string>>(new Set());
  const shuffled = ref(false);

  // ── 一轮练习 ────────────────────────────────────────
  const session = ref<QuizQuestion[]>([]);
  const sessionIndex = ref(0);
  const answers = ref<AnswerRecord[]>([]);
  const sessionStartAt = ref(0);
  const sessionDone = ref(false);
  const roundId = ref("");

  // ── 错题本 ──────────────────────────────────────────
  const mistakes = ref<QuizQuestion[]>([]);
  const mistakesLoading = ref(false);

  // ── 计算属性 ────────────────────────────────────────
  const filteredBank = computed(() => {
    let list = bank.value;
    if (filterRole.value)
      list = list.filter((q) => q.role === filterRole.value);
    if (filterCategory.value)
      list = list.filter((q) => q.category === filterCategory.value);
    if (filterDifficulty.value)
      list = list.filter((q) => q.difficulty === filterDifficulty.value);
    if (filterStatus.value)
      list = list.filter((q) => q.status === filterStatus.value);
    const kw = searchText.value.trim().toLowerCase();
    if (kw)
      list = list.filter(
        (q) =>
          q.question.toLowerCase().includes(kw) ||
          q.tags.some((t) => t.toLowerCase().includes(kw)) ||
          q.category.toLowerCase().includes(kw),
      );
    return list;
  });

  const statusCounts = computed(() => {
    const counts = { untried: 0, wrong: 0, mastered: 0 };
    for (const q of bank.value) counts[q.status] += 1;
    return counts;
  });

  const currentQuestion = computed(
    () => session.value[sessionIndex.value] ?? null,
  );
  const correctCount = computed(
    () => answers.value.filter((a) => a.correct).length,
  );
  const accuracy = computed(() =>
    answers.value.length
      ? Math.round((correctCount.value / answers.value.length) * 100)
      : 0,
  );

  // ── 操作 ────────────────────────────────────────────
  /** 加载题库,带瞬时故障重试(首屏请求并发密集时后端可能暂时 503)。 */
  async function loadBank() {
    bankLoading.value = true;
    bankError.value = "";
    try {
      for (let attempt = 0; ; attempt++) {
        try {
          const res = await fetchQuizBank();
          bank.value = res.data.questions;
          categories.value = res.data.categories;
          bankTotal.value = res.data.total;
          return;
        } catch (err) {
          if (attempt >= 2) throw err;
          await new Promise((r) => setTimeout(r, 600 * (attempt + 1)));
        }
      }
    } catch {
      bankError.value = "题库加载失败,请检查后端服务后重试";
    } finally {
      bankLoading.value = false;
    }
  }

  function toggleSelect(id: string) {
    const s = new Set(selectedIds.value);
    if (s.has(id)) s.delete(id);
    else s.add(id);
    selectedIds.value = s;
  }

  function selectAll() {
    const ids = new Set(filteredBank.value.map((q) => q.id));
    selectedIds.value = ids.size === selectedIds.value.size ? new Set() : ids;
  }

  function clearSelection() {
    selectedIds.value = new Set();
  }

  async function startSession(ids: string[]) {
    const res = await startQuizPractice(ids);
    let questions = res.data.questions;
    if (shuffled.value) {
      questions = [...questions].sort(() => Math.random() - 0.5);
    }
    session.value = questions;
    sessionIndex.value = 0;
    answers.value = [];
    sessionStartAt.value = Date.now();
    sessionDone.value = false;
    roundId.value = `r${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  }

  async function answerQuestion(choice: number): Promise<AnswerRecord | null> {
    const q = currentQuestion.value;
    if (!q) return null;
    const res = await submitQuizAnswer(q.id, choice, roundId.value);
    const record: AnswerRecord = {
      question: q,
      chosen: choice,
      correct: res.data.correct,
      answer_index: res.data.answer_index,
      explanation: res.data.explanation,
    };
    answers.value.push(record);
    // 本地状态同步(错题入本/掌握)
    const inBank = bank.value.find((b) => b.id === q.id);
    if (inBank) {
      inBank.status = res.data.correct ? "mastered" : "wrong";
      if (!res.data.correct) inBank.wrong_times += 1;
    }
    return record;
  }

  function nextQuestion() {
    if (sessionIndex.value < session.value.length - 1) {
      sessionIndex.value += 1;
      return true;
    }
    sessionDone.value = true;
    return false;
  }

  function backToBank() {
    session.value = [];
    sessionDone.value = false;
    sessionIndex.value = 0;
    answers.value = [];
    roundId.value = "";
    clearSelection();
  }

  /** 半路退出: 丢弃本轮作答记录(不留痕迹),回到题库。 */
  async function quitSession() {
    const rid = roundId.value;
    backToBank();
    if (rid) {
      try {
        await discardQuizRound(rid);
      } catch {
        /* 丢弃失败不阻塞退出 */
      }
      await loadBank();
    }
  }

  /** 手动加入/移出错题本(题库行按钮)。 */
  async function toggleMistake(q: QuizQuestion) {
    if (q.status === "wrong") {
      await removeFromMistakes(q.id);
      q.status = "untried";
    } else {
      await addToMistakes(q.id);
      q.status = "wrong";
    }
  }

  async function removeMistake(q: QuizQuestion) {
    await removeFromMistakes(q.id);
    mistakes.value = mistakes.value.filter((m) => m.id !== q.id);
    const inBank = bank.value.find((b) => b.id === q.id);
    if (inBank) inBank.status = "untried";
  }

  async function loadMistakes() {
    mistakesLoading.value = true;
    try {
      for (let attempt = 0; ; attempt++) {
        try {
          const res = await fetchQuizMistakes();
          mistakes.value = res.data.questions;
          return;
        } catch (err) {
          if (attempt >= 2) throw err;
          await new Promise((r) => setTimeout(r, 600 * (attempt + 1)));
        }
      }
    } catch {
      /* 与题库一致: 失败保持旧数据,不吞异常以外的提示 */
    } finally {
      mistakesLoading.value = false;
    }
  }

  return {
    bank,
    categories,
    bankTotal,
    bankLoading,
    bankError,
    filterRole,
    filterCategory,
    filterDifficulty,
    filterStatus,
    searchText,
    selectedIds,
    shuffled,
    session,
    sessionIndex,
    answers,
    sessionStartAt,
    sessionDone,
    roundId,
    mistakes,
    mistakesLoading,
    filteredBank,
    statusCounts,
    currentQuestion,
    correctCount,
    accuracy,
    loadBank,
    toggleSelect,
    selectAll,
    clearSelection,
    startSession,
    answerQuestion,
    nextQuestion,
    backToBank,
    quitSession,
    toggleMistake,
    removeMistake,
    loadMistakes,
  };
});
