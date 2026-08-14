import type { LearningPath } from "@/apis/learningApi";
import { diagnose as diagnoseApi, fetchProfile } from "@/apis/learningApi";
import { defineStore } from "pinia";
import { ref } from "vue";

export const useProfileStore = defineStore("profile", () => {
  const hasProfile = ref(false);
  const loading = ref(false);
  const progress = ref<any>(null);
  const error = ref("");

  /** 检查是否需要诊断 */
  async function checkProfile() {
    loading.value = true;
    error.value = "";
    try {
      const res = await fetchProfile();
      const p = res.data.profile;
      // 如果没有任何角色配置，认为需要诊断
      hasProfile.value = p.roles && p.roles.length > 0;
    } catch {
      hasProfile.value = false;
    } finally {
      loading.value = false;
    }
  }

  /** 执行诊断 */
  async function runDiagnose(payload: {
    role: string;
    self_assessment: Record<string, number>;
    goal: string;
    weekly_hours: number;
  }) {
    loading.value = true;
    error.value = "";
    try {
      await diagnoseApi(payload.role, payload.self_assessment, payload.goal);
      hasProfile.value = true;
    } catch (e: any) {
      error.value = e?.message || "诊断失败";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  /** 获取学习进度 */
  async function loadProgress() {
    loading.value = true;
    try {
      const { default: request } = await import("@/utils/request");
      const progressRes = await request.get("/profile/progress");
      progress.value = progressRes.data;
    } catch {
      progress.value = null;
    } finally {
      loading.value = false;
    }
  }

  /** 成就已读(庆祝弹窗关闭后调用) */
  async function ackAchievements() {
    try {
      const { default: request } = await import("@/utils/request");
      await request.post("/profile/achievements/ack");
      if (progress.value?.achievements) {
        for (const a of progress.value.achievements) a.is_new = false;
      }
    } catch {
      /* 忽略 */
    }
  }

  return {
    hasProfile,
    loading,
    progress,
    error,
    checkProfile,
    runDiagnose,
    loadProgress,
    ackAchievements,
  };
});
