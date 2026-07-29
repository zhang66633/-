<template>
  <div class="relative">
    <!-- 未登录 -->
    <template v-if="!auth.isLoggedIn">
      <DropdownMenu>
        <DropdownMenuTrigger>
          <button
            class="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          >
            <Menu class="h-4 w-4" />
            <span class="hidden sm:inline">菜单</span>
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent class="w-40">
          <DropdownMenuItem @click="handleAction('login')">
            <Github class="h-4 w-4" />
            <span>GitHub 登录</span>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem @click="handleAction('apikeys')">
            <Key class="h-4 w-4" />
            <span>API Keys</span>
          </DropdownMenuItem>
          <DropdownMenuItem @click="handleAction('settings')">
            <Settings class="h-4 w-4" />
            <span>设置</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </template>

    <!-- 已登录 -->
    <template v-else>
      <DropdownMenu>
        <DropdownMenuTrigger>
          <button
            class="flex items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-accent transition-colors"
          >
            <Avatar class="h-8 w-8">
              <AvatarImage v-if="auth.avatar" :src="auth.avatar" :alt="auth.displayName" />
              <AvatarFallback>{{ auth.initials }}</AvatarFallback>
            </Avatar>
            <div class="flex-1 min-w-0 hidden sm:block">
              <p class="text-sm font-medium truncate">{{ auth.displayName }}</p>
              <p class="text-xs text-muted-foreground truncate">
                <Badge v-if="auth.isContributor" variant="accent" class="text-[10px] px-1.5 py-0">贡献者</Badge>
                <span v-else>已登录</span>
              </p>
            </div>
            <ChevronDown class="h-3.5 w-3.5 text-muted-foreground hidden sm:block" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent class="w-56">
          <!-- 用户信息 -->
          <DropdownMenuLabel>
            <p class="font-medium text-foreground">{{ auth.displayName }}</p>
            <p class="font-normal text-[11px]">{{ auth.isContributor ? '贡献者' : '已登录' }}</p>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <!-- 昵称输入 -->
          <div class="px-2 py-1.5">
            <label class="text-[10px] text-muted-foreground font-mono uppercase tracking-wider">昵称</label>
            <input
              v-model="nickname"
              class="mt-1 flex h-7 w-full rounded-sm border border-input bg-background px-2 text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="游客"
              @change="saveNickname"
            />
          </div>
          <DropdownMenuSeparator />
          <DropdownMenuItem @click="handleAction('apikeys')">
            <Key class="h-4 w-4" />
            <span>API Keys</span>
          </DropdownMenuItem>
          <DropdownMenuItem @click="handleAction('settings')">
            <Settings class="h-4 w-4" />
            <span>设置</span>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem class="text-destructive focus:bg-destructive/10 focus:text-destructive" @click="handleLogout">
            <LogOut class="h-4 w-4" />
            <span>退出登录</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ChevronDown, Settings, Key, Github, LogOut, Menu } from "lucide-vue-next";
import { useAuthStore } from "@/stores/auth";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";

const STORAGE_KEY = "mma:nickname";
const router = useRouter();
const auth = useAuthStore();

const stored = (() => { try { return localStorage.getItem(STORAGE_KEY) || ""; } catch { return ""; } })();
const nickname = ref(stored);

function saveNickname() {
  try { localStorage.setItem(STORAGE_KEY, nickname.value.trim()); } catch { /* ignore */ }
}

function handleAction(action: string) {
  if (action === "login") router.push("/login");
  else if (action === "settings") router.push("/settings");
  else if (action === "apikeys") router.push("/apikeys");
}

function handleLogout() {
  auth.logout();
  router.push("/");
}
</script>
