import request from "@/utils/request";

export interface ApiKeyPayload {
  name: string;
  key: string;
  provider: string;
  model_name: string;
  base_url?: string;
  purpose?: "chat" | "embedding";
}

export interface ApiKeyItem {
  id: string;
  name: string;
  provider: string;
  model_name: string;
  masked_key: string;
  is_default: boolean;
  base_url: string;
  purpose: "chat" | "embedding";
}

export function getMyApiKey() {
  return request.get("/apikeys/mine");
}

export function quickAddApiKey(
  key: string,
  name?: string,
  opts?: {
    provider?: string;
    model_name?: string;
    base_url?: string;
    purpose?: string;
  },
) {
  return request.post("/apikeys/quick", { key, name: name || "", ...opts });
}

export function getApiKeys() {
  return request.get<ApiKeyItem[]>("/apikeys");
}

export function addApiKey(data: ApiKeyPayload) {
  return request.post("/apikeys", data);
}

export function deleteApiKey(id: string) {
  return request.delete(`/apikeys/${id}`);
}

export function setDefaultApiKey(id: string) {
  return request.post(`/apikeys/${id}/default`);
}
