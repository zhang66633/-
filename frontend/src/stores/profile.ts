import { fetchProfile } from "@/apis/learningApi";
import { defineStore } from "pinia";
import { ref } from "vue";

/** 学习画像/进度结构（未知字段透传） */
interface LearningProfile {
  roles?: string[];
  achievements?: { is_new?: boolean }[];
  [key: string]: unknown;
}

export const useProfileStore = defineStore("profile", () => {
  const hasProfile = ref(false);
  const loading = ref(false);
  const progress = ref<LearningProfile | null>(null);
  const error = ref("");

  /** 检查学习画像(首页「继续学习」卡等依赖) */
  async function checkProfile() {
    loading.value = true;
    error.value = "";
    try {
      const res = await fetchProfile();
      const p = res.data.profile;
      // 有角色配置即认为存在学习画像
      hasProfile.value = p.roles && p.roles.length > 0;
    } catch {
      hasProfile.value = false;
    } finally {
      loading.value = false;
    }
  }

  /** 获取学习进度。返回是否成功,让页面区分「加载失败」与「尚未开始学习」 */
  async function loadProgress(): Promise<boolean> {
    loading.value = true;
    try {
      const { default: request } = await import("@/utils/request");
      const progressRes = await request.get("/profile/progress");
      progress.value = progressRes.data;
      return true;
    } catch {
      progress.value = null;
      return false;
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
    loadProgress,
    ackAchievements,
  };
});
