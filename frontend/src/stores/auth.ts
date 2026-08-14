import {
  type UserInfo,
  getAuthCallback,
  getAuthLogin,
  getAuthUser,
} from "@/apis/authApi";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

const TOKEN_KEY = "mma:token";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<UserInfo | null>(null);
  const token = ref<string | null>(_loadToken());
  const isContributor = ref(false);
  const loading = ref(false);
  const authReady = ref(false);

  const isLoggedIn = computed(() => !!token.value && !!user.value);
  const displayName = computed(
    () => user.value?.login || user.value?.name || "游客",
  );
  const avatar = computed(() => user.value?.avatar_url || null);
  const initials = computed(() => {
    const name = displayName.value;
    return name ? name.charAt(0).toUpperCase() : "U";
  });

  async function fetchLoginUrl(): Promise<string | null> {
    try {
      const data = await getAuthLogin();
      return data.authorize_url;
    } catch {
      return null;
    }
  }

  async function handleCallback(code: string, state: string): Promise<boolean> {
    loading.value = true;
    try {
      const data = await getAuthCallback(code, state);
      _setSession(data.access_token, data.user);
      authReady.value = true;
      return true;
    } catch {
      authReady.value = true;
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function checkSession(): Promise<boolean> {
    if (!token.value) {
      authReady.value = true;
      return false;
    }
    try {
      const data = await getAuthUser();
      if (data.authenticated && data.user) {
        user.value = data.user;
        isContributor.value = data.is_contributor;
        authReady.value = true;
        return true;
      }
      authReady.value = true;
      return false;
    } catch {
      _clearSession();
      authReady.value = true;
      return false;
    }
  }

  function logout() {
    _clearSession();
  }

  function _setSession(tok: string, u: UserInfo) {
    token.value = tok;
    user.value = u;
    isContributor.value =
      u.login?.toLowerCase() === "zhang66633" ||
      u.login?.toLowerCase() === "shu639";
    _saveToken(tok);
  }

  function _clearSession() {
    token.value = null;
    user.value = null;
    isContributor.value = false;
    authReady.value = true;
    _saveToken(null);
    // 登出时清理本地持久化会话与用户级偏好，避免跨账号泄露
    try {
      localStorage.removeItem("mma-chat-sessions");
      localStorage.removeItem("mma:nickname");
    } catch {
      /* ignore */
    }
  }

  function _loadToken(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  }

  function _saveToken(tok: string | null) {
    try {
      if (tok) localStorage.setItem(TOKEN_KEY, tok);
      else localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* ignore */
    }
  }

  return {
    user,
    token,
    isContributor,
    loading,
    authReady,
    isLoggedIn,
    displayName,
    avatar,
    initials,
    fetchLoginUrl,
    handleCallback,
    checkSession,
    logout,
  };
});
