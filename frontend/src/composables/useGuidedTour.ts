import { tourSteps } from "@/config/tourSteps";
import { useTourStore } from "@/stores/tour";
import { type Driver, driver } from "driver.js";
import "driver.js/dist/driver.css";
import { useRouter } from "vue-router";

/**
 * 新手导览编排：基于 driver.js 手动单步驱动。
 *
 * 为什么不用 drive(steps) 全自动模式：导览跨越 8 个路由，
 * 需要在每步之间 router.push 切页、等待目标渲染后再高亮——
 * highlight() 单步 + 自管索引是最可控的编排方式。
 */
let instance: Driver | null = null;

/** 轮询等待选择器出现（切页后 Vue 渲染时序兜底），超时返回 null */
function waitForSelector(
  selector: string,
  timeout = 3000,
): Promise<Element | null> {
  return new Promise((resolve) => {
    const start = performance.now();
    const tick = () => {
      const el = document.querySelector(selector);
      if (el) {
        resolve(el);
        return;
      }
      if (performance.now() - start > timeout) {
        resolve(null);
        return;
      }
      requestAnimationFrame(() => setTimeout(tick, 50));
    };
    tick();
  });
}

export function useGuidedTour() {
  const router = useRouter();
  const tourStore = useTourStore();

  /** 导览是否正在进行 */
  function isActive(): boolean {
    return instance?.isActive() ?? false;
  }

  async function goTo(index: number) {
    if (!instance) return;

    // 走出两端：收尾销毁（onDestroyed 内统一 markDone）
    if (index < 0 || index >= tourSteps.length) {
      instance.destroy();
      return;
    }

    const step = tourSteps[index];
    if (!step) {
      instance.destroy();
      return;
    }

    // 跨页步骤：先切路由，再等锚点出现
    if (step.route && router.currentRoute.value.path !== step.route) {
      await router.push(step.route).catch(() => {});
      await new Promise((r) => requestAnimationFrame(() => r(null)));
    }

    let element: Element | undefined;
    if (step.selector) {
      element =
        (await waitForSelector(`[data-tour="${step.selector}"]`)) ?? undefined;
      if (!element) {
        // 锚点缺失（如面板被关闭等边缘态）：静默跳过该步
        await goTo(index + 1);
        return;
      }
    }

    const total = tourSteps.length;
    instance.highlight({
      element,
      popover: {
        title: `${step.title} · ${index + 1}/${total}`,
        description: step.description,
        // highlight() 内部会把 showButtons 预置为 []（空数组为 truthy，
        // 吞掉全局配置导致按钮全部不渲染），必须逐步显式传入
        showButtons: ["next", "previous", "close"],
        onNextClick: () => void goTo(index + 1),
        onPrevClick: () => void goTo(index - 1),
      },
    });
  }

  /** 启动导览（手动入口 / 首次自动触发共用）；进行中重复调用会被忽略 */
  function start() {
    if (isActive()) return;

    instance = driver({
      nextBtnText: "下一步",
      prevBtnText: "上一步",
      doneBtnText: "完成",
      allowClose: true,
      smoothScroll: true,
      // 完成、中途跳过都算「已读」：不再自动弹出；手动入口仍可随时重看
      onDestroyed: () => {
        instance = null;
        tourStore.markDone();
      },
    });

    void goTo(0);
  }

  return { start, isActive };
}
