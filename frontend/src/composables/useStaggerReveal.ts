/**
 * 交错揭示组合式函数 — 列表项逐一入场动画
 *
 * 使用方式：
 *   const { itemProps } = useStaggerReveal({ count: list.length, delay: 50 })
 *   在模板中：<div v-for="(item, i) in list" :key="item.id" v-bind="itemProps(i)">
 */

import { computed, onMounted, ref } from "vue"

export interface StaggerOptions {
  /** 列表项数量 */
  count: number
  /** 项间延迟 (ms) */
  delay?: number
  /** 初始 Y 偏移 (px) */
  yOffset?: number
  /** 持续时间 (ms) */
  duration?: number
}

export function useStaggerReveal(options: StaggerOptions) {
  const { count, delay = 60, yOffset = 12, duration = 400 } = options
  const mounted = ref(false)

  onMounted(() => {
    // 延迟一帧触发，确保 DOM 已挂载
    requestAnimationFrame(() => {
      mounted.value = true
    })
  })

  const itemProps = (index: number) => {
    const style = computed(() => {
      if (!mounted.value) {
        return {
          opacity: "0",
          transform: `translateY(${yOffset}px)`,
        }
      }
      return {
        opacity: "1",
        transform: "translateY(0)",
        transition: `opacity ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${index * delay}ms, transform ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${index * delay}ms`,
      }
    })

    return {
      style: style.value,
      class: mounted.value ? "reveal is-visible" : "reveal",
    }
  }

  return { itemProps, mounted }
}
