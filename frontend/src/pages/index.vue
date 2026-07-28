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
      <!-- 已配置状态 -->
      <div v-if="myKey.has_key" class="flex items-center gap-3 rounded-md border border-green-200 bg-green-50 px-4 py-2.5">
        <CheckCircle2 class="h-5 w-5 shrink-0 text-green-600" />
        <span class="text-sm text-green-800 font-medium">API Key 已激活</span>
        <span class="text-xs text-green-700 font-mono">{{ myKey.key?.masked_key }}</span>
        <span class="text-xs text-green-600">· {{ myKey.key?.provider }} · {{ myKey.key?.model_name }}</span>
        <button class="ml-auto text-xs text-green-600 hover:text-green-800 underline shrink-0" @click="showKeyInput = !showKeyInput">
          {{ showKeyInput ? '取消' : '更换' }}
        </button>
      </div>

      <!-- 未配置 / 更换 Key 输入区 -->
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

      <!-- 标题区:大留白,衬线大标题 + italic 副标题,左对齐 -->
      <header class="pt-20 pb-24 sm:pt-28 sm:pb-32">
        <p class="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground mb-6">
          ·0 &nbsp; 工作台
        </p>
        <h1 class="font-display text-5xl sm:text-6xl font-medium tracking-tight leading-[1.05]">
          数学建模
        </h1>
        <p class="font-display italic text-2xl sm:text-3xl text-muted-foreground mt-3 leading-[1.2] pb-1">
          一份正在演算的手册
        </p>
        <p class="mt-8 text-base text-muted-foreground max-w-xl leading-relaxed">
          选择模式进入对话。教学模式以引导提问培养建模思维,方案模式结构化输出完整解题流程。
          所有推理与代码可追溯,像翻阅一份带批注的研究笔记。
        </p>
      </header>

      <!-- ·1 模式:章节列表式,左描述 + 右公式装饰 -->
      <section class="pb-24">
        <div class="section-rule mb-12">
          <span class="font-mono text-xs tracking-wider">·1 &nbsp; 开始</span>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-5 gap-12 lg:gap-16">
          <!-- 教学模式:占 3 -->
          <article class="lg:col-span-3">
            <div class="flex items-baseline gap-3 mb-3">
              <span class="font-mono text-xs text-primary">·1.1</span>
              <h2 class="font-display text-2xl font-medium">教学模式</h2>
            </div>
            <p class="text-sm text-muted-foreground leading-relaxed max-w-md mb-5">
              苏格拉底式引导提问,逐步建立建模思维。适合日常训练与备赛学习,留下完整推理痕迹。
            </p>
            <p class="font-mono text-xs text-muted-foreground mb-6">
              <span class="text-foreground/60">示例问题:</span>
              如何在总运输成本最小化时满足各节点需求?
            </p>
            <button
              :class="BTN_PRIMARY"
              @click="enterChat('teach')"
            >
              开始学习
              <ArrowRight class="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </button>
          </article>

          <!-- 公式装饰块:占 2,像论文里的公式 -->
          <aside class="lg:col-span-2 lg:border-l lg:border-border lg:pl-8">
            <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mb-3">
              典型形式
            </p>
            <pre class="font-mono text-xs leading-relaxed text-muted-foreground whitespace-pre-wrap">min  Z = Σᵢ Σⱼ cᵢⱼ · xᵢⱼ

s.t.  Σᵢ xᵢⱼ = Dⱼ,  ∀j ∈ J
       xᵢⱼ ∈ {0, 1}</pre>
            <p class="font-mono text-[10px] text-muted-foreground/70 mt-3">
              [mc_008] 运输问题 · 整数规划
            </p>
          </aside>
        </div>

        <!-- 方案模式:第二行,反向(左公式右描述)打破对称 -->
        <div class="grid grid-cols-1 lg:grid-cols-5 gap-12 lg:gap-16 mt-16">
          <aside class="lg:col-span-2 lg:order-1 lg:border-r lg:border-border lg:pr-8">
            <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mb-3">
              输出结构
            </p>
            <pre class="font-mono text-xs leading-relaxed text-muted-foreground whitespace-pre-wrap">1. 问题重述与假设
2. 模型建立
3. 求解与代码
4. 结果分析
5. 论文撰写</pre>
          </aside>
          <article class="lg:col-span-3 lg:order-2">
            <div class="flex items-baseline gap-3 mb-3">
              <span class="font-mono text-xs text-primary">·1.2</span>
              <h2 class="font-display text-2xl font-medium">方案模式</h2>
            </div>
            <p class="text-sm text-muted-foreground leading-relaxed max-w-md mb-5">
              结构化输出完整建模方案,含代码执行、结果验证与论文。适合限时竞赛与正式提交。
            </p>
            <button
              :class="BTN_PRIMARY"
              @click="enterChat('execute')"
            >
              开始建模
              <ArrowRight class="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </button>
          </article>
        </div>
      </section>

      <!-- ·2 模块:紧凑列表式,divide-y,非图标卡片 -->
      <section class="pb-24">
        <div class="section-rule mb-8">
          <span class="font-mono text-xs tracking-wider">·2 &nbsp; 模块</span>
        </div>
        <ul class="divide-y divide-border">
          <li v-for="mod in modules" :key="mod.path">
            <button
              class="group flex w-full items-center gap-6 py-4 text-left transition-colors"
              @click="router.push(mod.path)"
            >
              <span class="font-mono text-xs text-muted-foreground w-8 shrink-0">{{ mod.num }}</span>
              <span class="font-display text-lg font-medium w-28 shrink-0 transition-colors group-hover:text-primary">
                {{ mod.label }}
              </span>
              <span class="text-sm text-muted-foreground flex-1 truncate">{{ mod.desc }}</span>
              <ArrowRight class="h-4 w-4 text-muted-foreground/50 transition-all group-hover:text-primary group-hover:translate-x-1 shrink-0" />
            </button>
          </li>
        </ul>
      </section>

      <!-- §3 知识库:等宽大数字横向,无框 -->
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

      <!-- 脚注:游客提示,像论文脚注 -->
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
import { ArrowRight, ShieldAlert, X, Key, Zap, Loader2, CheckCircle2 } from "lucide-vue-next";
import { getKBStats, type KBStats } from "@/apis/knowledgeApi";
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

const dismissedApiKey = ref(false);

const statsReady = ref(false);

const modules = [
  { num: "§2", label: "对话", desc: "与智能体交互,实时推进建模", path: "/chat" },
  { num: "§3", label: "教学", desc: "苏格拉底式引导,逐步培养建模思维", path: "/teach" },
  { num: "§4", label: "方案", desc: "结构化输出完整建模方案", path: "/solution" },
  { num: "§5", label: "知识库", desc: "方法卡片、真题与模板套路", path: "/knowledge" },
];

const statItems = ref([
  { key: "methods", label: "方法卡片", value: 0 },
  { key: "papers", label: "真题论文", value: 0 },
  { key: "templates", label: "模板套路", value: 0 },
]);

function enterChat(mode: "teach" | "execute") {
  router.push(mode === "teach" ? "/teach" : "/solution");
}

onMounted(async () => {
  // 知识库统计
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

  // API Key 检查
  await checkMyKey();
});
</script>
