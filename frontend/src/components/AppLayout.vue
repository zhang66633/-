<template>
  <div class="flex h-screen w-full overflow-hidden bg-background">
    <SkipToContent />
    <!-- 侧栏:桌面固定 -->
    <AppSidebar class="hidden lg:flex" />

    <!-- 主区域 -->
    <div class="flex flex-1 flex-col min-w-0">
      <!-- 顶栏 -->
      <header
        class="flex h-14 shrink-0 items-center justify-between border-b px-4 sm:px-6"
      >
        <!-- 左:移动端汉堡+品牌 / 桌面端当前章节定位 -->
        <div class="flex items-center gap-3 min-w-0">
          <Sheet v-model:open="mobileNavOpen">
            <SheetTrigger as-child>
              <button
                class="inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground hover:bg-accent lg:hidden"
                aria-label="打开导航"
              >
                <Menu class="h-4 w-4" />
              </button>
            </SheetTrigger>
            <SheetContent side="left" class="w-64 p-0">
              <AppSidebar class="w-full border-r-0" />
            </SheetContent>
          </Sheet>
          <!-- 移动端:品牌名(桌面端由侧栏显示,不重复) -->
          <span class="font-display text-sm font-medium tracking-tight lg:hidden">
            {{ APP_NAME }}
          </span>
          <!-- 桌面端:当前章节定位,呼应学术手稿编号系统 -->
          <span class="hidden lg:flex items-baseline gap-2 min-w-0">
            <span class="font-mono text-xs text-primary shrink-0">{{ currentSection.num }}</span>
            <span class="font-display text-sm text-foreground/80 truncate">{{ currentSection.label }}</span>
          </span>
        </div>

        <!-- 右:服务状态 + 主题切换 + 用户 -->
        <div class="flex items-center gap-2 shrink-0">
          <ServiceStatus class="hidden sm:flex" />
          <div class="h-4 w-px bg-border mx-1 hidden sm:block" />
          <ThemeToggle />
          <NavUser />
        </div>
      </header>

      <!-- 内容区 -->
      <main id="main-content" class="flex-1 overflow-hidden">
        <SessionStorageAlert />
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import AppSidebar from "@/components/AppSidebar.vue";
import NavUser from "@/components/NavUser.vue";
import ServiceStatus from "@/components/ServiceStatus.vue";
import SkipToContent from "@/components/SkipToContent.vue";
import ThemeToggle from "@/components/ThemeToggle.vue";
import SessionStorageAlert from "@/components/chat/SessionStorageAlert.vue";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { APP_NAME } from "@/types/const";
import { Menu } from "lucide-vue-next";
import { computed, ref } from "vue";
import { useRoute } from "vue-router";

const mobileNavOpen = ref(false);
const route = useRoute();

const currentSection = computed(() => {
  const p = route.path;
  if (p.startsWith("/chat")) return { num: "§2", label: "对话" };
  if (p.startsWith("/solution")) return { num: "§2", label: "方案" };
  if (p.startsWith("/learn")) return { num: "§3", label: "学习中心" };
  if (p.startsWith("/practice")) return { num: "§3", label: "训练场" };
  if (p.startsWith("/qa")) return { num: "§3", label: "答疑室" };
  if (p.startsWith("/progress")) return { num: "§3", label: "成长档案" };
  if (p.startsWith("/task")) return { num: "§4", label: "任务" };
  if (p.startsWith("/knowledge")) return { num: "§4", label: "知识库" };
  return { num: "§1", label: "首页" };
});
</script>
