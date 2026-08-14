import request from "@/utils/request";

// ── 类型定义 ──────────────────────────────────────────

export interface LearningUnit {
  unit_id: string;
  title: string;
  role: "modeler" | "programmer" | "writer";
  type: "knowledge" | "practice" | "project";
  difficulty: "beginner" | "intermediate" | "advanced" | "competition";
  method_category: string;
  tags: string[];
  primary_agent: string;
  estimated_minutes: number;
  content_md: string;
  status: "pending" | "in_progress" | "completed" | "skipped";
  mastery_score: number;
  prerequisites: { unit_id: string; required_mastery: number }[];
}

export interface LearningPhase {
  name: string;
  description: string;
  duration_weeks: number;
  units: LearningUnit[];
}

export interface LearningPath {
  path_id: string;
  user_id: string;
  role: string;
  generated_at: string;
  phases: LearningPhase[];
  total_units: number;
  completed_units: number;
  overall_mastery: number;
}

// ── API 调用 ──────────────────────────────────────────

/** 获取指定角色的默认学习路径 */
export function fetchLearningPath(role: string) {
  return request.get<{ path: LearningPath }>(`/learning/path/${role}`);
}

/** 生成个性化学习路径 */
export function generatePath(role: string, level: string, goal: string) {
  return request.post<{ path: LearningPath }>("/learning/path/generate", {
    role,
    level,
    goal,
  });
}

/** 获取学习单元详情 */
export function fetchUnitDetail(unitId: string) {
  return request.get<{ unit: LearningUnit }>(`/learning/units/${unitId}`);
}

/** 标记学习单元为完成 */
export function markUnitComplete(unitId: string) {
  return request.post(`/learning/units/${unitId}/complete`, {
    user_id: "default",
  });
}

/** 获取下一步推荐 */
export function fetchNextRecommendation(role: string) {
  return request.get(`/learning/next/${role}`);
}

/** 获取用户画像 */
export function fetchProfile() {
  return request.get("/profile");
}

/** 初始诊断 */
export function diagnose(
  role: string,
  selfAssessment: Record<string, number>,
  goal: string,
) {
  return request.post("/profile/diagnose", {
    role,
    self_assessment: selfAssessment,
    goal,
  });
}

/** 获取学习进度 */
export function fetchProgress() {
  return request.get("/profile/progress");
}

// ── 题库与练习(选择题)───────────────────────────────

export type QuizStatus = "untried" | "wrong" | "mastered";

export interface QuizQuestion {
  id: string;
  unit_id: string;
  role: "modeler" | "programmer" | "writer";
  category: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  question: string;
  options: string[];
  tags: string[];
  status: QuizStatus;
  wrong_times: number;
}

export interface QuizBankResponse {
  total: number;
  categories: { name: string; count: number }[];
  questions: QuizQuestion[];
}

/** 题库浏览(可筛选,不含答案) */
export function fetchQuizBank(params?: {
  category?: string;
  difficulty?: string;
  role?: string;
  unit_id?: string;
}) {
  return request.get<QuizBankResponse>("/learning/quiz/bank", { params });
}

/** 按勾选题目创建一轮练习 */
export function startQuizPractice(question_ids: string[]) {
  return request.post<{ questions: QuizQuestion[] }>(
    "/learning/quiz/practice",
    {
      question_ids,
    },
  );
}

export interface QuizAnswerResult {
  question_id: string;
  correct: boolean;
  answer_index: number;
  explanation: string;
}

/** 判分一道选择题(答错自动入错题本) */
export function submitQuizAnswer(question_id: string, choice: number) {
  return request.post<QuizAnswerResult>("/learning/quiz/answer", {
    question_id,
    choice,
  });
}

/** 错题本列表 */
export function fetchQuizMistakes() {
  return request.get<{ total: number; questions: QuizQuestion[] }>(
    "/learning/quiz/mistakes",
  );
}

/** 某学习单元的自测题(单元页「单元自测」块) */
export function fetchUnitQuiz(unitId: string) {
  return request.get<{ questions: QuizQuestion[] }>(
    `/learning/quiz/by-unit/${unitId}`,
  );
}
