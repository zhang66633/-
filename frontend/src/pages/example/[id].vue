<template>
  <div class="h-full overflow-y-auto bg-grid-paper">
    <main class="mx-auto max-w-3xl px-6 sm:px-10 py-12 sm:py-16">
      <!-- Breadcrumb:等宽小字,细线分隔 -->
      <nav class="flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-muted-foreground mb-10">
        <router-link to="/" class="hover:text-foreground transition-colors">§1 首页</router-link>
        <ChevronRight class="h-3 w-3" />
        <router-link to="/example/0" class="hover:text-foreground transition-colors">§5 例题</router-link>
        <ChevronRight class="h-3 w-3" />
        <span class="text-foreground truncate normal-case">{{ example.title || '加载中...' }}</span>
      </nav>

      <!-- Loading:骨架 -->
      <div v-if="loading" class="space-y-4 animate-pulse">
        <div class="h-8 bg-muted rounded w-3/4" />
        <div class="h-4 bg-muted rounded w-1/2" />
        <div class="h-40 bg-muted rounded" />
      </div>

      <template v-else>
        <!-- 标题区:§5 + 衬线大标题 + 等宽元数据(无彩色 badge) -->
        <div class="mb-12">
          <p class="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground mb-4">§5 &nbsp; 例题</p>
          <h1 class="font-display text-3xl sm:text-4xl font-medium tracking-tight leading-[1.1]">{{ example.title }}</h1>
          <div class="mt-4 flex flex-wrap items-center gap-x-5 gap-y-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
            <span>{{ example.category }}</span>
            <span class="text-muted-foreground/40">·</span>
            <span>{{ example.difficulty }}</span>
            <span v-if="example.competition" class="text-muted-foreground/40">·</span>
            <span v-if="example.competition">{{ example.competition }}</span>
          </div>
        </div>

        <!-- 问题描述 -->
        <section class="mb-12">
          <div class="section-rule mb-5"><span class="font-mono text-xs tracking-wider">·1 &nbsp; 问题描述</span></div>
          <div class="prose prose-sm dark:prose-invert max-w-none rounded-md border border-border bg-background p-6 leading-relaxed">
            {{ example.description }}
          </div>
        </section>

        <!-- 问题分析 -->
        <section v-if="example.analysis" class="mb-12">
          <div class="section-rule mb-5"><span class="font-mono text-xs tracking-wider">·2 &nbsp; 问题分析</span></div>
          <div class="prose prose-sm dark:prose-invert max-w-none rounded-md border border-border bg-background p-6" v-html="renderedAnalysis" />
        </section>

        <!-- 模型建立 -->
        <section v-if="example.model" class="mb-12">
          <div class="section-rule mb-5"><span class="font-mono text-xs tracking-wider">·3 &nbsp; 模型建立</span></div>
          <div class="prose prose-sm dark:prose-invert max-w-none rounded-md border border-border bg-background p-6" v-html="renderedModel" />
        </section>

        <!-- 求解过程 -->
        <section v-if="example.solution" class="mb-12">
          <div class="section-rule mb-5"><span class="font-mono text-xs tracking-wider">·4 &nbsp; 求解过程</span></div>
          <div class="rounded-md border border-border bg-background overflow-hidden">
            <div class="prose prose-sm dark:prose-invert max-w-none p-6" v-html="renderedSolution" />
            <!-- 代码块 -->
            <div v-if="example.code" class="border-t border-border bg-muted/30 p-4">
              <div class="flex items-center justify-between mb-2">
                <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Python 实现</span>
                <button class="flex items-center gap-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors" @click="copyCode">
                  <Copy class="h-3 w-3" />复制
                </button>
              </div>
              <pre class="text-xs font-mono overflow-x-auto leading-relaxed"><code>{{ example.code }}</code></pre>
            </div>
          </div>
        </section>

        <!-- 结果分析 -->
        <section v-if="example.results" class="mb-12">
          <div class="section-rule mb-5"><span class="font-mono text-xs tracking-wider">·5 &nbsp; 结果分析</span></div>
          <div class="prose prose-sm dark:prose-invert max-w-none rounded-md border border-border bg-background p-6" v-html="renderedResults" />
        </section>

        <!-- 行动:深近黑按钮 -->
        <div class="flex items-center justify-center py-8 border-t border-border">
          <button :class="BTN_PRIMARY" @click="tryExample">
            <Play class="h-3.5 w-3.5" />
            尝试此例题
          </button>
        </div>

        <!-- 相关例题:细线列表 -->
        <section v-if="relatedExamples.length > 0" class="border-t border-border pt-8">
          <div class="section-rule mb-5"><span class="font-mono text-xs tracking-wider">·6 &nbsp; 相关例题</span></div>
          <ul class="divide-y divide-border">
            <li
              v-for="rel in relatedExamples"
              :key="rel.id"
              class="group flex items-start gap-4 py-3 cursor-pointer"
              @click="router.push(`/example/${rel.id}`)"
            >
              <span class="font-mono text-[10px] text-muted-foreground/70 w-10 shrink-0 pt-0.5">·6.{{ rel.id }}</span>
              <div class="flex-1 min-w-0">
                <span class="font-display text-sm font-medium group-hover:text-primary transition-colors block">{{ rel.title }}</span>
                <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/70 mt-0.5 block">{{ rel.category }}</span>
              </div>
              <ChevronRight class="h-4 w-4 text-muted-foreground/40 group-hover:text-primary group-hover:translate-x-1 transition-all shrink-0 mt-1" />
            </li>
          </ul>
        </section>
      </template>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ChevronRight, Copy, Play } from "lucide-vue-next";
import { BTN_PRIMARY } from "@/config/styles";
import { renderMarkdown } from "@/utils/markdown";

const props = defineProps<{
  id: string;
}>();

const router = useRouter();
const loading = ref(true);

interface ExampleData {
  title: string;
  category: string;
  difficulty: string;
  competition: string;
  description: string;
  analysis?: string;
  model?: string;
  solution?: string;
  code?: string;
  results?: string;
}

const example = ref<ExampleData>({
  title: "",
  category: "",
  difficulty: "中等",
  competition: "",
  description: "",
});

const relatedExamples = ref<Array<{ id: number; title: string; category: string }>>([]);

const difficultyClass = computed(() => "");

const renderedAnalysis = computed(() =>
  renderMarkdown(example.value.analysis || "")
);
const renderedModel = computed(() =>
  renderMarkdown(example.value.model || "")
);
const renderedSolution = computed(() =>
  renderMarkdown(example.value.solution || "")
);
const renderedResults = computed(() =>
  renderMarkdown(example.value.results || "")
);

function copyCode() {
  if (example.value.code) {
    navigator.clipboard.writeText(example.value.code);
  }
}

function tryExample() {
  router.push({
    path: "/chat",
    query: {
      problem: `${example.value.title}\n\n${example.value.description}`,
      mode: "execute",
    },
  });
}

// Demo data - in production, fetch from API
const demos: Record<string, ExampleData> = {
  "1": {
    title: "配送中心选址优化",
    category: "优化问题",
    difficulty: "中等",
    competition: "2023 国赛 B 题",
    description:
      "某物流公司计划在 5 个备选地点中选择 2 个建立配送中心，为 10 个需求点提供服务。\n\n已知各备选地点到各需求点的运输距离和单位运输成本，以及各需求点的日需求量。目标是最小化总运输成本。",
    analysis:
      "这是一个典型的**设施选址问题**（Facility Location Problem），可建模为混合整数线性规划（MILP）。\n\n**决策变量**：\n- $x_{ij}$：从配送中心 $i$ 到需求点 $j$ 的运输量\n- $y_i$：是否在备选点 $i$ 建立配送中心（二元变量）\n\n**约束条件**：\n- 每个需求点的需求必须被满足\n- 配送中心容量限制\n- 只能选择 2 个配送中心",
    model:
      "## 数学模型\n\n**目标函数**：\n$$\\min Z = \\sum_{i=1}^{5}\\sum_{j=1}^{10} c_{ij} \\cdot d_{ij} \\cdot x_{ij}$$\n\n其中 $c_{ij}$ 为单位运输成本，$d_{ij}$ 为运输距离。\n\n**约束条件**：\n$$\\sum_{i=1}^{5} x_{ij} = D_j, \\quad \\forall j$$\n$$\\sum_{j=1}^{10} x_{ij} \\leq C_i \\cdot y_i, \\quad \\forall i$$\n$$\\sum_{i=1}^{5} y_i = 2$$\n$$x_{ij} \\geq 0, \\quad y_i \\in \\{0, 1\\}$$",
    solution:
      "采用分支定界法求解该 MILP 问题。由于决策变量中包含二元变量 $y_i$，需在满足整数约束的子空间中搜索最优解。\n\n**求解步骤**：\n1. 松弛整数约束,求线性规划松弛解\n2. 若松弛解满足整数条件,即为最优;否则分支\n3. 对每个分支继续求解,剪去bound劣于当前最优的子树\n\n**复杂度**：最坏情况指数级,但实际中分支定界通常能快速收敛。",
    code: 'from pulp import *\n\n# 定义问题\nprob = LpProblem("Facility_Location", LpMinimize)\n\n# 决策变量\nx = LpVariable.dicts("x", [(i,j) for i in range(5) for j in range(10)], lowBound=0)\ny = LpVariable.dicts("y", range(5), cat="Binary")\n\n# 目标函数\nprob += lpSum([cost[i][j] * dist[i][j] * x[i,j] for i in range(5) for j in range(10)])\n\n# 需求约束\nfor j in range(10):\n    prob += lpSum([x[i,j] for i in range(5)]) == demand[j]\n\n# 容量约束\nfor i in range(5):\n    prob += lpSum([x[i,j] for j in range(10)]) <= capacity[i] * y[i]\n\n# 数量约束\nprob += lpSum([y[i] for i in range(5)]) == 2\n\n# 求解\nprob.solve()',
    results:
      "求解结果显示，选择备选地点 2 和 4 建立配送中心，总运输成本为 125,430 元/天。\n\n**灵敏度分析**：\n- 需求波动 ±20% 的情况下，最优选址不变\n- 运输成本上升 10% 时，总成本按比例增加，但不影响选址决策",
  },
};

onMounted(async () => {
  loading.value = true;
  if (demos[props.id]) {
    example.value = demos[props.id];
    relatedExamples.value = [
      { id: 2, title: "城市交通流量预测", category: "预测问题" },
      { id: 3, title: "水资源质量评价", category: "评价问题" },
    ];
  } else {
    example.value = {
      title: `例题 ${props.id}`,
      category: "综合问题",
      difficulty: "中等",
      competition: "",
      description: "该例题正在建设中，敬请期待...",
    };
  }
  loading.value = false;
});
</script>
