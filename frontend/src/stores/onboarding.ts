import { defineStore } from "pinia";
import { computed, ref } from "vue";

export type AgentRole = "modeler" | "programmer" | "writer";

export interface SelfAssessment {
  math_level: number;
  programming_level: number;
  writing_level: number;
  modeling_experience: number;
}

export interface DiagnosePayload {
  role: AgentRole;
  self_assessment: SelfAssessment;
  goal: string;
  weekly_hours: number;
  level: string;
}

export const useOnboardingStore = defineStore("onboarding", () => {
  const visible = ref(false);
  const step = ref(0); // 0=角色, 1=自评, 2=目标, 3=诊断结果
  const role = ref<AgentRole>("modeler");
  const assessment = ref<SelfAssessment>({
    math_level: 3,
    programming_level: 3,
    writing_level: 3,
    modeling_experience: 3,
  });
  const goal = ref("国赛");
  const weeklyHours = ref(10);
  const targetDate = ref("");
  const diagnosed = ref(false);

  const computedLevel = computed(() => {
    const a = assessment.value;
    if (role.value === "modeler") {
      const avg = (a.math_level + a.modeling_experience) / 2;
      return avg <= 2 ? "beginner" : avg <= 3.5 ? "intermediate" : "advanced";
    }
    if (role.value === "programmer") {
      return a.programming_level <= 2
        ? "beginner"
        : a.programming_level <= 3.5
          ? "intermediate"
          : "advanced";
    }
    return a.writing_level <= 2
      ? "beginner"
      : a.writing_level <= 3.5
        ? "intermediate"
        : "advanced";
  });

  const levelLabel = computed(
    () =>
      (({ beginner: "入门", intermediate: "进阶", advanced: "高手" }) as any)[
        computedLevel.value
      ] ?? "入门",
  );

  const levelSuggestion = computed(() => {
    if (computedLevel.value === "beginner")
      return {
        title: "建议从入门课程开始",
        tips: [
          "先夯实基础方法 (优化→评价→预测)",
          "每个知识点配合练习巩固",
          "推荐每周学习 3-5 个单元",
        ],
        focus: "入门课程",
      };
    if (computedLevel.value === "intermediate")
      return {
        title: "建议主推进阶课程",
        tips: [
          "快速浏览入门内容查漏补缺",
          "重点关注方法对比和组合应用",
          "多动手做综合练习",
        ],
        focus: "进阶课程",
      };
    return {
      title: "可以挑战实战项目",
      tips: [
        "跳过纯基础单元",
        "直接进入方法组合和竞赛实战",
        "建议以赛代练，找真题模拟",
      ],
      focus: "实战课程",
    };
  });

  function start() {
    visible.value = true;
    step.value = 0;
  }
  function next() {
    if (step.value < 3) step.value++;
  }
  function prev() {
    if (step.value > 0) step.value--;
  }

  /** 收集当前诊断数据(不关闭向导),供分析阶段 emit 给页面执行 API */
  function buildPayload(): DiagnosePayload {
    return {
      role: role.value,
      self_assessment: { ...assessment.value },
      goal: goal.value,
      weekly_hours: weeklyHours.value,
      level: computedLevel.value,
    };
  }

  function finish(): DiagnosePayload {
    visible.value = false;
    diagnosed.value = true;
    return buildPayload();
  }

  return {
    visible,
    step,
    role,
    assessment,
    goal,
    weeklyHours,
    targetDate,
    diagnosed,
    computedLevel,
    levelLabel,
    levelSuggestion,
    start,
    next,
    prev,
    buildPayload,
    finish,
  };
});
