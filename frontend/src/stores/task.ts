import type { Message } from "@/types/response";
import { TaskWebSocket } from "@/utils/websocket";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

function genId() {
  return `tmsg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export const useTaskStore = defineStore("task", () => {
  // 每个 task 的进度/结果消息（system 进度 + agent 最终答案）
  const messagesByTask = ref<Record<string, Message[]>>({});
  const currentTaskId = ref<string | null>(null);
  // solution 任务的进度消息由 solution/index.vue 通过 watch 同步到 chatSession，
  // 保证切页/刷新后不丢失；taskStore 仅作 WS 连接管理 + 即时进度缓存。
  let ws: TaskWebSocket | null = null;
  const wsStatus = ref<"connecting" | "connected" | "disconnected" | "reconnecting">("disconnected");
  const isRunning = ref(false);
  const completed = ref(false);
  const currentStep = ref<string>("");

  const messages = computed<Message[]>(() => {
    if (!currentTaskId.value) return [];
    return messagesByTask.value[currentTaskId.value] ?? [];
  });

  function ensureTaskBucket(taskId: string) {
    if (!messagesByTask.value[taskId]) {
      messagesByTask.value[taskId] = [];
    }
  }

  function appendMessage(taskId: string, message: Message) {
    ensureTaskBucket(taskId);
    messagesByTask.value[taskId] = [...messagesByTask.value[taskId], message];
  }

  function setCurrentTask(taskId: string) {
    currentTaskId.value = taskId;
  }

  function now() {
    return new Date().toISOString();
  }

  function handleProgressEvent(taskId: string, data: Record<string, any>) {
    const event = data?.event;

    // 节点完成：追加一条进度 system 消息 + 更新当前步骤
    // 优先用 summary（节点实际产出）替代空泛的 desc，让用户看到"做了什么"
    if (event === "node_end") {
      const stage = data.data?.stage ?? "";
      const title = data.data?.title ?? stage;
      const desc = data.data?.desc ?? "";
      const summary: string = (data.data?.summary ?? "").trim();
      const content = summary
        ? `[${title}] ${desc}\n\n${summary}${summary.length >= 280 ? "…" : ""}`
        : `[${title}] ${desc}…`;
      appendMessage(taskId, {
        id: data.id ?? genId(),
        msg_type: "system",
        type: "info",
        content,
        created_at: now(),
      } as Message);
      currentStep.value = stage || currentStep.value;
      return;
    }

    // 任务结束：停止运行态，主动拉完整 final_response 渲染
    if (event === "task_end") {
      isRunning.value = false;
      completed.value = true;
      currentStep.value = "已完成";
      const finalPreview: string = data.data?.final_response_preview ?? "";
      if (data.data?.final_response_length) {
        // 先展示轻量预览，再异步 GET 完整内容并替换
        if (finalPreview) {
          appendMessage(taskId, {
            id: "final-" + taskId,
            msg_type: "agent",
            content: finalPreview + (data.data.final_response_length > finalPreview.length ? "\n\n_（正在加载完整论文…）_" : ""),
            streaming: false,
            created_at: now(),
          });
        }
        // 异步拉取完整内容
        fetchFullFinalResponse(taskId).catch((e) => {
          console.error("拉取完整论文失败：", e);
          appendMessage(taskId, {
            id: genId(),
            msg_type: "system",
            type: "warning",
            content: "⚠️ 完整论文拉取失败，仅显示上文预览片段。请重试或刷新页面。",
            created_at: now(),
          } as Message);
        });
      } else if (data.data?.message) {
        appendMessage(taskId, {
          id: genId(),
          msg_type: "system",
          type: "error",
          content: "任务失败：" + data.data.message,
          created_at: now(),
        } as Message);
      }
      return;
    }
  }

  async function fetchFullFinalResponse(taskId: string) {
    const { getTask } = await import("@/apis/commonApi");
    const res = await getTask(taskId);
    const task = res.data?.data ?? res.data;
    const full: string = task?.final_response ?? task?.writing_output ?? "";
    if (!full) return;
    // 替换占位消息
    const bucket = messagesByTask.value[taskId];
    if (!bucket) return;
    const idx = bucket.findIndex((m) => m.id === "final-" + taskId);
    if (idx === -1) {
      appendMessage(taskId, {
        id: "final-" + taskId,
        msg_type: "agent",
        content: full,
        streaming: false,
        created_at: now(),
      });
      return;
    }
    bucket[idx] = { ...bucket[idx], content: full };
    messagesByTask.value = { ...messagesByTask.value, [taskId]: [...bucket] };
  }

  function connectWebSocket(taskId: string) {
    // 短路：若已连到同一任务且连接正常，复用避免切页回来时断开/重连把进度搞丢
    if (
      ws &&
      currentTaskId.value === taskId &&
      wsStatus.value === "connected"
    ) {
      return;
    }
    if (ws) { ws.close(); ws = null; }
    setCurrentTask(taskId);
    ensureTaskBucket(taskId);
    isRunning.value = true;
    completed.value = false;
    currentStep.value = "";

    const baseUrl = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/api/ws`;
    const token = localStorage.getItem("mma:token") || "";
    const wsUrl = `${baseUrl}/task/${taskId}?token=${encodeURIComponent(token)}`;

    ws = new TaskWebSocket(
      wsUrl,
      (data) => handleProgressEvent(taskId, data as Record<string, any>),
      (status) => { wsStatus.value = status; },
    );
    ws.connect();
  }

  function closeWebSocket() {
    ws?.close();
    ws = null;
  }

  return {
    messages, wsStatus, isRunning, completed, currentStep, currentTaskId,
    connectWebSocket, closeWebSocket, setCurrentTask, appendMessage,
  };
});
// ⚠️ 故意不持久化 taskStore：messagesByTask 含 LLM 全文太大、且不能与 isRunning/
//    completed 同步持久化（否则刷新后会出现"显示思考中但无消息"的白屏诡异状态）。
//    路由切页不丢（pinia store 跨路由保留）；刷新页面后用户需重新触发。
