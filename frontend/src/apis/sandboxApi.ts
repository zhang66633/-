import { request } from "@/utils/request";

export interface SandboxStatus {
  backend: "subprocess" | "docker";
  configured: string;
  docker_available: boolean;
  note: string;
}

/** 获取沙箱执行模式状态（设置页/首页徽章用）。 */
export function getSandboxStatus(): Promise<SandboxStatus> {
  return request.get("/sandbox/status").then((r) => r.data);
}
