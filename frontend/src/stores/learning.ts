import { ref, computed } from "vue";
import { defineStore } from "pinia";
import type { LearningPath, LearningUnit, LearningPhase } from "@/apis/learningApi";
import { fetchLearningPath, fetchUnitDetail, generatePath } from "@/apis/learningApi";

export type { LearningPath, LearningUnit, LearningPhase };

export type AgentRole = "modeler" | "programmer" | "writer";

export const useLearningStore = defineStore("learning", () => {
  // ── 状态 ──────────────────────────────────────────
  const currentRole = ref<AgentRole>("modeler");
  const currentLevel = ref<string>("beginner");
  const path = ref<LearningPath | null>(null);
  const currentUnit = ref<LearningUnit | null>(null);
  const loading = ref(false);
  const error = ref("");

  // ── 计算属性 ──────────────────────────────────────
  const skillTree = computed(() => {
    if (!path.value) return [];
    return path.value.phases.map((phase: LearningPhase) => ({
      name: phase.name,
      expanded: true,
      units: phase.units.map((u: LearningUnit) => ({
        id: u.unit_id,
        name: u.title,
        status: u.status === "completed" ? "completed" as const
               : u.status === "in_progress" ? "active" as const
               : "locked" as const,
        difficulty: u.difficulty,
      })),
    }));
  });

  const totalUnits = computed(() => path.value?.total_units ?? 0);
  const completedUnits = computed(() => path.value?.completed_units ?? 0);
  const progressPercent = computed(() =>
    totalUnits.value > 0 ? Math.round((completedUnits.value / totalUnits.value) * 100) : 0,
  );

  // ── 操作 ──────────────────────────────────────────
  async function loadPath(role?: AgentRole) {
    const r = role ?? currentRole.value;
    loading.value = true;
    error.value = "";
    try {
      const res = await fetchLearningPath(r);
      path.value = res.data.path;
    } catch (e: any) {
      error.value = e?.message || "加载学习路径失败";
    } finally {
      loading.value = false;
    }
  }

  async function generateNewPath(role: AgentRole, level: string, goal: string) {
    loading.value = true;
    error.value = "";
    try {
      const res = await generatePath(role, level, goal);
      path.value = res.data.path;
      currentRole.value = role;
      currentLevel.value = level;
    } catch (e: any) {
      error.value = e?.message || "生成学习路径失败";
    } finally {
      loading.value = false;
    }
  }

  async function loadUnit(unitId: string) {
    loading.value = true;
    error.value = "";
    try {
      const res = await fetchUnitDetail(unitId);
      currentUnit.value = res.data.unit;
    } catch (e: any) {
      error.value = e?.message || "加载学习单元失败";
    } finally {
      loading.value = false;
    }
  }

  function switchRole(role: AgentRole) {
    currentRole.value = role;
    currentUnit.value = null;
    loadPath(role);
  }

  return {
    currentRole,
    currentLevel,
    path,
    currentUnit,
    loading,
    error,
    skillTree,
    totalUnits,
    completedUnits,
    progressPercent,
    loadPath,
    generateNewPath,
    loadUnit,
    switchRole,
  };
});
