import {
  type ChatFileRef,
  type ChatHistoryMessage,
  streamChat,
} from "@/apis/chatApi";
import { type SessionMode, useChatSessionStore } from "@/stores/chatSession";
import type { Message } from "@/types/response";
/** 流式对话组合式函数 — 对话/学习/答疑/练习页共用。
 *
 * 负责：会话创建/复用、用户消息与 agent 占位消息写入、
 * 调 SSE 接口并流式就地累加、工具调用可视化、运行态管理、最新会话恢复、
 * 按会话记录 AbortController，卸载/失活时中止进行中的流。
 */
import { onDeactivated, onUnmounted } from "vue";

function generateId() {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

/** 从工具输出文本中提取图表 URL（png/jpg/gif/webp；tool_result 无 images 字段时兜底）。 */
function extractImageUrls(text: string): string[] {
  return (
    text.match(/\/api\/images\/[^\s,，)）'"]+\.(?:png|jpg|jpeg|gif|webp)/g) ??
    []
  );
}

export function useStreamChat(
  sessionMode: SessionMode,
  chatMode: "chat" | "learning" | "practice",
) {
  const chatSession = useChatSessionStore();
  // 每次发送独立 AbortController，按 (mode, sessionId) 键控，避免并发会话互串
  const abortControllers = new Map<string, AbortController>();

  function controllerKey(sessionId: string): string {
    return `${sessionMode}:${sessionId}`;
  }

  /** 中止本模式所有进行中的流式请求。 */
  function abortAllStreams() {
    for (const controller of abortControllers.values()) controller.abort();
    abortControllers.clear();
    chatSession.setRunning(null);
  }

  /** 取消当前正在进行的流式请求。 */
  function cancelStream() {
    abortAllStreams();
  }

  // 卸载或 keepAlive 失活时中止进行中的流，避免后台继续写入
  onUnmounted(abortAllStreams);
  onDeactivated(abortAllStreams);

  /** 当前会话消息 → 后端历史格式（仅 user/assistant，跳过流式中的空消息）。 */
  function buildHistory(): ChatHistoryMessage[] {
    return chatSession
      .getActiveMessages(sessionMode)
      .value.filter(
        (m) => (m.msg_type === "user" || m.msg_type === "agent") && m.content,
      )
      .map((m) => ({
        role: m.msg_type === "user" ? "user" : "assistant",
        content: m.content as string,
      }));
  }

  // 最近一次发送的载荷（供「重试」幂等复用：不追加用户气泡，只重跑流）
  let lastPayload: {
    text: string;
    files?: ChatFileRef[];
    unitContext?: Record<string, unknown>;
  } | null = null;

  async function handleUserSend(
    text: string,
    files?: ChatFileRef[],
    unitContext?: Record<string, unknown>,
    retryAgentId?: string,
  ) {
    let sessionId = chatSession.getActiveId(sessionMode).value;
    if (!sessionId) {
      sessionId = chatSession.createSession(sessionMode);
    }

    // 创建 AbortController 用于取消，按会话记录
    const controller = new AbortController();
    abortControllers.set(controllerKey(sessionId), controller);

    // 重试时复用同一 agent 气泡（先重置为空 + 流式态），不追加用户消息
    if (!retryAgentId) {
      const userMsg: Message = {
        id: generateId(),
        msg_type: "user",
        content: text,
        created_at: new Date().toISOString(),
      };
      chatSession.addMessage(sessionMode, sessionId, userMsg);
    } else {
      chatSession.clearToolAttachments(retryAgentId);
      chatSession.clearAgentSegments(retryAgentId);
      chatSession.updateMessage(sessionMode, sessionId, retryAgentId, {
        content: "",
        streaming: true,
        error: false,
        thinking: "",
      });
    }
    lastPayload = { text, files, unitContext };

    chatSession.setRunning(sessionMode);

    // agent 消息延迟到第一个 text delta 时再创建，
    // 确保工具调用气泡排在最终回答之前
    let agentMsgId: string | null = retryAgentId ?? null;
    let acc = "";
    let thinkingAcc = "";

    function ensureAgentMsg(): string {
      if (!agentMsgId) {
        agentMsgId = generateId();
        // sessionId is guaranteed to be non-null after createSession above
        if (sessionId) {
          chatSession.addMessage(sessionMode, sessionId, {
            id: agentMsgId,
            msg_type: "agent",
            content: "",
            streaming: true,
            created_at: new Date().toISOString(),
          });
        }
      }
      return agentMsgId;
    }

    await streamChat(buildHistory(), {
      mode: chatMode,
      files,
      unitContext,
      signal: controller.signal,
      onDelta(delta) {
        acc += delta;
        const id = ensureAgentMsg();
        chatSession.updateMessage(sessionMode, sessionId, id, { content: acc });
        // 片段流：文本增量拼接进"最后一个文本片段"（若在工具之后，则开新文本片段）
        chatSession.updateTextSegment(id, delta);
      },
      onThinking(thinking) {
        thinkingAcc += thinking;
        const id = ensureAgentMsg();
        chatSession.updateMessage(sessionMode, sessionId, id, {
          thinking: thinkingAcc,
        });
      },
      onToolCall(event) {
        // dsh 式内联：工具卡片挂到 agent 气泡下（不进消息列表），
        // 并按事件顺序插入片段流——渲染时出现在调用它那句话的正下方
        const toolMsg: Message = {
          id: generateId(),
          msg_type: "tool",
          tool_name: event.name,
          input: event.args,
          output: null,
          status: "running",
          // 协议 v2.1：记录 tool_call_id，结果事件按 id 精确配对（修复并发同名工具错配）
          tool_call_id: event.id,
          created_at: new Date().toISOString(),
        };
        const agentId = ensureAgentMsg();
        chatSession.attachTool(agentId, toolMsg);
        chatSession.appendSegment(agentId, {
          kind: "tool",
          toolId: toolMsg.id,
        });
      },
      onToolResult(event) {
        // 协议 v2.1：优先按 id 精确配对；旧后端无 id 时退化为最近同名未完成匹配
        const tools = chatSession.getToolAttachments(agentMsgId ?? "");
        let target: Message | null = null;
        if (event.id) {
          target =
            [...tools]
              .reverse()
              .find((m) => (m as any).tool_call_id === event.id) ?? null;
        }
        if (!target) {
          for (let i = tools.length - 1; i >= 0; i--) {
            const m = tools[i];
            if (
              m.msg_type === "tool" &&
              (m as any).tool_name === event.name &&
              !(m as any).output
            ) {
              target = m;
              break;
            }
          }
        }
        if (target) {
          // 图表来源优先级（协议 v2.2）：tool_result.images（后端完整携带）
          // → code_exec done 帧已写入的 images → 从 preview 文本兜底提取 URL
          const prevOut = (target.output as any[] | null) ?? [];
          const prevImages: string[] =
            (prevOut.find((o) => o?.name === "run_code") as any)?.images ?? [];
          target.output = [
            {
              name: event.name,
              preview: event.preview,
              images:
                event.images && event.images.length > 0
                  ? event.images
                  : prevImages.length > 0
                    ? prevImages
                    : extractImageUrls(event.preview),
            },
          ];
          target.status = event.ok ? "success" : "error";
          target.error = event.ok ? undefined : event.error;
          target.duration_ms = event.duration_ms;
        }
      },
      onClarify(event) {
        // 确保前面的文本 delta 已写入 agent 消息
        if (acc) ensureAgentMsg();
        // 创建 clarify 卡片消息
        const clarifyMsg: Message = {
          id: generateId(),
          msg_type: "clarify",
          content: JSON.stringify(event.questions),
          answered: false,
          created_at: new Date().toISOString(),
        };
        chatSession.addMessage(sessionMode, sessionId, clarifyMsg);
      },
      onCodeExec(event) {
        // 协议 v2.1：优先按 id 精确配对（并发多个 run_code 时不串）
        const tools = chatSession.getToolAttachments(agentMsgId ?? "");
        let target: Message | null = null;
        if (event.id) {
          target =
            [...tools]
              .reverse()
              .find((m) => (m as any).tool_call_id === event.id) ?? null;
        }
        if (!target) {
          for (let i = tools.length - 1; i >= 0; i--) {
            const m = tools[i];
            if (m.msg_type === "tool" && (m as any).tool_name === "run_code") {
              target = m;
              break;
            }
          }
        }
        if (!target) return;
        if (event.status === "running") {
          target.output = [{ name: "run_code", preview: "代码执行中…" }];
          target.status = "running";
        } else if (event.status === "done") {
          const parts = [];
          if (event.stdout) parts.push(`输出:\n${event.stdout}`);
          if (event.images?.length)
            parts.push(`图表: ${event.images.length} 张`);
          target.output = [
            {
              name: "run_code",
              preview: parts.join("\n") || "执行完成",
              images: event.images ?? [],
            },
          ];
          target.status = event.ok === false ? "error" : "success";
          target.error = event.ok === false ? event.error : undefined;
          target.duration_ms = event.duration_ms;
        }
      },
      onDone(taskId?: string) {
        abortControllers.delete(controllerKey(sessionId));
        const id = ensureAgentMsg();
        const doneContent = acc || "（未收到回复内容）";
        chatSession.updateMessage(sessionMode, sessionId, id, {
          content: doneContent,
          streaming: false,
          // 附加 task_id 供下载按钮使用
          ...(taskId ? ({ task_id: taskId } as any) : {}),
        });
        chatSession.setRunning(null);

        // solution 模式：写入 task_id 到 session 上
        if (taskId) {
          const sess = chatSession.getActiveSession(sessionMode).value;
          if (sess) {
            (sess as any).taskId = taskId;
          }
        }
      },
      onError(message) {
        abortControllers.delete(controllerKey(sessionId));
        const id = ensureAgentMsg();
        // 用户主动取消时不显示错误
        if (controller.signal.aborted) {
          chatSession.updateMessage(sessionMode, sessionId, id, {
            content: acc || "（已取消）",
            streaming: false,
            error: false,
          });
        } else {
          chatSession.updateMessage(sessionMode, sessionId, id, {
            content: `出错了：${message}`,
            streaming: false,
            error: true, // 供「重试」按钮识别
          });
        }
        chatSession.setRunning(null);
      },
    });
  }

  /** 重试最近一次失败的回答：复用同一 agent 气泡，不追加用户消息（幂等）。 */
  async function retryLast() {
    if (!lastPayload) return;
    const sessionId = chatSession.getActiveId(sessionMode).value;
    if (!sessionId) return;
    // 找最后一条带 error 标记的 agent 消息，复用其气泡
    const msgs = chatSession.getActiveMessages(sessionMode).value;
    let failedId: string | null = null;
    for (let i = msgs.length - 1; i >= 0; i--) {
      const m = msgs[i];
      if (m.msg_type === "agent" && (m as any).error === true) {
        failedId = m.id;
        break;
      }
    }
    if (!failedId) return;
    await handleUserSend(
      lastPayload.text,
      lastPayload.files,
      lastPayload.unitContext,
      failedId,
    );
  }

  /** 无激活会话时，切到最近一条会话（供 onMounted 调用）。 */
  function restoreLatestSession() {
    const active = chatSession.getActiveId(sessionMode).value;
    const sorted = chatSession.getSortedSessions(sessionMode).value;
    if (!active && sorted.length > 0) {
      chatSession.switchSession(sessionMode, sorted[0].id);
    }
    // 如果 sessionMode 从未有过任何会话，自动创建一个
    if (sorted.length === 0) {
      chatSession.createSession(sessionMode);
    }
  }

  return { handleUserSend, restoreLatestSession, cancelStream, retryLast };
}
