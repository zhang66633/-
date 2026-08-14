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
