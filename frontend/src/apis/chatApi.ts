/** 自由问答（纯对话）SSE 流式接口封装。
 *
 * 不走 axios（不便读流），用 fetch + ReadableStream 解析 SSE 分帧。
 */

export interface ChatHistoryMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

/** 聊天附件引用（已上传的文件） */
export interface ChatFileRef {
  file_id: string;
  filename: string;
}

export interface ToolCallEvent {
  /** 工具调用 id（协议 v2.1：tool_result/code_exec 回声，用于精确配对） */
  id?: string;
  name: string;
  args: Record<string, unknown>;
}

export interface ToolResultEvent {
  /** 与 tool_call 对齐的 id（协议 v2.1；缺失时前端退化按 name 匹配） */
  id?: string;
  name: string;
  preview: string;
  ok?: boolean;
  duration_ms?: number;
  error?: string;
}

export interface ClarifyEvent {
  questions: Array<{
    question: string;
    options: Array<{ label: string; description?: string }>;
    multiSelect?: boolean;
  }>;
}

export interface CodeExecEvent {
  status: "running" | "done";
  /** 与 tool_call 对齐的 id（协议 v2.1） */
  id?: string;
  stdout?: string;
  images?: string[];
  ok?: boolean;
  duration_ms?: number;
  error?: string;
}

export interface StreamChatOptions {
  /** 每次收到增量文本时回调 */
  onDelta: (delta: string) => void;
  /** LLM 决定调用某个工具时回调（args 已完整） */
  onToolCall?: (event: ToolCallEvent) => void;
  /** 工具执行完成时回调（含结果预览） */
  onToolResult?: (event: ToolResultEvent) => void;
  /** LLM 需要用户澄清时回调（前端渲染选项卡片） */
  onClarify?: (event: ClarifyEvent) => void;
  /** 代码执行状态变化回调 */
  onCodeExec?: (event: CodeExecEvent) => void;
  /** 思考模式：推理模型的思考过程增量回调 */
  onThinking?: (thinking: string) => void;
  /** 流正常结束回调（可选传 taskId） */
  onDone?: (taskId?: string) => void;
  /** 出错回调（网络错误或服务端 error 帧） */
  onError?: (message: string) => void;
  /** 可选：外部中止 */
  signal?: AbortSignal;
  useRag?: boolean;
  /** 对话模式：chat=自由问答（默认），teach=教学模式（引导式），learning=学习中心（单元感知） */
  mode?: "chat" | "teach" | "learning" | "practice";
  /** 本轮附带的文件引用 */
  files?: ChatFileRef[];
  /** 学习模式专用：当前学习单元的上下文 */
  unitContext?: Record<string, unknown>;
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

function getToken(): string | null {
  return localStorage.getItem("mma:token");
}

/** 上传聊天附件到 /files/upload，返回 file_id + filename */
export async function uploadChatFile(file: File): Promise<ChatFileRef> {
  const formData = new FormData();
  formData.append("file", file);

  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const resp = await fetch(`${BASE_URL}/files/upload`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`上传失败 (${resp.status}): ${text || resp.statusText}`);
  }

  const data = await resp.json();
  return { file_id: data.file_id, filename: data.filename ?? file.name };
}

export async function streamChat(
  messages: ChatHistoryMessage[],
  opts: StreamChatOptions,
): Promise<void> {
  const {
    onDelta,
    onToolCall,
    onToolResult,
    onClarify,
    onCodeExec,
    onThinking,
    onDone,
    onError,
    signal,
    useRag = false,
    mode = "chat",
    files,
    unitContext,
  } = opts;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  // 收集所有非 delta 事件，在 [DONE] 时传给 onDone
  let finalTaskId: string | undefined;

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        messages,
        use_rag: useRag,
        mode,
        files: files ?? [],
        ...(unitContext ? { unit_context: unitContext } : {}),
      }),
      signal,
    });
  } catch (e: any) {
    if (e?.name === "AbortError") return;
    onError?.(`网络错误，无法连接后端：${e?.message ?? e}`);
    return;
  }

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    onError?.(`请求失败 (${response.status})：${text || response.statusText}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onError?.("浏览器不支持流式读取");
    return;
  }

  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // 归一化 \r\n 后按空行切帧（SSE 事件以空行分隔）
      const frames = buffer.replace(/\r\n/g, "\n").split("\n\n");
      buffer = frames.pop() ?? "";

      for (const frame of frames) {
        // 聚合同一事件内的多行 data: 字段（以 \n 拼接）
        const dataLines: string[] = [];
        for (const line of frame.split("\n")) {
          if (line.startsWith("data:"))
            dataLines.push(line.slice(5).replace(/^ /, ""));
        }
        if (dataLines.length === 0) continue;
        const payload = dataLines.join("\n");

        if (payload === "[DONE]") {
          onDone?.(finalTaskId);
          return;
        }

        try {
          const obj = JSON.parse(payload);
          if (obj.error) {
            onError?.(obj.error);
            return;
          }
          if (obj.done && obj.task_id) {
            finalTaskId = obj.task_id;
          }
          if (obj.delta) {
            onDelta(obj.delta);
          }
          if (obj.tool_call) {
            onToolCall?.(obj.tool_call);
          }
          if (obj.tool_result) {
            onToolResult?.(obj.tool_result);
          }
          if (obj.clarify) {
            onClarify?.(obj.clarify);
          }
          if (obj.code_exec) {
            onCodeExec?.(obj.code_exec);
          }
          if (obj.thinking) {
            onThinking?.(obj.thinking);
          }
        } catch (e) {
          console.warn("SSE 帧 JSON 解析失败:", payload, e);
        }
      }
    }
    onDone?.(finalTaskId);
  } catch (e: any) {
    if (e?.name !== "AbortError") {
      onError?.(`流读取中断：${e?.message ?? e}`);
    }
  }
}
