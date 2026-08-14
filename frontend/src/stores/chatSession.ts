import { ref, computed } from "vue";
import { defineStore } from "pinia";
import type { Message, ToolStatus } from "@/types/response";

export type SessionMode = "chat" | "solution" | "learning" | "qa" | "practice";

export interface ChatSession {
  id: string;
  title: string;
  mode: SessionMode;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

function now() {
  return new Date().toISOString();
}

function genId() {
  return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export const useChatSessionStore = defineStore(
  "chatSession",
  () => {
    const chatSessions = ref<ChatSession[]>([]);
    const solutionSessions = ref<ChatSession[]>([]);
    const learningSessions = ref<ChatSession[]>([]);
    const qaSessions = ref<ChatSession[]>([]);
    const practiceSessions = ref<ChatSession[]>([]);

    const activeChatId = ref<string | null>(null);
    const activeSolutionId = ref<string | null>(null);
    const activeLearningId = ref<string | null>(null);
    const activeQaId = ref<string | null>(null);
    const activePracticeId = ref<string | null>(null);

    /** 当前正在运行的模式（仅允许一个，避免三页互串）。null = 空闲。 */
    const runningMode = ref<SessionMode | null>(null);

    function getIsRunning(mode: SessionMode) {
      return runningMode.value === mode;
    }
    function setRunning(mode: SessionMode | null) {
      runningMode.value = mode;
    }

    function getSessions(mode: SessionMode) {
      switch (mode) {
        case "chat": return chatSessions;
        case "solution": return solutionSessions;
        case "learning": return learningSessions;
        case "qa": return qaSessions;
        case "practice": return practiceSessions;
      }
    }

    function getActiveId(mode: SessionMode) {
      switch (mode) {
        case "chat": return activeChatId;
        case "solution": return activeSolutionId;
        case "learning": return activeLearningId;
        case "qa": return activeQaId;
        case "practice": return activePracticeId;
      }
    }

    function setActiveId(mode: SessionMode, id: string | null) {
      switch (mode) {
        case "chat": activeChatId.value = id; break;
        case "solution": activeSolutionId.value = id; break;
        case "learning": activeLearningId.value = id; break;
        case "qa": activeQaId.value = id; break;
        case "practice": activePracticeId.value = id; break;
      }
    }

    const sortedChatSessions = computed(() =>
      [...chatSessions.value].sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()),
    );
    const sortedSolutionSessions = computed(() =>
      [...solutionSessions.value].sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()),
    );
    const sortedLearningSessions = computed(() =>
      [...learningSessions.value].sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()),
    );
    const sortedQaSessions = computed(() =>
      [...qaSessions.value].sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()),
    );
    const sortedPracticeSessions = computed(() =>
      [...practiceSessions.value].sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()),
    );

    function getSortedSessions(mode: SessionMode) {
      switch (mode) {
        case "chat": return sortedChatSessions;
        case "solution": return sortedSolutionSessions;
        case "learning": return sortedLearningSessions;
        case "qa": return sortedQaSessions;
        case "practice": return sortedPracticeSessions;
      }
    }

    const activeChatSession = computed(() =>
      chatSessions.value.find((s) => s.id === activeChatId.value) ?? null,
    );
    const activeSolutionSession = computed(() =>
      solutionSessions.value.find((s) => s.id === activeSolutionId.value) ?? null,
    );
    const activeLearningSession = computed(() =>
      learningSessions.value.find((s) => s.id === activeLearningId.value) ?? null,
    );
    const activeQaSession = computed(() =>
      qaSessions.value.find((s) => s.id === activeQaId.value) ?? null,
    );
    const activePracticeSession = computed(() =>
      practiceSessions.value.find((s) => s.id === activePracticeId.value) ?? null,
    );

    function getActiveSession(mode: SessionMode) {
      switch (mode) {
        case "chat": return activeChatSession;
        case "solution": return activeSolutionSession;
        case "learning": return activeLearningSession;
        case "qa": return activeQaSession;
        case "practice": return activePracticeSession;
      }
    }

    const activeChatMessages = computed(() => activeChatSession.value?.messages ?? []);
    const activeSolutionMessages = computed(() => activeSolutionSession.value?.messages ?? []);
    const activeLearningMessages = computed(() => activeLearningSession.value?.messages ?? []);
    const activeQaMessages = computed(() => activeQaSession.value?.messages ?? []);
    const activePracticeMessages = computed(() => activePracticeSession.value?.messages ?? []);

    function getActiveMessages(mode: SessionMode) {
      switch (mode) {
        case "chat": return activeChatMessages;
        case "solution": return activeSolutionMessages;
        case "learning": return activeLearningMessages;
        case "qa": return activeQaMessages;
        case "practice": return activePracticeMessages;
      }
    }

    /** 每个模式最多持久化的会话数，超出淘汰最旧（按 updatedAt）。 */
    const MAX_SESSIONS_PER_MODE = 60;

    function trimSessions(mode: SessionMode) {
      const list = getSessions(mode).value;
      if (list.length <= MAX_SESSIONS_PER_MODE) return;
      // 按 updatedAt 降序，保留最新 N 条，就地淘汰最旧会话
      const keepIds = new Set(
        [...list]
          .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
          .slice(0, MAX_SESSIONS_PER_MODE)
          .map((s) => s.id),
      );
      for (let i = list.length - 1; i >= 0; i--) {
        if (!keepIds.has(list[i].id)) list.splice(i, 1);
      }
    }

    function createSession(mode: SessionMode): string {
      const id = genId();
      const titleMap: Record<SessionMode, string> = {
        chat: "新对话",
        solution: "新方案",
        learning: "新学习",
        qa: "新问题",
        practice: "新练习",
      };
      const session: ChatSession = {
        id,
        title: titleMap[mode],
        mode,
        messages: [],
        createdAt: now(),
        updatedAt: now(),
      };
      getSessions(mode).value.push(session);
      setActiveId(mode, id);
      trimSessions(mode);
      return id;
    }

    function switchSession(mode: SessionMode, id: string) {
      const list = getSessions(mode).value;
      if (list.some((s) => s.id === id)) {
        setActiveId(mode, id);
      }
    }

    function deleteSession(mode: SessionMode, id: string) {
      const list = getSessions(mode).value;
      const idx = list.findIndex((s) => s.id === id);
      if (idx === -1) return;
      list.splice(idx, 1);
      const activeId = getActiveId(mode);
      if (activeId.value === id) {
        const sorted = getSortedSessions(mode).value;
        setActiveId(mode, sorted[0]?.id ?? null);
      }
    }

    function renameSession(mode: SessionMode, id: string, newTitle: string) {
      const list = getSessions(mode).value;
      const session = list.find((s) => s.id === id);
      if (!session) return;
      session.title = newTitle.trim() || "新对话";
      session.updatedAt = now();
    }

    function addMessage(mode: SessionMode, sessionId: string, msg: Message) {
      const list = getSessions(mode).value;
      const session = list.find((s) => s.id === sessionId);
      if (!session) return;
      session.messages.push(msg);
      session.updatedAt = now();
      const defaultTitle: Record<SessionMode, string> = {
        chat: "新对话",
        solution: "新方案",
        learning: "新学习",
        qa: "新问题",
        practice: "新练习",
      };
      if (session.title === defaultTitle[mode] && msg.msg_type === "user" && msg.content) {
        session.title = msg.content.slice(0, 30) + (msg.content.length > 30 ? "..." : "");
      }
    }

    /** 流式更新同一条消息（就地累加/替换 content，或更新 streaming / thinking / status 标记）。 */
    function updateMessage(
      mode: SessionMode,
      sessionId: string,
      msgId: string,
      patch: Partial<Pick<Message, "content" | "streaming">> & {
        thinking?: string;
        status?: ToolStatus;
        output?: unknown[];
        answered?: boolean;
      },
    ) {
      const list = getSessions(mode).value;
      const session = list.find((s) => s.id === sessionId);
      if (!session) return;
      const msg = session.messages.find((m) => m.id === msgId);
      if (!msg) return;
      if (patch.content !== undefined) msg.content = patch.content;
      if (patch.streaming !== undefined) msg.streaming = patch.streaming;
      if (patch.thinking !== undefined) (msg as any).thinking = patch.thinking;
      if (patch.status !== undefined) (msg as any).status = patch.status;
      if (patch.output !== undefined) (msg as any).output = patch.output;
      if (patch.answered !== undefined && "answered" in msg) (msg as any).answered = patch.answered;
      session.updatedAt = now();
    }

    function clearActive(mode: SessionMode) {
      setActiveId(mode, null);
    }

    /** 显式新建会话（不清空当前会话）。 */
    function newSession(mode: SessionMode): string {
      return createSession(mode);
    }

    return {
      chatSessions, solutionSessions, learningSessions, qaSessions, practiceSessions,
      activeChatId, activeSolutionId, activeLearningId, activeQaId, activePracticeId,
      runningMode,
      sortedChatSessions, sortedSolutionSessions, sortedLearningSessions, sortedQaSessions, sortedPracticeSessions,
      activeChatSession, activeSolutionSession, activeLearningSession, activeQaSession, activePracticeSession,
      activeChatMessages, activeSolutionMessages, activeLearningMessages, activeQaMessages, activePracticeMessages,
      createSession, newSession, switchSession, deleteSession, renameSession,
      addMessage, updateMessage, clearActive,
      getSessions, getActiveId, getSortedSessions, getActiveSession, getActiveMessages,
      getIsRunning, setRunning,
    };
  },
  {
    persist: {
      key: "mma-chat-sessions",
      storage: localStorage,
      pick: ["chatSessions", "solutionSessions", "learningSessions", "qaSessions", "practiceSessions",
             "activeChatId", "activeSolutionId", "activeLearningId", "activeQaId", "activePracticeId"],
    },
  },
);