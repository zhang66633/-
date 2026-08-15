import type { ChatFileRef } from "@/apis/chatApi";
import request from "@/utils/request";

export function createTask(data: {
  problem: string;
  mode: string;
  files?: ChatFileRef[];
}) {
  return request.post("/tasks", data);
}

export function cancelTask(taskId: string) {
  return request.post(`/tasks/${taskId}/cancel`);
}

export function getTask(taskId: string) {
  return request.get(`/tasks/${taskId}`);
}

export function getTaskFiles(taskId: string) {
  return request.get(`/tasks/${taskId}/files`);
}

/** 拉取任务持久化事件流（协议 v2.1：plan/node_start/node_end/tool_call/... 回放） */
export function getTaskEvents(taskId: string, after = 0, limit = 500) {
  return request.get(`/tasks/${taskId}/events`, { params: { after, limit } });
}
