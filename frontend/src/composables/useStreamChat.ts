/** 流式对话组合式函数 — /chat 与 /teach 页共用。
 *
 * 负责：会话创建/复用、用户消息与 agent 占位消息写入、
 * 调 SSE 接口并流式就地累加、工具调用可视化、运行态管理、最新会话恢复。
 */
import { ref } from "vue";
import { useChatSessionStore, type SessionMode } from "@/stores/chatSession";
import { streamChat, type ChatHistoryMessage, type ChatFileRef } from "@/apis/chatApi";
import type { Message } from "@/types/response";

function generateId() {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export function useStreamChat(sessionMode: SessionMode, chatMode: "chat" | "teach") {
  const chatSession = useChatSessionStore();
  const abortController = ref<AbortController | null>(null);

  /** 取消当前正在进行的流式请求。 */
  function cancelStream() {
    if (abortController.value) {
      abortController.value.abort();
      abortController.value = null;
    }
    chatSession.setRunning(null);
  }

  /** 当前会话消息 → 后端历史格式（仅 user/assistant，跳过流式中的空消息）。 */
  function buildHistory(): ChatHistoryMessage[] {
    return chatSession
      .getActiveMessages(sessionMode)
      .value.filter((m) => (m.msg_type === "user" || m.msg_type === "agent") && m.content)
      .map((m) => ({
        role: m.msg_type === "user" ? "user" : "assistant",
        content: m.content as string,
      }));
  }

  async function handleUserSend(text: string, files?: ChatFileRef[]) {
    let sessionId = chatSession.getActiveId(sessionMode).value;
    if (!sessionId) {
      sessionId = chatSession.createSession(sessionMode);
    }

    // 创建 AbortController 用于取消
    const controller = new AbortController();
    abortController.value = controller;

    const userMsg: Message = {
      id: generateId(),
      msg_type: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    chatSession.addMessage(sessionMode, sessionId, userMsg);

    chatSession.setRunning(sessionMode);

    // agent 消息延迟到第一个 text delta 时再创建，
    // 确保工具调用气泡排在最终回答之前
    let agentMsgId: string | null = null;
    let acc = "";

    function ensureAgentMsg(): string {
      if (!agentMsgId) {
        agentMsgId = generateId();
        chatSession.addMessage(sessionMode, sessionId, {
          id: agentMsgId,
          msg_type: "agent",
          content: "",
          streaming: true,
          created_at: new Date().toISOString(),
        });
      }
      return agentMsgId;
    }

    await streamChat(buildHistory(), {
      mode: chatMode,
      files,
      signal: controller.signal,
      onDelta(delta) {
        acc += delta;
        const id = ensureAgentMsg();
        chatSession.updateMessage(sessionMode, sessionId, id, { content: acc });
      },
      onToolCall(event) {
        const toolMsg: Message = {
          id: generateId(),
          msg_type: "tool",
          tool_name: event.name,
          input: event.args,
          output: null,
          created_at: new Date().toISOString(),
        };
        chatSession.addMessage(sessionMode, sessionId, toolMsg);
      },
      onToolResult(event) {
        // 找到最近一条同名 tool 消息，更新其 output
        const msgs = chatSession.getActiveMessages(sessionMode).value;
        for (let i = msgs.length - 1; i >= 0; i--) {
          const m = msgs[i];
          if (m.msg_type === "tool" && (m as any).tool_name === event.name && !(m as any).output) {
            chatSession.updateMessage(sessionMode, sessionId, m.id, {
              output: [{ name: event.name, preview: event.preview }],
            } as any);
            break;
          }
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
        } as any;
        chatSession.addMessage(sessionMode, sessionId, clarifyMsg);
      },
      onCodeExec(event) {
        // 更新最近一条 run_code 工具消息的 output
        const msgs = chatSession.getActiveMessages(sessionMode).value;
        for (let i = msgs.length - 1; i >= 0; i--) {
          const m = msgs[i];
          if (m.msg_type === "tool" && (m as any).tool_name === "run_code") {
            if (event.status === "running") {
              chatSession.updateMessage(sessionMode, sessionId, m.id, {
                output: [{ name: "run_code", preview: "代码执行中…" }],
              } as any);
            } else if (event.status === "done") {
              const parts = [];
              if (event.stdout) parts.push(`输出:\n${event.stdout}`);
              if (event.images?.length) parts.push(`图表: ${event.images.length} 张`);
              chatSession.updateMessage(sessionMode, sessionId, m.id, {
                output: [{
                  name: "run_code",
                  preview: parts.join("\n") || "执行完成",
                  images: event.images ?? [],
                }],
              } as any);
            }
            break;
          }
        }
      },
      onDone() {
        abortController.value = null;
        const id = ensureAgentMsg();
        chatSession.updateMessage(sessionMode, sessionId, id, {
          content: acc || "（未收到回复内容）",
          streaming: false,
        });
        chatSession.setRunning(null);
      },
      onError(message) {
        abortController.value = null;
        const id = ensureAgentMsg();
        // 用户主动取消时不显示错误
        if (controller.signal.aborted) {
          chatSession.updateMessage(sessionMode, sessionId, id, {
            content: acc || "（已取消）",
            streaming: false,
          });
        } else {
          chatSession.updateMessage(sessionMode, sessionId, id, {
            content: `出错了：${message}`,
            streaming: false,
          });
        }
        chatSession.setRunning(null);
      },
    });
  }

  /** 无激活会话时，切到最近一条会话（供 onMounted 调用）。 */
  function restoreLatestSession() {
    const active = chatSession.getActiveId(sessionMode).value;
    const sorted = chatSession.getSortedSessions(sessionMode).value;
    if (!active && sorted.length > 0) {
      chatSession.switchSession(sessionMode, sorted[0].id);
    }
  }

  return { handleUserSend, restoreLatestSession, cancelStream };
}