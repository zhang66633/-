<template>
  <div class="bg-grid-paper h-full overflow-y-auto">
    <!-- Access denied banner -->
    <div v-if="deniedMessage" class="mx-auto max-w-4xl px-6 sm:px-10 pt-4">
      <div class="flex items-start gap-3 rounded-md border border-amber-200 bg-amber-50 px-4 py-3">
        <ShieldAlert class="h-5 w-5 shrink-0 text-amber-600 mt-0.5" />
        <p class="text-sm text-amber-800 flex-1">{{ deniedMessage }}</p>
        <button class="shrink-0 text-amber-500 hover:text-amber-700 transition-colors" @click="dismissDenied">
          <X class="h-4 w-4" />
        </button>
      </div>
    </div>

    <!-- API Key 快速配置区域 -->
    <div class="mx-auto max-w-4xl px-6 sm:px-10 pt-4">
      <div v-if="myKey.has_key" class="flex items-center gap-3 rounded-md border border-green-200 bg-green-50 px-4 py-2.5">
        <CheckCircle2 class="h-5 w-5 shrink-0 text-green-600" />
        <span class="text-sm text-green-800 font-medium">API Key 已激活</span>
        <span class="text-xs text-green-700 font-mono">{{ myKey.key?.masked_key }}</span>
        <span class="text-xs text-green-600">· {{ myKey.key?.provider }} · {{ myKey.key?.model_name }}</span>
        <button class="ml-auto text-xs text-green-600 hover:text-green-800 underline shrink-0" @click="showKeyInput = !showKeyInput">
          {{ showKeyInput ? '取消' : '更换' }}
        </button>
      </div>

      <div v-if="!myKey.has_key || showKeyInput" class="rounded-md border border-border bg-card p-4">
        <div class="flex items-center gap-3 flex-wrap">
          <Key class="h-5 w-5 shrink-0 text-muted-foreground" />
          <input
            v-model="keyInput"
            type="password"
            placeholder="粘贴你的 API Key，例如 sk-..."
            class="flex-1 min-w-[260px] h-10 rounded-md border border-input bg-background px-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            @keydown.enter="activateKey"
          />
          <button
            class="inline-flex items-center gap-1.5 rounded-md bg-foreground px-5 py-2.5 text-sm font-medium text-background hover:bg-foreground/90 transition-colors disabled:opacity-50 shrink-0"
            :disabled="!keyInput.trim() || activating"
            @click="activateKey"
          >
            <Loader2 v-if="activating" class="h-4 w-4 animate-spin" />
            <Zap v-else class="h-4 w-4" />
            {{ myKey.has_key ? '更新并激活' : '激活 Key' }}
          </button>
        </div>
        <p class="mt-2 text-xs text-muted-foreground">
          支持 DeepSeek、OpenAI、Anthropic 等 OpenAI 兼容 API。
          从 <a href="https://platform.deepseek.com" target="_blank" class="underline">platform.deepseek.com</a> 获取 Key，Key 仅保存在本地服务器。
        </p>
        <p v-if="activateError" class="mt-1 text-xs text-red-600">{{ activateError }}</p>
      </div>
    </div>

    <div class="mx-auto max-w-4xl px-6 sm:px-10">

      <!-- 标题区 -->
      <header class="pt-20 pb-16 sm:pt-28 sm:pb-20">
        <p class="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground mb-6">
          ·0 &nbsp; 工作台
        </p>
        <h1 class="font-display text-5xl sm:text-6xl font-medium tracking-tight leading-[1.05]">
          数学建模
        </h1>
        <p class="font-display italic text-2xl sm:text-3xl text-muted-foreground mt-3 leading-[1.2] pb-1">
          智能体团队，陪你从入门到竞赛
        </p>
        <p class="mt-8 text-base text-muted-foreground max-w-xl leading-relaxed">
          论文写作与学习训练双线并行。建模师教方法、求解器写代码、编辑改论文——智能体团队分工协作。
        </p>
      </header>

      <!-- ·1 论文工作台 -->
      <section class="pb-16">
        <div class="section-rule mb-8">
          <span class="font-mono text-xs tracking-wider">·1 &nbsp; 论文工作台</span>
          <span class="font-mono text-[10px] text-muted-foreground/60 ml-3">从问题到论文，一站式输出</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <button
            v-for="mod in paperModules"
            :key="mod.path"
            class="group flex flex-col items-start gap-2 rounded-lg border border-border bg-card p-5 text-left transition-all hover:border-primary/30 hover:shadow-sm"
            @click="router.push(mod.path)"
          >
            <component :is="mod.icon" class="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            <span class="font-display text-base font-medium">{{ mod.label }}</span>
            <span class="text-xs text-muted-foreground leading-relaxed">{{ mod.desc }}</span>
          </button>
        </div>
      </section>

      <!-- ·2 学习中心 -->
      <section class="pb-20">
        <div class="section-rule mb-8">
          <span class="font-mono text-xs tracking-wider">·2 &nbsp; 学习中心</span>
          <span class="font-mono text-[10px] text-muted-foreground/60 ml-3">建模手 · 编程手 · 论文手</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            v-for="mod in learnModules"
            :key="mod.path"
            class="group flex flex-col items-start gap-2 rounded-lg border border-border bg-card p-5 text-left transition-all hover:border-primary/30 hover:shadow-sm"
            @click="router.push(mod.path)"
          >
            <component :is="mod.icon" class="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            <span class="font-display text-base font-medium">{{ mod.label }}</span>
            <span class="text-xs text-muted-foreground leading-relaxed">{{ mod.desc }}</span>
          </button>
        </div>
      </section>

      <!-- ·3 知识库 -->
      <section v-if="statsReady" class="pb-20">
        <div class="section-rule mb-10">
          <span class="font-mono text-xs tracking-wider">·3 &nbsp; 知识库</span>
        </div>
        <div class="grid grid-cols-3 gap-8">
          <div v-for="s in statItems" :key="s.key">
            <p class="font-mono text-4xl sm:text-5xl font-medium tabular-nums leading-none">{{ s.value }}</p>
            <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mt-3">{{ s.label }}</p>
          </div>
        </div>
      </section>

      <!-- 脚注 -->
      <footer class="border-t border-border py-10 mb-8">
        <p class="font-mono text-xs text-muted-foreground/80 leading-relaxed max-w-2xl">
          <span class="text-primary">†</span> &nbsp;
          当前为本地游客模式,对话与任务保存在本机。如需云端同步或多端协作,可在右上角设置中配置。
        </p>
      </footer>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import {
  ArrowRight, ShieldAlert, X, Key, Zap, Loader2, CheckCircle2,
  MessageSquare, FileText, Library, BookOpen, Dumbbell, MessageCircleQuestion, TrendingUp,
} from "lucide-vue-next";
import { getKBStats } from "@/apis/knowledgeApi";
import { getApiKeys } from "@/apis/apiKeyApi";
import { BTN_PRIMARY } from "@/config/styles";
import request from "@/utils/request";

const router = useRouter();
const route = useRoute();

const deniedMessage = ref("");
watch(() => route.query.denied, (val) => {
  if (val === "knowledge") deniedMessage.value = "知识库仅对项目贡献者开放。请联系 zhang66633 或 shu639 获取权限。";
}, { immediate: true });
function dismissDenied() { deniedMessage.value = ""; router.replace({ query: {} }); }

const myKey = ref<{ has_key: boolean; key: { masked_key: string; provider: string; model_name: string } | null }>({ has_key: false, key: null });
const keyInput = ref("");
const activating = ref(false);
const activateError = ref("");
const showKeyInput = ref(false);

async function checkMyKey() {
  try {
    const r: any = await request.get("/apikeys/mine");
    myKey.value = r.data || r;
    showKeyInput.value = !myKey.value.has_key;
  } catch {
    myKey.value = { has_key: false, key: null };
    showKeyInput.value = true;
  }
}

async function activateKey() {
  if (!keyInput.value.trim() || activating.value) return;
  activating.value = true;
  activateError.value = "";
  try {
    await request.post("/apikeys/quick", { key: keyInput.value.trim() });
    keyInput.value = "";
    await checkMyKey();
  } catch (e: any) {
    activateError.value = e?.response?.data?.detail || e?.message || "激活失败，请检查 Key 是否正确";
  } finally {
    activating.value = false;
  }
}

const statsReady = ref(false);

const paperModules = [
  { label: "对话", desc: "与智能体自由对话，实时推进建模讨论", path: "/chat", icon: MessageSquare },
  { label: "方案", desc: "结构化输出完整建模方案与论文", path: "/solution", icon: FileText },
  { label: "知识库", desc: "方法卡片、真题论文与模板套路", path: "/knowledge", icon: Library },
];

const learnModules = [
  { label: "学习工位", desc: "技能树导航，智能体对话式教学", path: "/learn", icon: BookOpen },
  { label: "训练场", desc: "每日推荐练习，智能体出题批改", path: "/practice", icon: Dumbbell },
  { label: "答疑室", desc: "随时 @智能体 提问，联网推荐资源", path: "/qa", icon: MessageCircleQuestion },
  { label: "成长档案", desc: "学习日历、成就系统与进度追踪", path: "/progress", icon: TrendingUp },
];

const statItems = ref([
  { key: "methods", label: "方法卡片", value: 0 },
  { key: "papers", label: "真题论文", value: 0 },
  { key: "templates", label: "模板套路", value: 0 },
]);

onMounted(async () => {
  try {
    const res = await getKBStats();
    const data = res.data;
    statItems.value = [
      { key: "methods", label: "方法卡片", value: data.methods_count },
      { key: "papers", label: "真题论文", value: data.papers_count },
      { key: "templates", label: "模板套路", value: data.templates_count },
    ];
    statsReady.value = true;
  } catch {
    statsReady.value = false;
  }
  await checkMyKey();
});
</script>
