<template>
  <div class="flex h-full bg-background">
    <div class="flex-1 min-w-0 relative">
      <button
        class="absolute top-2 right-2 z-10 inline-flex h-8 w-8 items-center justify-center rounded-md border border-border bg-background/80 backdrop-blur hover:bg-accent transition-colors"
        title="切换执行进度面板"
        @click="rightPanelOpen = !rightPanelOpen"
      >
        <PanelRight class="h-4 w-4" />
      </button>
      <ChatArea
        :messages="displayMessages"
        :is-running="chatSession.getIsRunning('solution')"
        :cancellable="!!currentTaskId"
        :cancelling="cancelling"
        empty-text="开始建模"
        empty-subtext="描述你的问题，我将输出完整建模方案和论文"
        input-placeholder="描述你想解决的建模问题..."
        @send="handleUserSend"
        @cancel="handleCancel"
      />
    </div>
    <Transition name="slide-right">
      <div v-if="rightPanelOpen" class="w-80 shrink-0 border-l bg-background p-4 overflow-y-auto">
        <ProgressTimeline
          :steps="agentSteps"
          :running="taskStore.isRunning"
          :completed="taskStore.completed"
          :ws-status="taskStore.wsStatus"
          :open="true"
          @toggle="rightPanelOpen = !rightPanelOpen"
        />
        <div v-if="currentTaskId" class="mt-3 font-mono text-[10px] text-muted-foreground break-all">
          Task ID: {{ currentTaskId }}
        </div>

        <!-- 下载按钮：任务完成后显示 -->
        <div v-if="taskStore.completed && currentTaskId" class="mt-4 space-y-2">
          <p class="text-xs font-medium text-foreground mb-2">📥 下载文档</p>
          <button
            class="flex items-center gap-2 w-full rounded-md border px-3 py-2 text-sm hover:bg-accent transition-colors"
            @click="downloadExport('md')"
          >
            <FileText class="h-4 w-4" /> Markdown (.md)
          </button>
          <button
            class="flex items-center gap-2 w-full rounded-md border px-3 py-2 text-sm hover:bg-accent transition-colors"
            @click="downloadExport('docx')"
          >
            <FileDown class="h-4 w-4" /> Word (.docx)
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { PanelRight, FileText, FileDown } from "lucide-vue-next";
import ChatArea from "@/components/ChatArea.vue";
import ProgressTimeline, { type ProgressStep } from "@/components/ProgressTimeline.vue";
import { useChatSessionStore } from "@/stores/chatSession";
import { useTaskStore } from "@/stores/task";
import { createTask, cancelTask } from "@/apis/commonApi";
import type { Message } from "@/types/response";

const chatSession = useChatSessionStore();
const taskStore = useTaskStore();

const rightPanelOpen = ref(true);

// solution 页关联的 task_id：原本想放 taskStore（持久化），但 messagesByTask
// 不持久化会导致"刷新后显示 Task ID 但 messages 为空"白屏。
// 改为：task_id 仅在本次 session 内存中持有，刷新后用户重新触发即可；
// 任务进度消息本身已通过 chatSession.solutionSessions 持久化（向下兼容）。
const currentTaskId = ref<string | null>(null);
const cancelling = ref(false);

const stepDefs: ProgressStep[] = [
  { id: "1", label: "问题分析", description: "识别问题类型，理解题意", status: "wait" },
  { id: "2", label: "模型构建", description: "选择并建立数学模型", status: "wait" },
  { id: "3", label: "求解计算", description: "生成并执行求解代码", status: "wait" },
  { id: "4", label: "验证分析", description: "检验模型鲁棒性", status: "wait" },
  { id: "5", label: "论文写作", description: "生成结构化论文", status: "wait" },
];

const agentSteps = computed<ProgressStep[]>(() => {
  const current = taskStore.currentStep;
  if (taskStore.completed) {
    return stepDefs.map((s) => ({ ...s, status: "done" }));
  }
  if (!current) {
    return stepDefs;
  }
  const order = stepDefs.map((s) => s.label);
  let activeIdx = order.indexOf(current);
  if (current === "已完成") {
    return stepDefs.map((s) => ({ ...s, status: "done" }));
  }
  if (activeIdx === -1) {
    if (current.includes("分析") || current.includes("检索") || current.includes("计划")) activeIdx = 0;
    else if (current.includes("模型")) activeIdx = 1;
    else if (current.includes("求解") || current.includes("计算")) activeIdx = 2;
    else if (current.includes("验证")) activeIdx = 3;
    else if (current.includes("写作") || current.includes("整合") || current.includes("输出")) activeIdx = 4;
  }
  return stepDefs.map((s, i) => ({
    ...s,
    status:
      activeIdx === -1
        ? "wait"
        : i < activeIdx
          ? "done"
          : i === activeIdx
            ? "active"
            : "wait",
  }));
});

const displayMessages = computed<Message[]>(() => {
  const userMsgs = chatSession.activeSolutionMessages;
  const taskMsgs = currentTaskId.value ? taskStore.messages : [];
  // 去重：taskStore 的消息会被 watcher 同步进 chatSession，直接拼接会重复显示。
  // 同 id 消息优先取 taskStore 版本（实时源），确保完整论文替换预览后立即生效。
  const taskMap = new Map(taskMsgs.map((m) => [m.id, m]));
  const seen = new Set<string>();
  const result: Message[] = [];
  for (const m of [...userMsgs, ...taskMsgs]) {
    if (seen.has(m.id)) continue;
    seen.add(m.id);
    result.push(taskMap.get(m.id) ?? m);
  }
  return result;
});

/** 把 taskStore 推送的进度/final 消息同步到 chatSession（持久化）。 */
function syncTaskMsgToSession(msg: Message) {
  const sid = chatSession.activeSolutionId;
  if (!sid) return;
  const list = chatSession.activeSolutionMessages;
  const existing = list.find((m) => m.id === msg.id);
  if (existing) {
    // 已存在则更新内容（关键：fetchFullFinalResponse 会用完整论文替换
    // 800字预览占位消息，若此处跳过，chatSession 将永远停留在旧预览，
    // 导致完整论文不显示、导出 PDF 只有截断的预览）
    if (existing.content !== msg.content) {
      chatSession.updateMessage("solution", sid, msg.id, { content: msg.content });
    }
    return;
  }
  chatSession.addMessage("solution", sid, msg);
}

watch(
  () => taskStore.messages,
  (newMsgs) => {
    // 把新推进来的消息同步到 chatSession（仅同步增量）
    for (const m of newMsgs) syncTaskMsgToSession(m);
  },
  { deep: true },
);

function generateId() {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

async function handleUserSend(text: string) {
  let sessionId = chatSession.activeSolutionId;
  if (!sessionId) {
    sessionId = chatSession.createSession("solution");
  }

  const userMsg: Message = {
    id: generateId(),
    msg_type: "user",
    content: text,
    created_at: new Date().toISOString(),
  };
  chatSession.addMessage("solution", sessionId, userMsg);

  // 如果已有任务在跑，先拒绝发送
  if (chatSession.runningMode !== null) {
    chatSession.addMessage("solution", sessionId, {
      id: generateId(),
      msg_type: "system",
      type: "error",
      content: "⚠️ 当前已有任务在执行，请先等待或停止。",
      created_at: new Date().toISOString(),
    } as Message);
    return;
  }

  chatSession.setRunning("solution");

  try {
    const res = await createTask({ problem: text, mode: "execute" });
    const taskId = res.data?.task_id ?? res.data?.data?.task_id;
    if (!taskId) throw new Error("未返回 task_id");
    currentTaskId.value = taskId;
    // 连接 WS 实时接收进度与最终答案；task_end 事件会清空 runningMode
    taskStore.connectWebSocket(taskId);
  } catch (e: any) {
    chatSession.addMessage("solution", sessionId, {
      id: generateId(),
      msg_type: "system",
      type: "error",
      content: `⚠️ 创建任务失败：${e?.message ?? "后端不可达，请确认已启动 (uvicorn app.main:app --port 8002)"}`,
      created_at: new Date().toISOString(),
    } as Message);
    chatSession.setRunning(null);
    currentTaskId.value = null;
  }
}

async function handleCancel() {
  if (!currentTaskId.value || cancelling.value) return;
  cancelling.value = true;
  try {
    await cancelTask(currentTaskId.value);
    // 后端会主动推 task_end/canceled 事件，前端通过 WS 收尾
  } catch (e: any) {
    console.error("取消任务失败：", e);
  } finally {
    // 兜底：若 WS 没收到 cancel 事件，2s 后强制清状态
    setTimeout(() => {
      cancelling.value = false;
      if (chatSession.runningMode === "solution") {
        chatSession.setRunning(null);
      }
    }, 2000);
  }
}

/** 带鉴权的文件导出下载 */
async function downloadExport(format: "md" | "docx") {
  if (!currentTaskId.value) return;
  try {
    const { default: request } = await import("@/utils/request");
    const resp = await request.get(`/tasks/${currentTaskId.value}/export`, {
      params: { format },
      responseType: "blob",
    });
    const blob = new Blob([resp.data]);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const ext = format === "latex" ? "tex" : format;
    a.download = `paper.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e: any) {
    console.error("导出失败：", e);
  }
}

// task_end 后 taskStore.isRunning=false，同步 solution 的 runningMode
watch(
  () => taskStore.isRunning,
  (running) => {
    if (!running && chatSession.runningMode === "solution") {
      chatSession.setRunning(null);
    }
  },
);

onMounted(() => {
  if (!chatSession.activeSolutionId && chatSession.sortedSolutionSessions.length > 0) {
    chatSession.switchSession("solution", chatSession.sortedSolutionSessions[0].id);
  }
  // 当前页面内的 task_id 不持久化（与 taskStore.messagesByTask 一致），刷新后
  // 用户需重新触发任务；路由切页通过 chatSession 持久化保留历史消息。
});

// 注意：故意不在 onUnmounted 关闭 WS，避免切页导致任务进度丢失。
// WS 由 taskStore 持有，task_end 后会保持连接直到用户切换任务/显式关闭。
onBeforeUnmount(() => {});
</script>

<style scoped>
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.25s ease;
}
.slide-right-enter-from,
.slide-right-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>