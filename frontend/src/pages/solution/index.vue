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
        @open-paper="openPaperViewer"
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

        <!-- 文件区：上传的附件 + 生成的图表 -->
        <div v-if="currentTaskId" class="mt-4">
          <p class="text-xs font-medium text-foreground mb-2">📁 文件区</p>
          <div v-if="taskFiles.length === 0" class="text-[11px] text-muted-foreground">
            暂无文件（上传的题目/数据与生成的图表会显示在这里）
          </div>
          <div v-else class="space-y-1.5">
            <div
              v-for="f in taskFiles"
              :key="f.url"
              class="flex items-center gap-2 rounded-md border px-2 py-1.5 text-xs hover:bg-accent transition-colors"
            >
              <!-- 生成的图表显示缩略图 -->
              <img
                v-if="f.type === 'figure'"
                :src="f.url"
                class="h-8 w-8 object-cover rounded border shrink-0"
                loading="lazy"
              />
              <FileSpreadsheet v-else-if="f.type === 'xlsx' || f.name.endsWith('.xlsx')" class="h-4 w-4 text-green-500 shrink-0" />
              <Table v-else-if="f.type === 'csv' || f.name.endsWith('.csv')" class="h-4 w-4 text-blue-500 shrink-0" />
              <FileText v-else-if="f.type === 'html' || f.name.endsWith('.html')" class="h-4 w-4 text-orange-500 shrink-0" />
              <Archive v-else-if="f.type === 'zip' || f.name.endsWith('.zip')" class="h-4 w-4 text-purple-500 shrink-0" />
              <Paperclip v-else class="h-4 w-4 text-muted-foreground shrink-0" />
              <span class="flex-1 truncate" :title="f.name">{{ f.name }}</span>
              <a
                :href="f.url"
                :download="f.name"
                class="text-muted-foreground hover:text-foreground shrink-0"
                title="下载"
              >
                <Download class="h-3.5 w-3.5" />
              </a>
            </div>
          </div>
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

          <template v-if="hasExportFiles">
            <p class="text-xs font-medium text-foreground mb-2 mt-4">📊 下载数据</p>
            <button
              v-if="hasXlsxFile"
              class="flex items-center gap-2 w-full rounded-md border px-3 py-2 text-sm hover:bg-accent transition-colors"
              @click="downloadExport('xlsx')"
            >
              <FileSpreadsheet class="h-4 w-4" /> Excel (.xlsx)
            </button>
            <button
              v-if="hasCsvFile"
              class="flex items-center gap-2 w-full rounded-md border px-3 py-2 text-sm hover:bg-accent transition-colors"
              @click="downloadExport('csv')"
            >
              <Table class="h-4 w-4" /> CSV (.csv)
            </button>
          </template>

          <p class="text-xs font-medium text-foreground mb-2 mt-4">📦 打包下载</p>
          <button
            class="flex items-center gap-2 w-full rounded-md border px-3 py-2 text-sm hover:bg-accent transition-colors"
            @click="downloadPackage"
          >
            <Archive class="h-4 w-4" /> 完整结果包 (.zip)
          </button>
        </div>
      </div>
    </Transition>

    <!-- 论文阅读器（全屏浮层） -->
    <PaperViewer
      v-if="showPaperViewer"
      :markdown="paperContent"
      :task-id="currentTaskId ?? undefined"
      @close="closePaperViewer"
    />
  </div>
</template>

<script setup lang="ts">
import type { ChatFileRef } from "@/apis/chatApi";
import { cancelTask, createTask, getTaskFiles } from "@/apis/commonApi";
import ChatArea from "@/components/ChatArea.vue";
import ProgressTimeline, {
  type ProgressStep,
} from "@/components/ProgressTimeline.vue";
import PaperViewer from "@/components/paper/PaperViewer.vue";
import { useChatSessionStore } from "@/stores/chatSession";
import { useTaskStore } from "@/stores/task";
import type { Message } from "@/types/response";
import {
  Archive,
  Download,
  FileDown,
  FileSpreadsheet,
  FileText,
  PanelRight,
  Paperclip,
  Table,
} from "lucide-vue-next";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

const chatSession = useChatSessionStore();
const taskStore = useTaskStore();

const rightPanelOpen = ref(true);

// solution 页关联的 task_id：原本想放 taskStore（持久化），但 messagesByTask
// 不持久化会导致"刷新后显示 Task ID 但 messages 为空"白屏。
// 改为：task_id 仅在本次 session 内存中持有，刷新后用户重新触发即可；
// 任务进度消息本身已通过 chatSession.solutionSessions 持久化（向下兼容）。
const currentTaskId = ref<string | null>(null);
const cancelling = ref(false);

// 文件区：任务的附件 + 生成文件
interface TaskFile {
  type: string;
  name: string;
  url: string;
  size?: number;
}
const taskFiles = ref<TaskFile[]>([]);

async function fetchTaskFiles(taskId: string) {
  try {
    const res = await getTaskFiles(taskId);
    taskFiles.value = res.data?.files ?? [];
  } catch {
    taskFiles.value = [];
  }
}

// 任务确定后拉一次文件区；任务完成（求解出图后）再刷新一次
watch(currentTaskId, (id) => {
  taskFiles.value = [];
  if (id) fetchTaskFiles(id);
});
watch(
  () => taskStore.completed,
  (done) => {
    if (done && currentTaskId.value) fetchTaskFiles(currentTaskId.value);
  },
);
// 求解阶段会陆续产出图表，消息数变化时顺带刷新文件区
watch(
  () => taskStore.messages.length,
  () => {
    if (currentTaskId.value && taskStore.isRunning)
      fetchTaskFiles(currentTaskId.value);
  },
);

const stepDefs: ProgressStep[] = [
  {
    id: "1",
    label: "问题分析",
    description: "识别问题类型，理解题意",
    status: "wait",
  },
  {
    id: "2",
    label: "模型构建",
    description: "选择并建立数学模型",
    status: "wait",
  },
  {
    id: "3",
    label: "数据预处理",
    description: "EDA 探索与数据清洗",
    status: "wait",
  },
  {
    id: "4",
    label: "求解计算",
    description: "生成并执行求解代码",
    status: "wait",
  },
  { id: "5", label: "验证分析", description: "检验模型鲁棒性", status: "wait" },
  { id: "6", label: "结果导出", description: "打包结构化文件", status: "wait" },
  { id: "7", label: "论文写作", description: "生成结构化论文", status: "wait" },
];

// 写作阶段的动态描述：并行生成章节 + 完成计数（node_progress 事件驱动）
const writingDescription = computed(() => {
  if (taskStore.writingStage === "outline")
    return "先写大纲，随后并行生成各章节…";
  if (taskStore.sectionsDone > 0)
    return `并行生成论文章节：已完成 ${taskStore.sectionsDone} 章`;
  if (
    taskStore.writingStage === "abstract" ||
    taskStore.writingStage === "red_team" ||
    taskStore.writingStage === "revise"
  )
    return "正文完成，正在提炼摘要与红队审校";
  return "并行生成论文章节…";
});

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
    if (
      current.includes("分析") ||
      current.includes("检索") ||
      current.includes("计划")
    )
      activeIdx = 0;
    else if (current.includes("模型") || current.includes("建模"))
      activeIdx = 1;
    else if (current.includes("预处理") || current.includes("数据"))
      activeIdx = 2;
    else if (current.includes("求解") || current.includes("计算"))
      activeIdx = 3;
    else if (current.includes("验证")) activeIdx = 4;
    else if (current.includes("导出") || current.includes("打包"))
      activeIdx = 5;
    else if (
      current.includes("写作") ||
      current.includes("整合") ||
      current.includes("输出")
    )
      activeIdx = 6;
  }
  return stepDefs.map((s, i) => ({
    ...s,
    // 写作步骤展示并行生成动态描述
    description: s.id === "7" ? writingDescription.value : s.description,
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
      chatSession.updateMessage("solution", sid, msg.id, {
        content: msg.content,
      });
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

async function handleUserSend(text: string, files?: ChatFileRef[]) {
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
    const res = await createTask({ problem: text, mode: "execute", files });
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
async function downloadExport(format: "md" | "docx" | "xlsx" | "csv") {
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
    const ext = format;
    a.download = `paper.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e: any) {
    console.error("导出失败：", e);
  }
}

/** 下载完整结果包 */
async function downloadPackage() {
  if (!currentTaskId.value) return;
  try {
    const { default: request } = await import("@/utils/request");
    const resp = await request.get(`/tasks/${currentTaskId.value}/package`, {
      responseType: "blob",
    });
    const blob = new Blob([resp.data]);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentTaskId.value}_results.zip`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e: any) {
    console.error("打包下载失败：", e);
  }
}

/** 是否有导出文件（xlsx/csv） */
const hasXlsxFile = computed(() =>
  taskFiles.value.some((f) => f.name.endsWith(".xlsx")),
);
const hasCsvFile = computed(() =>
  taskFiles.value.some((f) => f.name.endsWith(".csv")),
);
const hasExportFiles = computed(() => hasXlsxFile.value || hasCsvFile.value);

// ---- 论文阅读器 ----
const showPaperViewer = ref(false);
const paperContent = ref("");

function openPaperViewer() {
  // 从 displayMessages 中找到论文消息
  const paperMsg = displayMessages.value.find(
    (m) => typeof m.id === "string" && m.id.startsWith("final-"),
  );
  if (paperMsg?.content) {
    paperContent.value = paperMsg.content;
    showPaperViewer.value = true;
  }
}

function closePaperViewer() {
  showPaperViewer.value = false;
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
  if (
    !chatSession.activeSolutionId &&
    chatSession.sortedSolutionSessions.length > 0
  ) {
    chatSession.switchSession(
      "solution",
      chatSession.sortedSolutionSessions[0].id,
    );
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