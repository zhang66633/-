import request from "@/utils/request";
import type { ChatFileRef } from "@/apis/chatApi";

export function createTask(data: { problem: string; mode: string; files?: ChatFileRef[] }) {
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