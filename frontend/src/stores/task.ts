import { useAuthStore } from "@/stores/auth";
import type { Message } from "@/types/response";
import { TaskWebSocket } from "@/utils/websocket";
import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";

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
  const wsStatus = ref<
    "connecting" | "connected" | "disconnected" | "reconnecting"
  >("disconnected");
  const isRunning = ref(false);
  const completed = ref(false);
  const currentStep = ref<string>("");
  // 写作阶段并行生成状态（node_progress 事件驱动：outline → section×N → abstract → red_team → revise）
  const writingStage = ref<string | null>(null);
  const sectionsDone = ref(0);
  // 动态执行计划（plan 事件；波次 2 用真实计划渲染时间线，替换写死步骤）
  const planSteps = ref<string[]>([]);

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

  /** 更新 task 内已存在的消息（同 id 覆盖，供工具结果/代码执行回填） */
  function updateMessage(
    taskId: string,
    messageId: string,
    patch: Partial<Message>,
  ) {
    const bucket = messagesByTask.value[taskId];
    if (!bucket) return;
    const idx = bucket.findIndex((m) => m.id === messageId);
    if (idx === -1) return;
    const updated = { ...bucket[idx], ...patch };
    bucket[idx] = updated;
    messagesByTask.value = { ...messagesByTask.value, [taskId]: [...bucket] };
  }

  /** 找最近的 tool 消息：优先 tool_call_id 精确匹配，退化最近同名未完成 */
  function findToolMessage(
    taskId: string,
    toolCallId?: string,
    toolName?: string,
  ) {
    const bucket = messagesByTask.value[taskId];
    if (!bucket) return null;
    if (toolCallId) {
      const hit = [...bucket]
        .reverse()
        .find(
          (m) =>
            m.msg_type === "tool" && (m as any).tool_call_id === toolCallId,
        );
      if (hit) return hit;
    }
    if (toolName) {
      return (
        [...bucket]
          .reverse()
          .find(
            (m) =>
              m.msg_type === "tool" &&
              (m as any).tool_name === toolName &&
              ((m as any).status === "running" || !(m as any).output),
          ) ?? null
      );
    }
    return null;
  }

  function setCurrentTask(taskId: string) {
    currentTaskId.value = taskId;
  }

  function now() {
    return new Date().toISOString();
  }

  function handleProgressEvent(taskId: string, data: Record<string, any>) {
    const event = data?.event;

    // 动态执行计划（协议 v2.1：前端按真实计划渲染时间线）
    if (event === "plan") {
      const plan: string[] = Array.isArray(data.data?.plan)
        ? data.data.plan
        : [];
      if (plan.length) planSteps.value = plan;
      return;
    }

    // 写作阶段细粒度进度（并行生成章节提示）
    if (event === "node_progress") {
      const stage: string | undefined = data.data?.stage;
      if (stage) writingStage.value = stage;
      if (stage === "outline") sectionsDone.value = 0;
      if (stage === "section") sectionsDone.value += 1;
      return;
    }

    // 工具调用：先发 running（协议 v2.1：两段式，同一卡片执行态 → 结果回填）
    if (event === "tool_call") {
      appendMessage(taskId, {
        id: data.id ?? genId(),
        msg_type: "tool",
        tool_name: data.data?.tool_name ?? "run_code",
        input: data.data?.input ?? null,
        output: null,
        status: "running",
        tool_call_id: data.data?.tool_call_id,
        created_at: now(),
      } as Message);
      return;
    }

    // 工具结果（协议 v2.1：按 id 回填同一卡片，修复"调用在后、输出在前"的割裂）
    if (event === "tool_result") {
      const d = data.data ?? {};
      const target = findToolMessage(taskId, d.tool_call_id, d.tool_name);
      if (!target) return;
      updateMessage(taskId, target.id, {
        output: [
          {
            name: d.tool_name,
            preview: d.preview ?? "",
            images: d.images ?? [],
            xlsx_files: d.xlsx_files ?? [],
            csv_files: d.csv_files ?? [],
            html_files: d.html_files ?? [],
          },
        ],
        status: d.ok === false ? "error" : "success",
        error: d.ok === false ? d.error : undefined,
        duration_ms: d.duration_ms,
      } as Partial<Message>);
      return;
    }

    // 代码执行态（run_code 的 running/done 帧，与 chat 通道协议一致）
    if (event === "code_exec") {
      const d = data.data ?? {};
      const target = findToolMessage(taskId, d.id, "run_code");
      if (!target) return;
      if (d.status === "running") {
        updateMessage(taskId, target.id, {
          output: [{ name: "run_code", preview: "代码执行中…" }],
          status: "running",
        } as Partial<Message>);
      } else if (d.status === "done") {
        const parts = [];
        if (d.stdout) parts.push(`输出:\n${d.stdout}`);
        if (d.images?.length) parts.push(`图表: ${d.images.length} 张`);
        updateMessage(taskId, target.id, {
          output: [
            {
              name: "run_code",
              preview: parts.join("\n") || "执行完成",
              images: d.images ?? [],
            },
          ],
          status: d.ok === false ? "error" : "success",
          error: d.ok === false ? d.error : undefined,
          duration_ms: d.duration_ms,
        } as Partial<Message>);
      }
      return;
    }

    // 节点完成：追加一条 agent 消息，思考内容放入 thinking 字段
    // 这样 BubbleAgent + ThinkingBlock 可以渲染可折叠的思考过程
    if (event === "node_end") {
      const stage = data.data?.stage ?? "";
      const title = data.data?.title ?? stage;
      const summary: string = (data.data?.summary ?? "").trim();
      const outputLength = data.data?.output_length ?? 0;
      const passed = data.data?.passed;
      const imagesCount = data.data?.images_count ?? 0;

      // 构建给用户看的摘要
      let content = "";
      if (passed !== undefined) {
        content = passed ? "✅ 验证通过" : "❌ 验证不通过";
      } else if (imagesCount > 0) {
        content = `求解完成，输出 ${outputLength} 字，图表 ${imagesCount} 张`;
      } else if (outputLength > 0) {
        content = `输出 ${outputLength} 字`;
      }

      appendMessage(taskId, {
        id: data.id ?? genId(),
        msg_type: "agent",
        content,
        agent_type: undefined,
        thinking: summary || `[${title}] 分析完成`,
        streaming: false,
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
            id: `final-${taskId}`,
            msg_type: "agent",
            content:
              finalPreview +
              (data.data.final_response_length > finalPreview.length
                ? "\n\n_（正在加载完整论文…）_"
                : ""),
            streaming: false,
            created_at: now(),
          });
        }
        // 异步拉取完整内容
        fetchFullFinalResponse(taskId).catch((e) => {
          console.error("拉取完整论文失败：", e);
          // 清除占位消息中的"正在加载"提示，避免残留
          const bucket = messagesByTask.value[taskId];
          if (bucket) {
            const idx = bucket.findIndex((m) => m.id === `final-${taskId}`);
            if (idx !== -1) {
              const cleaned = (bucket[idx].content as string).replace(
                /\n\n_（正在加载完整论文…）_$/,
                "\n\n_（完整论文加载失败，以上为预览片段）_",
              );
              bucket[idx] = { ...bucket[idx], content: cleaned };
              messagesByTask.value = {
                ...messagesByTask.value,
                [taskId]: [...bucket],
              };
            }
          }
        });
      } else if (data.data?.message) {
        appendMessage(taskId, {
          id: genId(),
          msg_type: "system",
          type: "error",
          content: `任务失败：${data.data.message}`,
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
    const idx = bucket.findIndex((m) => m.id === `final-${taskId}`);
    if (idx === -1) {
      appendMessage(taskId, {
        id: `final-${taskId}`,
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
    if (ws) {
      ws.close();
      ws = null;
    }
    setCurrentTask(taskId);
    ensureTaskBucket(taskId);
    isRunning.value = true;
    completed.value = false;
    currentStep.value = "";

    // 未登录（无 token）：不发起无认证连接，避免 401 握手失败 + 重连刷屏。
    // 登录后由下方 watch(auth.token) 自动恢复连接。
    const token = localStorage.getItem("mma:token") || "";
    if (!token) {
      wsStatus.value = "disconnected";
      return;
    }

    const baseUrl =
      import.meta.env.VITE_WS_URL || `ws://${window.location.host}/api/ws`;
    const wsUrl = `${baseUrl}/task/${taskId}?token=${encodeURIComponent(token)}`;

    ws = new TaskWebSocket(
      wsUrl,
      (data) => handleProgressEvent(taskId, data as Record<string, any>),
      (status) => {
        wsStatus.value = status;
      },
    );
    ws.connect();
  }

  // 登录后自动恢复当前任务的 WS 连接（无 token 时被跳过的场景）
  const auth = useAuthStore();
  watch(
    () => auth.token,
    (tok) => {
      if (tok && currentTaskId.value && wsStatus.value !== "connected") {
        connectWebSocket(currentTaskId.value);
      }
    },
  );

  function closeWebSocket() {
    ws?.close();
    ws = null;
  }

  return {
    messages,
    wsStatus,
    isRunning,
    completed,
    currentStep,
    writingStage,
    sectionsDone,
    planSteps,
    currentTaskId,
    connectWebSocket,
    closeWebSocket,
    setCurrentTask,
    appendMessage,
    updateMessage,
  };
});
// ⚠️ 故意不持久化 taskStore：messagesByTask 含 LLM 全文太大、且不能与 isRunning/
//    completed 同步持久化（否则刷新后会出现"显示思考中但无消息"的白屏诡异状态）。
//    路由切页不丢（pinia store 跨路由保留）；刷新页面后用户需重新触发。
