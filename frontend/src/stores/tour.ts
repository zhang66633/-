import { TOUR_VERSION } from "@/config/tourSteps";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

/**
 * 新手导览状态：仅记录「看过的导览内容版本」。
 * 完成/跳过都写标记（不再自动弹出）；手动入口始终可重看。
 */
export const useTourStore = defineStore(
  "tour",
  () => {
    const doneVersion = ref<string | null>(null);

    const shouldAutoStart = computed(() => doneVersion.value !== TOUR_VERSION);

    function markDone() {
      doneVersion.value = TOUR_VERSION;
    }

    return { doneVersion, shouldAutoStart, markDone };
  },
  {
    persist: {
      key: "mma-tour",
      storage: localStorage,
      pick: ["doneVersion"],
    },
  },
);
