/** 对应后端消息结构定义 */
import type { AgentType } from "./enum";

/** 系统消息类型 */
export type SystemMessageType = "info" | "warning" | "success" | "error";

/** 工具执行状态 */
export type ToolStatus = "running" | "success" | "error";

/** 消息基础接口 */
export interface BaseMessage {
  id: string;
  created_at?: string;
  msg_type: "system" | "agent" | "user" | "tool" | "clarify";
  content?: string | null;
  /** 流式增量更新中（此时跳过打字机效果，直接全量渲染） */
  streaming?: boolean;
}

/** 工具调用消息 */
export interface ToolMessage extends BaseMessage {
  msg_type: "tool";
  tool_name: string;
  input: Record<string, unknown> | null;
  output: unknown[] | null;
  /** 执行状态 */
  status?: ToolStatus;
  /** 错误信息（status === "error" 时） */
  error?: string;
  /** 执行耗时（毫秒，事件协议 v2 tool_result.duration_ms） */
  duration_ms?: number;
  /** 后端 ok 标志（事件协议 v2 tool_result.ok） */
  ok?: boolean;
}

/** 系统通知消息 */
export interface SystemMessage extends BaseMessage {
  msg_type: "system";
  type: SystemMessageType;
}

/** 用户消息 */
export interface UserMessage extends BaseMessage {
  msg_type: "user";
}

/** Agent 消息基类 */
export interface AgentMessage extends BaseMessage {
  msg_type: "agent";
  /** 流水线 agent 类型；纯对话（chat/teach）消息无此字段 */
  agent_type?: AgentType;
  /** 思考过程 / 推理链内容（SSE thinking 事件累积） */
  thinking?: string;
  /** 出错标志（onError 置位，供「重试」按钮使用） */
  error?: boolean;
}

/** 澄清问题选项 */
export interface ClarifyOption {
  label: string;
  description?: string;
}

/** 澄清问题 */
export interface ClarifyQuestion {
  question: string;
  options: ClarifyOption[];
  multiSelect?: boolean;
}

/** 澄清卡片消息（LLM 调用 ask_user 后由后端推送） */
export interface ClarifyMessage extends BaseMessage {
  msg_type: "clarify";
  /** JSON 序列化的 ClarifyQuestion[] */
  content: string;
  /** 用户是否已作答 */
  answered?: boolean;
}

// ── 工具输出接口 ──────────────────────────────

/** 代码执行工具输出 */
export interface RunCodeOutput {
  name: "run_code";
  preview: string;
  stdout?: string;
  images?: string[];
  error?: string;
}

/** 搜索结果条目 */
export interface SearchResultItem {
  title: string;
  snippet: string;
  url?: string;
}

/** 搜索工具输出 */
export interface SearchOutput {
  name: string;
  preview: string;
  results?: SearchResultItem[];
}

/** 数学计算工具输出 */
export interface MathToolOutput {
  name: "sympy_compute" | "solve_optimization";
  preview: string;
  latex?: string;
  result?: string;
}

/** 通用工具输出（回退类型） */
export interface GenericToolOutput {
  name: string;
  preview: string;
}

/** 所有消息类型的联合类型 */
export type Message =
  | SystemMessage
  | UserMessage
  | AgentMessage
  | ToolMessage
  | ClarifyMessage;
