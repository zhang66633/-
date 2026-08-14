import { request } from "@/utils/request";

export interface UserInfo {
  id: number;
  login: string;
  name?: string | null;
  email?: string | null;
  avatar_url?: string | null;
}

export interface LoginUrlResponse {
  authorize_url: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

export interface UserResponse {
  authenticated: boolean;
  user: UserInfo | null;
  is_contributor: boolean;
}

/** 获取 GitHub OAuth 授权 URL。 */
export function getAuthLogin(): Promise<LoginUrlResponse> {
  return request.get("/auth/login").then((r) => r.data);
}

/** 用 OAuth code 换取 JWT。非贡献者会被后端 403 拒绝。state 用于防 login CSRF。 */
export function getAuthCallback(code: string, state: string): Promise<TokenResponse> {
  return request.get("/auth/callback", { params: { code, state } }).then((r) => r.data);
}

/** 获取当前登录用户信息。 */
export function getAuthUser(): Promise<UserResponse> {
  return request.get("/auth/user").then((r) => r.data);
}
