/**
 * 数字滚动动画 — 从 0 平滑滚动到目标值
 *
 * 使用方式：
 *   const { display } = useCountAnimation(target, { duration: 1500 })
 */

import { ref, watch, onUnmounted } from "vue"

export interface CountOptions {
  /** 动画持续时间 (ms) */
  duration?: number
  /** 是否启用 */
  enabled?: boolean
}

export function useCountAnimation(target: () => number, options: CountOptions = {}) {
  const { duration = 1500, enabled = true } = options
  const display = ref(0)
  let rafId: number | null = null
  let startTime: number | null = null
  let startValue = 0

  function animate(timestamp: number) {
    if (startTime === null) startTime = timestamp
    const elapsed = timestamp - startTime
    const progress = Math.min(elapsed / duration, 1)

    // easeOutExpo: 先快后慢
    const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress)
    display.value = Math.round(startValue + (target() - startValue) * eased)

    if (progress < 1) {
      rafId = requestAnimationFrame(animate)
    }
  }

  function start() {
    if (!enabled) {
      display.value = target()
      return
    }
    // 检查 prefers-reduced-motion
    if (typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      display.value = target()
      return
    }
    startValue = display.value
    startTime = null
    if (rafId !== null) cancelAnimationFrame(rafId)
    rafId = requestAnimationFrame(animate)
  }

  watch(target, () => {
    start()
  }, { immediate: true })

  onUnmounted(() => {
    if (rafId !== null) cancelAnimationFrame(rafId)
  })

  return { display, start }
}
