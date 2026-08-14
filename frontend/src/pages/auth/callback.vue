<template>
  <div class="flex min-h-screen items-center justify-center bg-background px-6">
    <div class="w-full max-w-sm text-center">
      <Loader2 v-if="loading" class="mx-auto h-8 w-8 animate-spin text-muted-foreground" />
      <div v-else-if="error">
        <div class="flex h-16 w-16 mx-auto items-center justify-center rounded-2xl bg-destructive/10 mb-4">
          <XCircle class="h-8 w-8 text-destructive" />
        </div>
        <h1 class="text-xl font-semibold mb-2">登录失败</h1>
        <p class="text-sm text-muted-foreground mb-6">{{ error }}</p>
        <router-link
          to="/login"
          class="inline-flex items-center gap-2 rounded-md bg-foreground px-5 py-2.5 text-sm font-medium text-background"
        >
          重新登录
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { Loader2, XCircle } from "lucide-vue-next";
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const loading = ref(true);
const error = ref("");

onMounted(async () => {
  const code = route.query.code as string;
  const state = route.query.state as string;
  const err = route.query.error as string;

  if (err) {
    error.value = `GitHub 授权被拒绝: ${err}`;
    loading.value = false;
    return;
  }

  if (!code || !state) {
    error.value = "缺少授权参数，请重新登录";
    loading.value = false;
    return;
  }

  const ok = await auth.handleCallback(code, state);
  if (ok) {
    router.replace("/");
  } else {
    error.value = "GitHub 授权失败，请重试";
    loading.value = false;
  }
});
</script>
