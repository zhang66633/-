<template>
  <div class="flex h-full flex-col overflow-hidden">
    <header class="flex items-center justify-between border-b px-6 py-4 shrink-0">
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="icon" :class="SCALE_PRESS_ONLY" @click="router.back()">
          <ArrowLeft class="h-4 w-4" />
        </Button>
        <div>
          <h1 class="text-lg font-semibold">API Keys</h1>
          <p class="text-xs text-muted-foreground">管理用于调用大模型的 API 凭证</p>
        </div>
      </div>
      <Button :class="SCALE_PRESS_ONLY" @click="showAdd = true">
        <Plus class="h-4 w-4 mr-1" />
        添加 Key
      </Button>
    </header>

    <div class="flex-1 overflow-y-auto overflow-x-hidden p-6">
      <div v-if="loading" class="flex items-center justify-center py-12 text-sm text-muted-foreground">
        <Loader2 class="h-4 w-4 mr-2 animate-spin" /> 加载中...
      </div>

      <div v-else-if="keys.length === 0" class="rounded-lg border border-dashed p-12 text-center">
        <Key class="h-10 w-10 mx-auto text-muted-foreground/50" />
        <p class="mt-4 text-sm text-muted-foreground">还没有 API Key</p>
        <p class="mt-1 text-xs text-muted-foreground">添加后可以在对话/任务中使用对应模型</p>
      </div>

      <div v-else class="grid gap-3 max-w-3xl">
        <div
          v-for="k in keys"
          :key="k.id"
          class="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/30 transition-colors"
        >
          <div class="flex items-center gap-3 min-w-0">
            <div class="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 shrink-0">
              <Key class="h-4 w-4 text-primary" />
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <p class="font-medium truncate">{{ k.name }}</p>
                <span v-if="k.purpose === 'embedding'" class="text-[10px] font-mono uppercase bg-purple-500/15 text-purple-600 px-1.5 py-0.5 rounded">向量</span>
                <span v-if="k.is_default && k.purpose !== 'embedding'" class="text-[10px] font-mono uppercase bg-primary/10 text-primary px-1.5 py-0.5 rounded">默认</span>
              </div>
              <p class="text-xs text-muted-foreground font-mono">{{ k.masked_key }} · {{ k.provider }} · {{ k.model_name }}</p>
              <p v-if="k.base_url" class="text-[11px] text-muted-foreground/60 font-mono truncate">{{ k.base_url }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <Button v-if="!k.is_default && k.purpose !== 'embedding'" variant="outline" size="sm" :class="SCALE_PRESS_ONLY" @click="handleSetDefault(k.id)">
              <Check class="h-3 w-3 mr-1" />
              设为默认
            </Button>
            <Button variant="ghost" size="icon" :class="['text-destructive hover:text-destructive', SCALE_PRESS_ONLY].join(' ')" @click="handleDelete(k.id)">
              <Trash2 class="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showAdd" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showAdd = false">
      <div class="w-full max-w-md rounded-lg border bg-background p-6 shadow-xl">
        <h2 class="text-lg font-semibold mb-4">添加 API Key</h2>
        <div class="space-y-3">
          <div>
            <label class="text-sm font-medium">名称</label>
            <Input v-model="form.name" placeholder="例如: 我的 DeepSeek" class="mt-1" />
          </div>
          <div>
            <label class="text-sm font-medium">用途</label>
            <div class="mt-1 flex gap-2">
              <button
                v-for="p in PURPOSES" :key="p.value"
                class="flex-1 rounded-md border px-3 py-1.5 text-xs transition-colors"
                :class="form.purpose === p.value ? 'border-primary bg-primary/5 text-foreground' : 'border-border text-muted-foreground hover:text-foreground'"
                @click="onPurposeChange(p.value)"
              >{{ p.label }}</button>
            </div>
            <p v-if="form.purpose === 'embedding'" class="mt-1 text-[11px] text-muted-foreground">用于知识库向量检索（语义搜索）。仅对话可不配。</p>
          </div>
          <div>
            <label class="text-sm font-medium">服务商</label>
            <select v-model="form.provider" class="mt-1 w-full h-9 rounded-md border border-input bg-background px-3 text-sm" @change="onProviderChange">
              <option v-for="p in PROVIDERS" :key="p.value" :value="p.value">{{ p.label }}</option>
            </select>
          </div>
          <div>
            <label class="text-sm font-medium">模型名称</label>
            <Input v-model="form.model_name" placeholder="deepseek-chat" class="mt-1" />
          </div>
          <div>
            <label class="text-sm font-medium">Base URL <span class="text-muted-foreground font-normal">（留空按服务商预设）</span></label>
            <Input v-model="form.base_url" :placeholder="presetBaseUrl || 'https://api.deepseek.com'" class="mt-1" />
          </div>
          <div>
            <label class="text-sm font-medium">Key</label>
            <Input v-model="form.key" type="password" placeholder="sk-..." class="mt-1" />
          </div>
        </div>
        <div class="mt-5 flex justify-end gap-2">
          <p v-if="addError" class="text-xs text-red-600 mr-auto self-center">{{ addError }}</p>
          <Button variant="ghost" :class="SCALE_PRESS_ONLY" @click="showAdd = false; addError = ''">取消</Button>
          <Button :disabled="!form.name || !form.key || !form.model_name || saving" :class="SCALE_PRESS_ONLY" @click="handleAdd">
            <Loader2 v-if="saving" class="h-4 w-4 mr-1 animate-spin" />
            {{ saving ? '验证中...' : '保存' }}
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  type ApiKeyItem,
  addApiKey,
  deleteApiKey,
  getApiKeys,
  setDefaultApiKey,
} from "@/apis/apiKeyApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SCALE_PRESS, SCALE_PRESS_ONLY } from "@/config/styles";
import { ArrowLeft, Check, Key, Loader2, Plus, Trash2 } from "lucide-vue-next";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const keys = ref<ApiKeyItem[]>([]);
const loading = ref(false);
const saving = ref(false);
const showAdd = ref(false);
const addError = ref("");

const PROVIDERS = [
  {
    value: "deepseek",
    label: "DeepSeek",
    base_url: "https://api.deepseek.com",
    chat_model: "deepseek-chat",
  },
  {
    value: "qwen",
    label: "通义千问 (Qwen)",
    base_url: "https://dashscope.aliyuncs.com/compatible-mode",
    chat_model: "qwen-plus",
  },
  {
    value: "glm",
    label: "智谱 (GLM)",
    base_url: "https://open.bigmodel.cn/api/paas",
    chat_model: "glm-4-flash",
  },
  {
    value: "siliconflow",
    label: "SiliconFlow",
    base_url: "https://api.siliconflow.cn",
    chat_model: "deepseek-ai/DeepSeek-V3",
  },
  {
    value: "openai",
    label: "OpenAI",
    base_url: "https://api.openai.com",
    chat_model: "gpt-4o-mini",
  },
  {
    value: "anthropic",
    label: "Anthropic (Claude)",
    base_url: "https://api.anthropic.com",
    chat_model: "claude-sonnet-4-6",
  },
  { value: "custom", label: "自定义...", base_url: "", chat_model: "" },
];
const PURPOSES = [
  { value: "chat" as const, label: "对话" },
  { value: "embedding" as const, label: "向量（知识库）" },
];
const DEFAULT_EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5";

const form = ref({
  name: "",
  provider: "deepseek",
  model_name: "deepseek-chat",
  key: "",
  base_url: "",
  purpose: "chat" as "chat" | "embedding",
});

const presetBaseUrl = computed(
  () => PROVIDERS.find((p) => p.value === form.value.provider)?.base_url ?? "",
);

function onProviderChange() {
  const preset = PROVIDERS.find((p) => p.value === form.value.provider);
  if (!preset) return;
  if (preset.value !== "custom") {
    form.value.base_url = preset.base_url;
    if (form.value.purpose === "chat")
      form.value.model_name = preset.chat_model;
  } else {
    form.value.base_url = "";
    form.value.model_name = "";
  }
}

function onPurposeChange(purpose: "chat" | "embedding") {
  form.value.purpose = purpose;
  const preset = PROVIDERS.find((p) => p.value === form.value.provider);
  form.value.model_name =
    purpose === "embedding"
      ? DEFAULT_EMBEDDING_MODEL
      : (preset?.chat_model ?? "");
}

function resetForm() {
  form.value = {
    name: "",
    provider: "deepseek",
    model_name: "deepseek-chat",
    key: "",
    base_url: "",
    purpose: "chat",
  };
}

async function load() {
  loading.value = true;
  try {
    const r = await getApiKeys();
    keys.value = r.data ?? [];
  } catch (e) {
    console.error(e);
    keys.value = [];
  } finally {
    loading.value = false;
  }
}

async function handleAdd() {
  saving.value = true;
  addError.value = "";
  try {
    await addApiKey({
      ...form.value,
      base_url: form.value.base_url || presetBaseUrl.value,
    });
    showAdd.value = false;
    addError.value = "";
    resetForm();
    await load();
  } catch (e) {
    const err = e as {
      response?: { data?: { detail?: string } };
      message?: string;
    };
    const detail = err?.response?.data?.detail || err?.message || "保存失败";
    addError.value = detail;
  } finally {
    saving.value = false;
  }
}

async function handleDelete(id: string) {
  try {
    await deleteApiKey(id);
    await load();
  } catch (e) {
    console.error(e);
  }
}

async function handleSetDefault(id: string) {
  try {
    await setDefaultApiKey(id);
    await load();
  } catch (e) {
    console.error(e);
  }
}

onMounted(load);
</script>