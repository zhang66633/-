import { type Ref, onUnmounted, ref, watch } from "vue";

/**
 * 打字机效果 composable — 逐字显示文本
 * @param text 源文本
 * @param speed 每个字符的延迟（ms），默认 15ms
 * @param enabled 是否启用打字效果，默认 true
 */
export function useTypewriter(
  text: Ref<string>,
  speed = 15,
  enabled: Ref<boolean> = ref(true),
) {
  const displayText = ref("");
  const isTyping = ref(false);
  let timer: ReturnType<typeof setTimeout> | null = null;
  let index = 0;

  function startTyping() {
    if (!enabled.value || !text.value) {
      displayText.value = text.value;
      isTyping.value = false;
      return;
    }

    stopTyping();
    isTyping.value = true;
    index = 0;
    displayText.value = "";

    function type() {
      if (index < text.value.length) {
        displayText.value += text.value[index];
        index++;
        timer = setTimeout(type, speed);
      } else {
        isTyping.value = false;
      }
    }

    type();
  }

  function stopTyping() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function skip() {
    stopTyping();
    displayText.value = text.value;
    isTyping.value = false;
  }

  // 监听文本变化
  watch(text, startTyping, { immediate: true });

  // 清理
  onUnmounted(stopTyping);

  return {
    displayText,
    isTyping,
    skip,
  };
}
