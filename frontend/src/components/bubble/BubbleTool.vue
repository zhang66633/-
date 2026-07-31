<script setup lang="ts">
/**
 * 工具消息气泡 — 按 tool_name 分发到对应渲染器
 *
 * 渲染器注册表 → 异步加载 → 动态组件渲染。
 * 未注册的工具回退到 GenericRenderer。
 */
import { computed, defineAsyncComponent } from "vue";
import type { Message, ToolMessage, ToolStatus } from "@/types/response";
import { getToolRenderer } from "@/components/tool/toolRenderers";
import GenericRenderer from "@/components/tool/renderers/GenericRenderer.vue";
import BubbleAvatar from "./BubbleAvatar.vue";

const props = defineProps<{
  message: Message;
}>();

const tool = computed(() => props.message as ToolMessage);
const toolName = computed(() => tool.value.tool_name ?? "");
const toolInput = computed(() => tool.value.input);
const toolOutput = computed(() => tool.value.output);
const toolStatus = computed<ToolStatus | undefined>(() => tool.value.status);

const rendererComponent = computed(() => {
  const loader = getToolRenderer(toolName.value);
  if (!loader) return GenericRenderer;
  return defineAsyncComponent(loader);
});

const timestamp = computed(() => {
  if (!props.message.created_at) return "";
  return new Date(props.message.created_at).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });
});
</script>

<template>
  <div class="flex gap-3 w-full my-2 animate-in fade-in slide-in-from-bottom-2">
    <div class="flex flex-col items-center shrink-0">
      <BubbleAvatar :message="message" />
    </div>
    <div class="flex-1 min-w-0">
      <div class="flex flex-col items-start">
        <component :is="rendererComponent" :input="toolInput" :output="toolOutput" :status="toolStatus" />
        <span v-if="timestamp" class="font-mono text-[10px] text-muted-foreground/50 mt-0.5">{{ timestamp }}</span>
      </div>
    </div>
  </div>
</template>