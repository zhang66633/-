import { ref } from "vue";
import { defineStore } from "pinia";

export type AgentRole = "modeler" | "programmer" | "writer";

export interface SelfAssessment {
  math_level: number;
  programming_level: number;
  writing_level: number;
  modeling_experience: number;
}

export interface DiagnosePayload {
  role: string;
  self_assessment: SelfAssessment;
  goal: string;
  weekly_hours: number;
}

export const useOnboardingStore = defineStore("onboarding", () => {
  const visible = ref(false);
  const step = ref(0); // 0=角色, 1=自评, 2=目标
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

  function start() {
    visible.value = true;
    step.value = 0;
  }

  function next() {
    if (step.value < 2) step.value++;
  }

  function prev() {
    if (step.value > 0) step.value--;
  }

  function finish(): DiagnosePayload {
    visible.value = false;
    return {
      role: role.value,
      self_assessment: { ...assessment.value },
      goal: goal.value,
      weekly_hours: weeklyHours.value,
    };
  }

  return {
    visible, step, role, assessment, goal, weeklyHours, targetDate,
    start, next, prev, finish,
  };
});