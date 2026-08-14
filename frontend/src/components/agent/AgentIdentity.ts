/**
 * Agent 身份配置 — 颜色、emoji、中文标签
 *
 * 用于 BubbleAvatar（头像 emoji + 颜色点）与 BubbleAgent（标签颜色 + 流式指示）。
 */
import { AgentType } from "@/types/enum";

export interface AgentIdentityConfig {
  /** Tailwind 背景色 class（颜色点、脉冲指示器） */
  color: string;
  /** 显示 emoji */
  emoji: string;
  /** 中文简称 */
  label: string;
  /** Tailwind 文字颜色 class */
  textColor: string;
}

export const AGENT_IDENTITY: Record<AgentType, AgentIdentityConfig> = {
  [AgentType.ORCHESTRATOR]: {
    color: "bg-violet-500",
    emoji: "🎯",
    label: "主控",
    textColor: "text-violet-600 dark:text-violet-400",
  },
  [AgentType.ANALYSIS]: {
    color: "bg-blue-500",
    emoji: "🔍",
    label: "分析",
    textColor: "text-blue-600 dark:text-blue-400",
  },
  [AgentType.MODELING]: {
    color: "bg-emerald-500",
    emoji: "🧮",
    label: "建模",
    textColor: "text-emerald-600 dark:text-emerald-400",
  },
  [AgentType.SOLVING]: {
    color: "bg-amber-500",
    emoji: "⚡",
    label: "求解",
    textColor: "text-amber-600 dark:text-amber-400",
  },
  [AgentType.VERIFICATION]: {
    color: "bg-rose-500",
    emoji: "✅",
    label: "验证",
    textColor: "text-rose-600 dark:text-rose-400",
  },
  [AgentType.WRITING]: {
    color: "bg-cyan-500",
    emoji: "📝",
    label: "写作",
    textColor: "text-cyan-600 dark:text-cyan-400",
  },
};

/** 根据 agent_type 获取身份配置，无匹配返回 null */
export function getAgentIdentity(
  agentType?: AgentType,
): AgentIdentityConfig | null {
  if (!agentType) return null;
  return AGENT_IDENTITY[agentType] ?? null;
}
