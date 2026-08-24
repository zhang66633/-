import type {
  LearningPath,
  LearningPhase,
  LearningUnit,
} from "@/apis/learningApi";
import {
  fetchLearningPath,
  fetchUnitDetail,
  markUnitComplete,
} from "@/apis/learningApi";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

export type { LearningPath, LearningUnit, LearningPhase };

export type AgentRole = "modeler" | "programmer" | "writer";

export const useLearningStore = defineStore("learning", () => {
  // ── 状态 ──────────────────────────────────────────
  const currentRole = ref<AgentRole>("modeler");
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
        // pending（未学）显示为可学态而非锁定——审查 P0-3：假锁会让 61 个单元
        // 永远带锁图标、进度恒 0。真正的解锁顺序约束由路径阶段划分体现。
        status:
          u.status === "completed"
            ? ("completed" as const)
            : ("active" as const),
        difficulty: u.difficulty,
      })),
    }));
  });

  const totalUnits = computed(() => path.value?.total_units ?? 0);
  const completedUnits = computed(() => path.value?.completed_units ?? 0);
  const progressPercent = computed(() =>
    totalUnits.value > 0
      ? Math.round((completedUnits.value / totalUnits.value) * 100)
      : 0,
  );

  // ── 操作 ──────────────────────────────────────────
  async function loadPath(role?: AgentRole) {
    const r = role ?? currentRole.value;
    loading.value = true;
    error.value = "";
    try {
      const res = await fetchLearningPath(r);
      path.value = res.data.path;
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      error.value = msg || "加载学习路径失败";
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
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      error.value = msg || "加载学习单元失败";
    } finally {
      loading.value = false;
    }
  }

  /** 标记单元完成（调用后端 API） */
  async function markComplete(unitId: string) {
    try {
      const res = await markUnitComplete(unitId);
      // 更新本地状态
      if (currentUnit.value && currentUnit.value.unit_id === unitId) {
        currentUnit.value.status = "completed";
        currentUnit.value.mastery_score = res.data?.mastery ?? 1.0;
      }
      // 刷新路径
      await loadPath();
      return res.data;
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      error.value = msg || "标记完成失败";
      throw e;
    }
  }

  function switchRole(role: AgentRole) {
    currentRole.value = role;
    currentUnit.value = null;
    loadPath(role);
  }

  return {
    currentRole,
    path,
    currentUnit,
    loading,
    error,
    skillTree,
    totalUnits,
    completedUnits,
    progressPercent,
    loadPath,
    loadUnit,
    markComplete,
    switchRole,
  };
});
