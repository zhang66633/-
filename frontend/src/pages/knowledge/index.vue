<!-- Knowledge page v2 — public access -->
<template>
  <div class="h-full overflow-y-auto overflow-x-hidden bg-grid-paper">
    <div class="mx-auto max-w-4xl px-6 sm:px-10 py-12 sm:py-16 overflow-x-hidden">
      <p class="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground mb-4">§4 &nbsp; 知识库</p>
      <h1 class="font-display text-3xl sm:text-4xl font-medium tracking-tight">方法卡片、真题与模板</h1>
      <p class="mt-2 text-sm text-muted-foreground">检索已有知识,管理条目,或从原始文本导入新内容。</p>

      <!-- login / contributor status -->
      <div v-if="!auth.isLoggedIn" class="mt-4 rounded-md border border-amber-200 bg-amber-50 px-4 py-2.5 flex items-center gap-3">
        <span class="text-sm text-amber-800">⚠ 未登录 — 无法上传或管理知识。请先登录 GitHub 账号。</span>
        <router-link to="/login" class="ml-auto text-sm text-amber-700 underline shrink-0">去登录</router-link>
      </div>
      <div v-else-if="!auth.isContributor" class="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-2.5 flex items-center gap-3">
        <span class="text-sm text-red-700">当前登录: <strong>{{ auth.user?.login }}</strong> — 不在贡献者列表中。</span>
        <button class="ml-auto text-sm text-red-700 underline shrink-0" @click="auth.logout(); $router.go(0)">退出重登</button>
      </div>
      <div v-else class="mt-4 rounded-md border border-green-200 bg-green-50 px-4 py-2.5 flex items-center gap-3">
        <span class="text-sm text-green-700">✓ 已认证为贡献者: <strong>{{ auth.user?.login }}</strong></span>
      </div>

        <!-- Tabs:章节式等宽标签 + 下划线高亮,无胶囊背景 -->
        <div class="flex items-center gap-6 border-b mt-8 mb-8">
          <button v-for="(tab, i) in tabs" :key="tab.value"
            class="relative flex items-center gap-2 py-3 text-sm transition-colors"
            :class="activeTab === tab.value ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'"
            @click="activeTab = tab.value">
            <span class="font-mono text-[10px] text-muted-foreground/70">·4.{{ i + 1 }}</span>
            <span :class="activeTab === tab.value ? 'font-display font-medium' : ''">{{ tab.label }}</span>
            <span v-if="activeTab === tab.value" class="absolute left-0 right-0 -bottom-px h-px bg-primary"></span>
          </button>
        </div>

        <!-- ==================== TAB 1: 检索知识 ==================== -->
        <div v-if="activeTab === 'search'">
          <div class="flex gap-2 mb-5">
            <div class="relative flex-1">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input v-model="searchQuery" type="text" placeholder="搜索方法、论文或模板..."
                class="w-full rounded-md border border-border bg-background pl-10 pr-4 py-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                @keyup.enter="doSearch" />
            </div>
            <button class="inline-flex items-center rounded-md bg-foreground px-5 py-2.5 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-50 transition-transform hover:scale-[0.98] active:scale-[0.97]"
              :disabled="!searchQuery.trim() || searchLoading" @click="doSearch">
              <Loader2 v-if="searchLoading" class="h-4 w-4 animate-spin" /><span v-else>搜索</span>
            </button>
          </div>
          <!-- 筛选:等宽小标签,非胶囊 -->
          <div class="flex flex-wrap items-center gap-x-5 gap-y-2 mb-6">
            <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">类型</span>
            <button v-for="o in typeOpts" :key="o.value"
              class="font-mono text-[10px] uppercase tracking-wider transition-colors"
              :class="searchFilter === o.value ? 'text-primary' : 'text-muted-foreground/60 hover:text-foreground'"
              @click="searchFilter = o.value">{{ o.label }}</button>
            <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground ml-2">问题</span>
            <button v-for="o in probOpts" :key="o.value"
              class="font-mono text-[10px] uppercase tracking-wider transition-colors"
              :class="searchProblem === o.value ? 'text-primary' : 'text-muted-foreground/60 hover:text-foreground'"
              @click="searchProblem = o.value">{{ o.label }}</button>
          </div>

          <div v-if="searchLoading" class="space-y-3"><div v-for="i in 3" :key="i" class="rounded-md border border-border p-5"><Skeleton class="h-4 w-2/3" /><Skeleton class="h-3 w-full mt-2" /></div></div>
          <div v-else-if="!isBrowsing && searchResults.length === 0" class="text-center py-16 text-muted-foreground text-sm">未找到匹配结果</div>
          <div v-else-if="isBrowsing && visibleResults.length === 0" class="text-center py-16 text-muted-foreground text-sm">知识库暂无条目,切换到「导入知识」添加</div>
          <div v-else class="space-y-3">
            <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{{ isBrowsing ? "全部条目" : "找到" }} {{ visibleResults.length }} 条</p>
            <div v-for="r in visibleResults" :key="r.id" class="cursor-pointer rounded-md border border-border bg-background p-4 hover:border-primary/40 transition-colors" @click="openDetail(r)">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">[{{ typeLabel(r.type) }}]</span>
                  <span v-if="r.score != null" class="font-mono text-[10px] text-muted-foreground/70">相关度 {{ ((r.score||0)*100).toFixed(0) }}%</span>
                </div>
                <ChevronRight class="h-4 w-4 text-muted-foreground/40" />
              </div>
              <h3 class="font-display text-sm font-medium mt-2">{{ r.name || r.title }}</h3>
              <p class="text-xs text-muted-foreground mt-1 line-clamp-3 leading-relaxed">{{ r.snippet }}</p>
            </div>
          </div>
        </div>

        <!-- ==================== TAB 2: 管理知识 ==================== -->
        <div v-if="activeTab === 'manage'">
          <div class="flex items-center gap-x-5 gap-y-2 mb-5 flex-wrap">
            <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">类型</span>
            <button v-for="o in mgrTypes" :key="o.value"
              class="font-mono text-[10px] uppercase tracking-wider transition-colors"
              :class="mgrType === o.value ? 'text-primary' : 'text-muted-foreground/60 hover:text-foreground'"
              @click="mgrType = o.value">{{ o.label }}</button>
            <span class="flex-1" />
            <button class="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs hover:bg-accent transition-colors" @click="loadMgrList"><RefreshCw class="h-3 w-3" />刷新</button>
          </div>

          <div v-if="mgrLoading" class="space-y-3"><div v-for="i in 5" :key="i" class="rounded-md border border-border p-4"><Skeleton class="h-4 w-3/4" /></div></div>
          <div v-else-if="mgrEntries.length === 0" class="text-center py-12 border border-dashed border-border rounded-md text-muted-foreground text-sm">暂无条目,切换到「导入知识」添加</div>
          <div v-else class="divide-y divide-border border border-border rounded-md">
            <div v-for="e in mgrEntries" :key="e.id" class="flex items-center gap-3 bg-background px-4 py-3 hover:bg-accent/30 group transition-colors">
              <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground shrink-0">[{{ mgrTypeLabel }}]</span>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium truncate">{{ e.name || e.title }}</p>
                <p class="font-mono text-[10px] text-muted-foreground/70 mt-0.5">{{ mgrSub(e) }}</p>
              </div>
              <div class="flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <button class="rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground" title="编辑" @click="openEdit(e)"><Pencil class="h-3.5 w-3.5" /></button>
                <button class="rounded-md p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive" title="删除" @click="confirmDel(e)"><Trash2 class="h-3.5 w-3.5" /></button>
              </div>
            </div>
          </div>
          <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/70 text-center pt-3">共 {{ mgrEntries.length }} 条</p>
          <div class="mt-8 pt-6 border-t text-center">
            <button class="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground/50 hover:text-muted-foreground mx-auto transition-colors" :disabled="reindexing" @click="doReindex">
              <RefreshCw v-if="reindexing" class="h-3 w-3 animate-spin" /><Database v-else class="h-3 w-3" />{{ reindexing ? '重建中' : '重建向量索引' }}
            </button>
          </div>
        </div>

        <!-- ==================== TAB 3: 导入知识 ==================== -->
        <div v-if="activeTab === 'import'">
          <div class="rounded-lg border border-border bg-background p-6">
            <!-- 导入引导提示：手稿边注风格 -->
            <div class="border-l-2 border-foreground/50 pl-4 mb-6">
              <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5">
                § 导入说明 · {{ impTypeLabel }}
              </p>
              <p class="text-xs leading-relaxed text-foreground/75">
                <template v-if="impType === 'problem'">上传竞赛真题原文。系统会提取年份、赛事、题号，作为后续论文关联的唯一标识。建议<strong class="font-medium text-foreground">先导入题目</strong>，再导入对应论文。</template>
                <template v-else-if="impType === 'paper'">
                  <template v-if="lastProblemRef">上传后将<strong class="font-medium text-foreground">自动关联到 {{ lastProblemRef }}</strong>，无需额外操作。</template>
                  <template v-else>先导入题目，再从此处追加论文，系统会自动关联。或直接上传，系统根据<strong class="font-medium text-foreground">年份+赛事+题号</strong>自动匹配。</template>
                </template>
                <template v-else-if="impType === 'method'">上传数学建模方法的描述文本。系统会提取原理、适用条件、代码示例等信息。</template>
                <template v-else>上传分析框架描述。系统会提取引导问题、决策树和检查清单。</template>
              </p>
            </div>
            <div class="flex items-center gap-x-5 gap-y-2 mb-5 flex-wrap">
              <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">类型</span>
              <button v-for="o in impTypes" :key="o.value"
                class="font-mono text-[10px] uppercase tracking-wider transition-colors"
                :class="impType === o.value ? 'text-primary' : 'text-muted-foreground/60 hover:text-foreground'"
                @click="impType = o.value">{{ o.label }}</button>
            </div>

            <!-- File drop zone -->
            <div class="relative rounded-md border border-dashed border-border p-6 text-center cursor-pointer transition-colors"
              :class="dragOver ? 'border-primary bg-primary/5' : impFile ? 'border-primary/50 bg-primary/5' : 'hover:border-muted-foreground/50'"
              @click="triggerFileInput" @dragover.prevent="dragOver = true" @dragleave.prevent="dragOver = false" @drop.prevent="onDrop">
              <input ref="fileRef" type="file" multiple accept=".txt,.md,.pdf,.doc,.docx,.tex,.xlsx,.xls,.csv,.png,.jpg,.jpeg,.gif,.webp,.bmp" class="hidden" @change="onFileSel" />
              <template v-if="impFiles.length > 0">
                <div class="space-y-1.5 text-left w-full">
                  <div v-for="(f, i) in impFiles" :key="i" class="flex items-center gap-2 text-sm rounded-md bg-muted/30 px-3 py-1.5">
                    <FileText class="h-4 w-4 shrink-0 text-primary" />
                    <span class="font-medium truncate flex-1 min-w-0">{{ f.name }}</span>
                    <span class="font-mono text-[10px] text-muted-foreground shrink-0">{{ fmtSize(f.size) }}</span>
                    <button class="rounded-md p-0.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive shrink-0" @click.stop="removeFile(i)"><X class="h-3 w-3" /></button>
                  </div>
                </div>
                <p class="font-mono text-[10px] text-muted-foreground/70 mt-2">{{ impFiles.length }} 个文件，可在下方补充文本后一起提取</p>
              </template>
              <template v-else>
                <FileUp class="h-8 w-8 mx-auto text-muted-foreground/40 mb-2" />
                <p class="text-sm text-muted-foreground">拖拽文件到此处，或<span class="text-primary">点击选择</span>（支持多选）</p>
                <p class="font-mono text-[10px] text-muted-foreground/60 mt-1">Excel / CSV / PDF / DOCX / TXT / 图片 / GIF</p>
              </template>
            </div>

            <label class="block font-mono text-[10px] uppercase tracking-wider text-muted-foreground mb-2 mt-5">{{ impFiles.length > 0 ? '补充文本(可选)' : '粘贴原始文本' }}</label>
            <textarea v-model="impText" rows="8" :placeholder="impPlaceholder"
              class="w-full resize-y rounded-md border border-border bg-background px-4 py-3 text-sm leading-relaxed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" />
            <div class="flex items-center gap-2 mt-3 flex-wrap">
              <input v-model="impName" type="text" placeholder="名称(可选)" class="flex-1 min-w-0 rounded-md border border-border bg-background px-3 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" />
              <button class="flex items-center whitespace-nowrap rounded-md bg-foreground px-5 py-2.5 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-50 transition-transform hover:scale-[0.98] active:scale-[0.97]"
                :disabled="(!impText.trim() && impFiles.length === 0) || extracting" @click="doExtract">
                <Loader2 v-if="extracting" class="h-4 w-4 mr-1.5 animate-spin" /><Sparkles v-else class="h-4 w-4 mr-1.5" />{{ extracting ? '提取中' : 'LLM 提取并预览' }}
              </button>
            </div>
            <div v-if="extractError" class="mt-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{{ extractError }}</div>
            <div v-if="extractPreview" class="mt-4">
              <p class="font-mono text-[10px] uppercase tracking-wider text-primary mb-2">提取完成</p>
              <pre class="rounded-md bg-zinc-950 p-4 font-mono text-xs text-zinc-300 overflow-auto max-h-96">{{ extractPreview }}</pre>
              <div class="flex gap-2 mt-3">
                <button class="flex items-center rounded-md bg-foreground px-5 py-2 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-50 transition-transform hover:scale-[0.98] active:scale-[0.97]"
                  :disabled="saving" @click="doSaveExtract"><Check v-if="!saving" class="h-4 w-4 mr-1" /><Loader2 v-else class="h-4 w-4 mr-1 animate-spin" />{{ saving ? '保存中' : '保存到知识库' }}</button>
                <button class="flex items-center rounded-md border border-border px-4 py-2 text-sm hover:bg-accent transition-colors" @click="extractPreview = ''; extractError = ''"><RotateCcw class="h-4 w-4 mr-1" />重新提取</button>
              </div>
            </div>

            <!-- 论文上传区: 始终可见 -->
            <div class="mt-8 pt-6 border-t-2 border-border">
              <p class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mb-1">§ 论文上传</p>
              <p class="font-display text-lg font-medium mb-1">上传对应论文</p>
              <p v-if="lastProblemRef" class="text-xs text-muted-foreground mb-5">关联到题目 <span class="font-mono text-primary">{{ lastProblemRef }}</span></p>
              <p v-else class="text-xs text-muted-foreground mb-5">先导入题目后论文将自动关联，也可独立上传</p>

              <!-- Paper file drop zone -->
              <div class="relative rounded-md border border-dashed border-border p-5 text-center cursor-pointer transition-colors"
                :class="paperDragOver ? 'border-primary bg-primary/5' : paperFiles.length > 0 ? 'border-primary/50 bg-primary/5' : 'hover:border-muted-foreground/50'"
                @click="paperTriggerFile" @dragover.prevent="paperDragOver = true" @dragleave.prevent="paperDragOver = false" @drop.prevent="paperOnDrop">
                <input ref="paperFileRef" type="file" multiple accept=".txt,.md,.pdf,.doc,.docx,.tex" class="hidden" @change="paperOnFileSel" />
                <template v-if="paperFiles.length > 0">
                  <div class="space-y-1 text-left w-full">
                    <div v-for="(f, i) in paperFiles" :key="i" class="flex items-center gap-2 text-sm rounded-md bg-muted/30 px-3 py-1.5">
                      <FileText class="h-4 w-4 shrink-0 text-primary" />
                      <span class="font-medium truncate flex-1 min-w-0">{{ f.name }}</span>
                      <span class="font-mono text-[10px] text-muted-foreground shrink-0">{{ fmtSize(f.size) }}</span>
                      <button class="rounded-md p-0.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive shrink-0" @click.stop="paperRemoveFile(i)"><X class="h-3 w-3" /></button>
                    </div>
                  </div>
                  <p class="font-mono text-[10px] text-muted-foreground/70 mt-2">{{ paperFiles.length }} 个文件</p>
                </template>
                <template v-else>
                  <FileUp class="h-7 w-7 mx-auto text-muted-foreground/40 mb-1.5" />
                  <p class="text-sm text-muted-foreground">拖拽论文文件，或<span class="text-primary">点击选择</span></p>
                  <p class="font-mono text-[10px] text-muted-foreground/60 mt-1">PDF / DOCX / TXT / MD / TEX</p>
                </template>
              </div>

              <label class="block font-mono text-[10px] uppercase tracking-wider text-muted-foreground mb-2 mt-4">补充文本(可选)</label>
              <textarea v-model="paperText" rows="4" placeholder="粘贴论文描述..."
                class="w-full resize-y rounded-md border border-border bg-background px-4 py-3 text-sm leading-relaxed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" />
              <div class="flex items-center gap-2 mt-3 flex-wrap">
                <input v-model="paperName" type="text" placeholder="论文名称(可选)" class="flex-1 min-w-0 rounded-md border border-border bg-background px-3 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" />
                <button class="flex items-center whitespace-nowrap rounded-md bg-foreground px-5 py-2.5 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-50 transition-transform hover:scale-[0.98] active:scale-[0.97]"
                  :disabled="(!paperText.trim() && paperFiles.length === 0) || paperExtracting" @click="paperDoExtract">
                  <Loader2 v-if="paperExtracting" class="h-4 w-4 mr-1.5 animate-spin" /><Sparkles v-else class="h-4 w-4 mr-1.5" />{{ paperExtracting ? '提取中' : 'LLM 提取并预览' }}
                </button>
              </div>
              <div v-if="paperError" class="mt-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{{ paperError }}</div>
              <div v-if="paperPreview" class="mt-4">
                <p class="font-mono text-[10px] uppercase tracking-wider text-primary mb-2">提取完成</p>
                <pre class="rounded-md bg-zinc-950 p-4 font-mono text-xs text-zinc-300 overflow-auto max-h-96">{{ paperPreview }}</pre>
                <div class="flex gap-2 mt-3">
                  <button class="flex items-center rounded-md bg-foreground px-5 py-2 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-50 transition-transform hover:scale-[0.98] active:scale-[0.97]"
                    :disabled="paperSaving" @click="paperDoSave"><Check v-if="!paperSaving" class="h-4 w-4 mr-1" /><Loader2 v-else class="h-4 w-4 mr-1 animate-spin" />{{ paperSaving ? '保存中' : '保存到知识库' }}</button>
                  <button class="flex items-center rounded-md border border-border px-4 py-2 text-sm hover:bg-accent transition-colors" @click="paperPreview = ''; paperError = ''"><RotateCcw class="h-4 w-4 mr-1" />重新提取</button>
                </div>
              </div>

              <button v-if="lastProblemRef" class="mt-4 flex items-center gap-1 font-mono text-[10px] text-muted-foreground/50 hover:text-muted-foreground transition-colors" @click="lastProblemRef = ''">清除关联</button>
            </div>
          </div>
        </div>
      </div>

    <!-- Detail Dialog -->
    <Dialog :open="!!detailItem" @update:open="detailItem = null">
      <DialogContent class="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle class="font-display">{{ detailItem?.name || detailItem?.title }}</DialogTitle>
          <div v-if="detailRawText" class="flex items-center gap-1 rounded-md bg-muted p-0.5 w-fit mt-2">
            <button class="rounded-sm px-3 py-1 text-xs font-medium transition-all"
              :class="detailViewMode === 'structured' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'"
              @click="detailViewMode = 'structured'">结构化分析</button>
            <button class="rounded-sm px-3 py-1 text-xs font-medium transition-all"
              :class="detailViewMode === 'raw' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'"
              @click="detailViewMode = 'raw'">原始资料</button>
          </div>
        </DialogHeader>
        <!-- Raw view -->
        <pre v-if="detailViewMode === 'raw' && detailRawText" class="text-xs leading-relaxed whitespace-pre-wrap max-h-[60vh] overflow-y-auto rounded-md border bg-muted/30 p-4">{{ detailRawText }}</pre>
        <div v-if="detailViewMode === 'raw' && !detailRawText" class="text-sm text-muted-foreground py-4">该条目没有原始资料（可能不是通过导入创建的）</div>
        <!-- Structured view -->
        <div v-if="detailLoading && detailViewMode === 'structured'" class="space-y-3"><Skeleton class="h-4 w-full" /><Skeleton class="h-4 w-5/6" /></div>
        <div v-else-if="detailData && detailViewMode === 'structured'" class="text-sm space-y-4 py-2">
          <template v-if="detailData.type === 'method_card'">
            <p class="leading-relaxed">{{ (detailData.data as any).principle }}</p>
            <div><h4 class="font-display font-medium text-sm mb-1">适用条件</h4><ul class="list-disc list-inside text-muted-foreground text-sm"><li v-for="c in (detailData.data as any).applicable_when" :key="c">{{ c }}</li></ul></div>
          </template>
          <template v-if="detailData.type === 'paper'">
            <div class="flex items-center gap-3 flex-wrap mb-3">
              <span class="font-mono text-[10px] uppercase tracking-wider border border-border rounded-sm px-2 py-0.5">{{ (detailData.data as any).competition }} {{ (detailData.data as any).year }}·{{ (detailData.data as any).problem_id }}题</span>
              <span class="text-xs text-amber-500">{{ '★'.repeat((detailData.data as any).quality_rating || 3) }}</span>
              <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{{ (detailData.data as any).difficulty_level }}</span>
              <span v-if="(detailData.data as any).problem_ref" class="font-mono text-[10px] uppercase tracking-wider text-emerald-600 cursor-pointer hover:underline" @click="openProblemFromPaper((detailData.data as any).problem_ref)">🔗 {{ (detailData.data as any).problem_ref }}</span>
              <span v-else class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/50">⚠ 未关联题目</span>
            </div>
            <!-- 问题背景 -->
            <div v-if="(detailData.data as any).problem_context" class="rounded-md border border-border p-4 bg-muted/20">
              <h4 class="font-display font-medium text-sm mb-2">问题背景</h4>
              <p class="text-sm leading-relaxed text-muted-foreground">{{ (detailData.data as any).problem_context }}</p>
            </div>
            <!-- 方法链路 -->
            <div v-if="(detailData.data as any).methodology_chain?.length" class="rounded-md border border-border p-4">
              <h4 class="font-display font-medium text-sm mb-2">建模方法链路</h4>
              <div class="space-y-1.5">
                <div v-for="(step, i) in (detailData.data as any).methodology_chain" :key="i" class="flex items-start gap-2 text-sm">
                  <span class="font-mono text-[10px] text-muted-foreground shrink-0 mt-1">{{ i + 1 }}.</span>
                  <span>{{ step }}</span>
                </div>
              </div>
            </div>
            <!-- 核心公式 -->
            <div v-if="(detailData.data as any).key_formulas?.length" class="rounded-md border border-border p-4">
              <h4 class="font-display font-medium text-sm mb-2">核心公式</h4>
              <div class="space-y-2">
                <div v-for="f in (detailData.data as any).key_formulas" :key="f.name" class="rounded-sm bg-muted/30 p-3">
                  <p class="font-mono text-xs mb-1">{{ f.name }}</p>
                  <p class="font-serif text-sm mb-1 italic">{{ f.latex }}</p>
                  <p class="text-xs text-muted-foreground">{{ f.description }}</p>
                </div>
              </div>
            </div>
            <!-- 算法概要 -->
            <div v-if="(detailData.data as any).algorithm_outline?.length" class="rounded-md border border-border p-4">
              <h4 class="font-display font-medium text-sm mb-2">算法概要</h4>
              <div v-for="(a, i) in (detailData.data as any).algorithm_outline" :key="i" class="mb-3 last:mb-0">
                <p class="text-xs text-muted-foreground mb-1">{{ a.description }}</p>
                <pre class="rounded-sm bg-zinc-950 p-3 text-xs text-zinc-300 overflow-x-auto"><code>{{ a.code }}</code></pre>
              </div>
            </div>
            <!-- 假设分析 -->
            <div v-if="(detailData.data as any).assumption_analysis?.length" class="rounded-md border border-border p-4">
              <h4 class="font-display font-medium text-sm mb-2">假设分析</h4>
              <ul class="space-y-1.5"><li v-for="a in (detailData.data as any).assumption_analysis" :key="a" class="text-sm text-muted-foreground flex items-start gap-2"><span class="text-primary shrink-0">→</span>{{ a }}</li></ul>
            </div>
            <!-- 可复用模式 -->
            <div v-if="(detailData.data as any).reusable_patterns?.length" class="rounded-md border border-emerald-200 bg-emerald-50/30 p-4">
              <h4 class="font-display font-medium text-sm mb-2 text-emerald-800">可复用的建模模式</h4>
              <ul class="space-y-1.5"><li v-for="p in (detailData.data as any).reusable_patterns" :key="p" class="text-sm text-emerald-700 flex items-start gap-2"><span class="text-emerald-500 shrink-0">✦</span>{{ p }}</li></ul>
            </div>
            <!-- 常见陷阱 -->
            <div v-if="(detailData.data as any).common_pitfalls?.length" class="rounded-md border border-amber-200 bg-amber-50/30 p-4">
              <h4 class="font-display font-medium text-sm mb-2 text-amber-800">常见陷阱</h4>
              <div class="space-y-2"><div v-for="p in (detailData.data as any).common_pitfalls" :key="p.mistake" class="text-sm"><p class="text-amber-700">⚠ {{ p.mistake }}</p><p class="text-muted-foreground text-xs mt-0.5">→ {{ p.solution }}</p></div></div>
            </div>
            <!-- 评价 -->
            <div class="border-t border-border pt-3 mt-2">
              <p class="text-sm font-medium">可学之处</p>
              <p class="text-sm text-muted-foreground leading-relaxed mt-1">{{ (detailData.data as any).evaluation?.lessons }}</p>
            </div>
          </template>
          <template v-if="detailData.type === 'template'">
            <div v-for="s in (detailData.data as any).steps" :key="s.step" class="border-l-2 border-border pl-3 py-1">
              <h5 class="font-display font-medium text-sm">§{{ s.step }} {{ s.name }}</h5>
              <ul class="list-disc list-inside text-xs text-muted-foreground mt-1"><li v-for="c in s.checklist" :key="c">{{ c }}</li></ul>
            </div>
          </template>
          <template v-if="detailData.type === 'problem'">
            <div class="flex items-center gap-3 flex-wrap mb-3">
              <span class="font-mono text-[10px] uppercase tracking-wider border border-border rounded-sm px-2 py-0.5">{{ (detailData.data as any).competition }} {{ (detailData.data as any).year }}·{{ (detailData.data as any).problem_id }}题</span>
              <span class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{{ (detailData.data as any).tags?.difficulty || 'medium' }}</span>
              <span class="text-xs text-muted-foreground" v-if="(detailData.data as any).linked_papers?.length">{{ (detailData.data as any).linked_papers.length }}篇关联论文</span>
            </div>
            <div v-if="(detailData.data as any).background" class="rounded-md border border-border p-4 bg-muted/20">
              <h4 class="font-display font-medium text-sm mb-2">问题背景</h4>
              <p class="text-sm leading-relaxed text-muted-foreground">{{ (detailData.data as any).background }}</p>
            </div>
            <div v-if="(detailData.data as any).objectives?.length" class="rounded-md border border-border p-4">
              <h4 class="font-display font-medium text-sm mb-2">求解目标</h4>
              <ul class="space-y-1"><li v-for="o in (detailData.data as any).objectives" :key="o" class="text-sm text-muted-foreground flex items-start gap-2"><span class="text-primary shrink-0">→</span>{{ o }}</li></ul>
            </div>
            <div v-if="(detailData.data as any).data_description" class="rounded-md border border-border p-4">
              <h4 class="font-display font-medium text-sm mb-2">数据说明</h4>
              <p class="text-sm text-muted-foreground leading-relaxed">{{ (detailData.data as any).data_description }}</p>
            </div>
            <div v-if="(detailData.data as any).full_text" class="rounded-md border border-border p-4">
              <h4 class="font-display font-medium text-sm mb-2">完整题目</h4>
              <p class="text-sm leading-relaxed whitespace-pre-wrap text-muted-foreground">{{ (detailData.data as any).full_text }}</p>
            </div>
          </template>
        </div>
        <DialogFooter><DialogClose class="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent transition-colors">关闭</DialogClose></DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Edit Dialog — 全字段表单 -->
    <Dialog :open="editOpen" @update:open="editOpen = $event">
      <DialogContent class="max-w-3xl max-h-[88vh] overflow-y-auto">
        <DialogHeader><DialogTitle class="font-display">编辑{{ mgrTypeLabel }}</DialogTitle></DialogHeader>
        <div v-if="editLoading" class="flex items-center justify-center py-16"><Loader2 class="h-5 w-5 animate-spin text-muted-foreground" /></div>
        <div v-else class="space-y-4 text-sm py-2">

          <!-- ===== 方法卡片 ===== -->
          <template v-if="mgrType === 'method'">
            <p class="font-mono text-[10px] text-muted-foreground/70">ID: {{ editForm.card_id }}</p>
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">名称</label><Input v-model="editForm.name" class="mt-1" /></div>
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">核心原理</label><Textarea v-model="editForm.principle" rows="5" class="mt-1" /></div>
            <ArrayEditor v-model="editForm.category" label="分类" placeholder="优化 / 预测 / 统计..." />
            <ArrayEditor v-model="editForm.applicable_when" label="适用条件" />
            <ArrayEditor v-model="editForm.typical_scenarios" label="典型场景" />
            <ArrayEditor v-model="editForm.not_applicable_when" label="不适用情况" />
            <ArrayEditor v-model="editForm.common_mistakes" label="常见错误与对策" :fields="[{key:'mistake',label:'错误'},{key:'solution',label:'对策'}]" empty-value="{mistake:'',solution:''}" />
            <ArrayEditor v-model="editForm.code_snippets" label="代码示例" :fields="[{key:'language',label:'语言'},{key:'description',label:'说明'},{key:'code',label:'代码',type:'textarea'}]" empty-value="{language:'',description:'',code:''}" />
            <ArrayEditor v-model="editForm.formulas" label="核心公式" :fields="[{key:'name',label:'名称'},{key:'latex',label:'LaTeX'},{key:'description',label:'说明'}]" empty-value="{name:'',latex:'',description:''}" />
            <ArrayEditor v-model="editForm.related_cards" label="关联方法ID" />
          </template>

          <!-- ===== 论文 ===== -->
          <template v-if="mgrType === 'paper'">
            <p class="font-mono text-[10px] text-muted-foreground/70">ID: {{ editForm.paper_id }}</p>
            <div class="grid grid-cols-3 gap-2">
              <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">年份</label><Input v-model.number="editForm.year" type="number" class="mt-1" /></div>
              <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">竞赛</label><Input v-model="editForm.competition" class="mt-1" /></div>
              <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">题号</label><Input v-model="editForm.problem_id" class="mt-1" /></div>
            </div>
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">标题</label><Input v-model="editForm.title" class="mt-1" /></div>
            <div class="grid grid-cols-2 gap-2">
              <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">评分 1-5</label><Input v-model.number="editForm.quality_rating" type="number" min="1" max="5" class="mt-1" /></div>
              <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">关联题目</label><Input v-model="editForm.problem_ref" class="mt-1" /></div>
            </div>
            <ArrayEditor v-model="editForm.tags_problem_type" label="问题类型" />
            <ArrayEditor v-model="editForm.tags_core_models" label="核心方法" />
            <h4 class="font-display text-xs uppercase tracking-wider text-muted-foreground pt-1">分析</h4>
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">问题摘要</label><Textarea v-model="editForm.analysis_problem_summary" rows="4" class="mt-1" /></div>
            <ArrayEditor v-model="editForm.analysis_key_assumptions" label="关键假设" />
            <ArrayEditor v-model="editForm.analysis_decision_variables" label="决策变量" />
            <div class="grid grid-cols-2 gap-2">
              <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">目标函数</label><Textarea v-model="editForm.analysis_objective" rows="2" class="mt-1" /></div>
              <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">约束条件</label><Textarea v-model="editForm.analysis_constraints" rows="2" class="mt-1" /></div>
            </div>
            <h4 class="font-display text-xs uppercase tracking-wider text-muted-foreground pt-1">模型</h4>
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">建模思路</label><Textarea v-model="editForm.model_approach" rows="4" class="mt-1" /></div>
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">创新点</label><Input v-model="editForm.model_innovation" class="mt-1" /></div>
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">求解方法</label><Input v-model="editForm.model_solution_method" class="mt-1" /></div>
            <h4 class="font-display text-xs uppercase tracking-wider text-muted-foreground pt-1">评价</h4>
            <ArrayEditor v-model="editForm.evaluation_strengths" label="优点" />
            <ArrayEditor v-model="editForm.evaluation_weaknesses" label="缺点" />
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">可学之处</label><Textarea v-model="editForm.evaluation_lessons" rows="3" class="mt-1" /></div>
            <ArrayEditor v-model="editForm.methodology_chain" label="方法链路" />
          </template>

          <!-- ===== 模板 ===== -->
          <template v-if="mgrType === 'template'">
            <p class="font-mono text-[10px] text-muted-foreground/70">ID: {{ editForm.template_id }}</p>
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">名称</label><Input v-model="editForm.name" class="mt-1" /></div>
            <ArrayEditor v-model="editForm.applicable_to" label="适用类型" />
            <ArrayEditor v-model="editForm.steps" label="引导步骤" :fields="[{key:'name',label:'步骤名'},{key:'guiding_questions',label:'引导问题',type:'textarea'},{key:'decision_tree',label:'决策分支',type:'textarea'},{key:'checklist',label:'检查清单',type:'textarea'}]" empty-value="{name:'',guiding_questions:'',decision_tree:'',checklist:''}" />
          </template>

          <!-- ===== 赛题 ===== -->
          <template v-if="mgrType === 'problem'">
            <p class="font-mono text-[10px] text-muted-foreground/70">ID: {{ editForm.problem_id }}</p>
            <div class="grid grid-cols-3 gap-2">
              <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">年份</label><Input v-model.number="editForm.year" type="number" class="mt-1" /></div>
              <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">竞赛</label><Input v-model="editForm.competition" class="mt-1" /></div>
              <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">题号</label><Input v-model="editForm.problem_id" class="mt-1" /></div>
            </div>
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">标题</label><Input v-model="editForm.title" class="mt-1" /></div>
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">问题背景</label><Textarea v-model="editForm.background" rows="4" class="mt-1" /></div>
            <ArrayEditor v-model="editForm.objectives" label="求解目标" />
            <ArrayEditor v-model="editForm.tags_problem_type" label="题型标签" />
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">数据描述</label><Input v-model="editForm.data_description" class="mt-1" /></div>
            <div><label class="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">原文全文</label><Textarea v-model="editForm.full_text" rows="6" class="mt-1" /></div>
            <ArrayEditor v-model="editForm.deliverables" label="提交物" />
          </template>
        </div>
        <DialogFooter>
          <button class="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent transition-colors" @click="editOpen = false">取消</button>
          <button class="rounded-md bg-foreground px-4 py-2 text-sm text-background hover:bg-foreground/90 disabled:opacity-50 transition-transform hover:scale-[0.98] active:scale-[0.97]" :disabled="editSaving" @click="doEditSave">
            <Loader2 v-if="editSaving" class="h-4 w-4 mr-1 animate-spin" />{{ editSaving ? '保存中' : '保存' }}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Delete Confirm -->
    <Dialog :open="delOpen" @update:open="delOpen = $event">
      <DialogContent class="max-w-sm">
        <DialogHeader><DialogTitle class="font-display">确认删除</DialogTitle><DialogDescription>确定删除 "{{ delTarget?.name || delTarget?.title }}"?不可撤销。</DialogDescription></DialogHeader>
        <DialogFooter>
          <button class="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent transition-colors" @click="delOpen = false">取消</button>
          <button class="rounded-md bg-destructive px-4 py-2 text-sm text-destructive-foreground hover:bg-destructive/90 disabled:opacity-50 transition-transform hover:scale-[0.98] active:scale-[0.97]" :disabled="deleting" @click="doDelete">
            <Loader2 v-if="deleting" class="h-4 w-4 mr-1 animate-spin" />{{ deleting ? '删除中' : '确认删除' }}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import {
  Search, Library, Loader2, ChevronRight, RefreshCw, Database,
  Upload, Sparkles, Check, RotateCcw, Pencil, Trash2, FileText, FileUp, X, Layers,
  ShieldAlert, ArrowLeft,
} from "lucide-vue-next";
import { useAuthStore } from "@/stores/auth";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import ArrayEditor from "@/components/ArrayEditor.vue";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from "@/components/ui/dialog";
import {
  searchKB, getKBStats, reindexKB, getMethod, getPaper, getTemplate, getProblem,
  listMethods, listPapers, listTemplates, listProblems,
  uploadKnowledge, getExtractionJob,
  updateMethod, deleteMethod, updatePaper, deletePaper, updateTemplate, deleteTemplate,
  updateProblem, deleteProblem,
  type SearchResult, type KBStats, type MethodCardSummary, type PaperSummary, type TemplateSummary, type ProblemSummary,
  getMethodRaw, getPaperRaw, getTemplateRaw, getProblemRaw, getProblemPapers,
} from "@/apis/knowledgeApi";

// ── auth ─────────────────────────────────────────────────────────
const router = useRouter();
const auth = useAuthStore();
const isContributor = computed(() => auth.isContributor);
const authReady = computed(() => auth.authReady);

// ── tabs ─────────────────────────────────────────────────────────
const tabs = [
  { value: "search", label: "检索知识", icon: Search },
  { value: "manage", label: "管理知识", icon: Layers },
  { value: "import", label: "导入知识", icon: Upload },
];
const activeTab = ref("search");

// ── Tab 1: Search ───────────────────────────────────────────────
const searchQuery = ref(""); const searchFilter = ref(""); const searchProblem = ref("");
const searchLoading = ref(false); const searchDone = ref(false);
const searchResults = ref<SearchResult[]>([]);
const detailItem = ref<SearchResult | null>(null); const detailLoading = ref(false);
const detailData = ref<{ type: string; data: Record<string, unknown> } | null>(null);
const detailRawText = ref(""); const detailViewMode = ref<"structured" | "raw">("structured");
const typeOpts = [{ label: "全部", value: "" }, { label: "方法卡片", value: "method_card" }, { label: "真题论文", value: "paper" }, { label: "框架模板", value: "template" }, { label: "竞赛真题", value: "problem" }];
const probOpts = [{ label: "全部", value: "" }, { label: "优化", value: "optimization" }, { label: "预测", value: "prediction" }, { label: "评价", value: "evaluation" }, { label: "统计", value: "statistics" }];
function typeLabel(t: string) { return { method_card: "方法卡片", paper: "真题论文", template: "框架模板", problem: "竞赛真题" }[t] || t; }
function badgeClass(t: string) { return { method_card: "bg-blue-100 text-blue-700", paper: "bg-purple-100 text-purple-700", template: "bg-green-100 text-green-700" }[t] || "bg-muted"; }
async function doSearch() {
  if (!searchQuery.value.trim()) return;
  searchLoading.value = true; searchDone.value = true;
  try { const r = await searchKB({ q: searchQuery.value.trim(), type: searchFilter.value || undefined, problem_type: searchProblem.value || undefined, k: 10 }); searchResults.value = r.data.results; }
  catch { searchResults.value = []; }
  finally { searchLoading.value = false; }
}

// ── 默认浏览全部（不搜索也能看到知识库存量）──────────────────
const browseAll = ref<SearchResult[]>([]);
const isBrowsing = computed(() => !searchDone.value || !searchQuery.value.trim());
const visibleResults = computed<SearchResult[]>(() => {
  const list = isBrowsing.value ? browseAll.value : searchResults.value;
  return searchFilter.value ? list.filter((r) => r.type === searchFilter.value) : list;
});
async function loadBrowseAll() {
  try {
    const [m, p, t, pr] = await Promise.all([listMethods(), listPapers(), listTemplates(), listProblems()]);
    browseAll.value = [
      ...(m.data as any[]).map((c) => ({ id: c.card_id, type: "method_card" as const, name: c.name, title: c.name, snippet: (c.principle || "").slice(0, 120), score: null })),
      ...(p.data as any[]).map((x) => ({ id: x.paper_id, type: "paper" as const, name: x.title, title: x.title, snippet: `${x.year} · ${x.competition} · ${x.problem || ""}`, score: null })),
      ...(t.data as any[]).map((x) => ({ id: x.template_id, type: "template" as const, name: x.name, title: x.name, snippet: (x.applicable_to || []).join("、"), score: null })),
      ...(pr.data as any[]).map((x) => ({ id: x.problem_id, type: "problem" as const, name: x.title, title: x.title, snippet: `${x.year} · ${x.competition} · ${x.problem || ""}`, score: null })),
    ];
  } catch { browseAll.value = []; }
}
// 清空搜索词时回到浏览模式
watch(searchQuery, (v) => { if (!v.trim()) searchDone.value = false; });
async function openDetail(r: SearchResult) {
  detailItem.value = r; detailLoading.value = true; detailData.value = null;
  detailRawText.value = ""; detailViewMode.value = "structured";
  try {
    if (r.type === "method_card") { const res = await getMethod(r.id); detailData.value = { type: "method_card", data: res.data as any }; }
    else if (r.type === "paper") { const res = await getPaper(r.id); detailData.value = { type: "paper", data: res.data as any }; }
    else if (r.type === "problem") { const res = await getProblem(r.id); detailData.value = { type: "problem", data: res.data as any }; }
    else { const res = await getTemplate(r.id); detailData.value = { type: "template", data: res.data as any }; }
  } catch { /* ignore */ }
  finally { detailLoading.value = false; }
  // Fetch raw text in background
  try {
    if (r.type === "method_card") { const rr = await getMethodRaw(r.id); detailRawText.value = rr.data.raw_text; }
    else if (r.type === "paper") { const rr = await getPaperRaw(r.id); detailRawText.value = rr.data.raw_text; }
    else if (r.type === "problem") { const rr = await getProblemRaw(r.id); detailRawText.value = rr.data.raw_text; }
    else { const rr = await getTemplateRaw(r.id); detailRawText.value = rr.data.raw_text; }
  } catch { /* no raw text available */ }
}
async function openProblemFromPaper(problemRef: string) {
  // 打开关联的题目详情
  detailItem.value = { id: problemRef, type: "problem", name: "", title: "", snippet: "", score: null } as any;
  detailLoading.value = true; detailData.value = null; detailRawText.value = ""; detailViewMode.value = "structured";
  try {
    const res = await getProblem(problemRef);
    detailData.value = { type: "problem", data: res.data as any };
  } catch { /* ignore */ }
  finally { detailLoading.value = false; }
  try { const rr = await getProblemRaw(problemRef); detailRawText.value = rr.data.raw_text; } catch { /* */ }
}

// ── Tab 2: Manage ───────────────────────────────────────────────
const mgrType = ref("method"); const mgrEntries = ref<any[]>([]); const mgrLoading = ref(false);
const mgrTypes = [{ label: "方法卡片", value: "method" }, { label: "真题论文", value: "paper" }, { label: "框架模板", value: "template" }, { label: "竞赛真题", value: "problem" }];
const mgrTypeLabel = computed(() => ({ method: "方法", paper: "论文", template: "模板", problem: "题目" }[mgrType.value]));
const mgrBadgeClass = computed(() => ({ method: "bg-blue-100 text-blue-700", paper: "bg-purple-100 text-purple-700", template: "bg-green-100 text-green-700", problem: "bg-amber-100 text-amber-700" }[mgrType.value]));
function mgrSub(e: any) {
  if (mgrType.value === "method") return (e.category || []).join(", ");
  if (mgrType.value === "paper") return `${e.year||""} ${e.competition||""} ${e.problem_id||""} ★${e.quality_rating||3}` + (e.problem_ref ? ` · 🔗已关联` : ` · ⚠未关联`);
  if (mgrType.value === "problem") return `${e.year||""} ${e.competition||""} ${e.problem_id||""} · ${e.linked_papers_count||0}篇论文`;
  return `${e.steps_count||0} 个步骤`;
}
async function loadMgrList() {
  mgrLoading.value = true;
  try {
    if (mgrType.value === "method") { const r = await listMethods(); mgrEntries.value = r.data as any; }
    else if (mgrType.value === "paper") { const r = await listPapers(); mgrEntries.value = r.data as any; }
    else if (mgrType.value === "problem") { const r = await listProblems(); mgrEntries.value = r.data as any; }
    else { const r = await listTemplates(); mgrEntries.value = r.data as any; }
  } catch { mgrEntries.value = []; }
  finally { mgrLoading.value = false; }
}
watch(mgrType, () => loadMgrList());

// Edit
const editOpen = ref(false); const editSaving = ref(false); const editLoading = ref(false); const editForm = ref<Record<string, any>>({});
async function openEdit(e: any) {
  editLoading.value = true;
  editOpen.value = true;
  editForm.value = { ...e };
  try {
    let detail: any = null;
    if (mgrType.value === "method") detail = (await getMethod(e.id)).data;
    else if (mgrType.value === "paper") detail = (await getPaper(e.id)).data;
    else if (mgrType.value === "template") detail = (await getTemplate(e.id)).data;
    else if (mgrType.value === "problem") detail = (await getProblem(e.id)).data;
    if (detail) editForm.value = { ...e, ...detail };
  } catch (err: any) {
    console.error("Failed to load detail:", err);
  } finally {
    editLoading.value = false;
  }
  const t: any = { ...editForm.value };
  if (mgrType.value === "method") {
    t.category = Array.isArray(t.category) ? [...t.category] : [];
    t.applicable_when = Array.isArray(t.applicable_when) ? [...t.applicable_when] : [];
    t.typical_scenarios = Array.isArray(t.typical_scenarios) ? [...t.typical_scenarios] : [];
    t.not_applicable_when = Array.isArray(t.not_applicable_when) ? [...t.not_applicable_when] : [];
    t.common_mistakes = Array.isArray(t.common_mistakes) ? t.common_mistakes.map((m:any) => ({...m})) : [];
    t.code_snippets = Array.isArray(t.code_snippets) ? t.code_snippets.map((c:any) => ({...c})) : [];
    t.formulas = Array.isArray(t.formulas) ? t.formulas.map((f:any) => ({...f})) : [];
    t.related_cards = Array.isArray(t.related_cards) ? [...t.related_cards] : [];
    t.related_papers = Array.isArray(t.related_papers) ? [...t.related_papers] : [];
  }
  if (mgrType.value === "paper") {
    const ana: any = t.analysis || {};
    t.analysis_problem_summary = ana.problem_summary || "";
    t.analysis_key_assumptions = Array.isArray(ana.key_assumptions) ? [...ana.key_assumptions] : [];
    t.analysis_decision_variables = ana.decision_variables || "";
    t.analysis_objective = ana.objective || "";
    t.analysis_constraints = ana.constraints || "";
    const mdl: any = t.model || {};
    t.model_approach = mdl.approach || "";
    t.model_innovation = mdl.innovation || "";
    t.model_solution_method = mdl.solution_method || "";
    const eva: any = t.evaluation || {};
    t.evaluation_strengths = Array.isArray(eva.strengths) ? [...eva.strengths] : [];
    t.evaluation_weaknesses = Array.isArray(eva.weaknesses) ? [...eva.weaknesses] : [];
    t.evaluation_lessons = eva.lessons || "";
    const tags: any = t.tags || {};
    t.tags_problem_type = Array.isArray(tags.problem_type) ? [...tags.problem_type] : [];
    t.tags_core_models = Array.isArray(tags.core_models) ? [...tags.core_models] : [];
    t.methodology_chain = Array.isArray(t.methodology_chain) ? [...t.methodology_chain] : [];
    t.problem_context = t.problem_context || "";
    t.key_formulas = Array.isArray(t.key_formulas) ? t.key_formulas.map((f:any) => ({...f})) : [];
    t.algorithm_outline = Array.isArray(t.algorithm_outline) ? t.algorithm_outline.map((a:any) => ({...a})) : [];
    t.assumption_analysis = Array.isArray(t.assumption_analysis) ? [...t.assumption_analysis] : [];
    t.reusable_patterns = Array.isArray(t.reusable_patterns) ? [...t.reusable_patterns] : [];
    t.common_pitfalls = Array.isArray(t.common_pitfalls) ? t.common_pitfalls.map((p:any) => ({...p})) : [];
  }
  if (mgrType.value === "template") {
    t.steps = Array.isArray(t.steps) ? t.steps.map((s:any) => ({...s})) : [];
    t.applicable_to = Array.isArray(t.applicable_to) ? [...t.applicable_to] : [];
  }
  if (mgrType.value === "problem") {
    const tags: any = t.tags || {};
    t.tags_problem_type = Array.isArray(tags.problem_type) ? [...tags.problem_type] : [];
    t.objectives = Array.isArray(t.objectives) ? [...t.objectives] : [];
    t.deliverables = Array.isArray(t.deliverables) ? [...t.deliverables] : [];
  }
  editForm.value = t;
}
async function doEditSave() {
  editSaving.value = true;
  try {
    const id = editForm.value.id || editForm.value.card_id || editForm.value.paper_id || editForm.value.problem_id || editForm.value.template_id;
    let data: any = { ...editForm.value };
    if (mgrType.value === "method") { delete data.id; await updateMethod(id, data); }
    else if (mgrType.value === "paper") {
      data.analysis = { problem_summary: data.analysis_problem_summary, key_assumptions: data.analysis_key_assumptions, decision_variables: data.analysis_decision_variables, objective: data.analysis_objective, constraints: data.analysis_constraints };
      data.model = { approach: data.model_approach, innovation: data.model_innovation, solution_method: data.model_solution_method };
      data.evaluation = { strengths: data.evaluation_strengths, weaknesses: data.evaluation_weaknesses, lessons: data.evaluation_lessons };
      data.tags = { problem_type: data.tags_problem_type, core_models: data.tags_core_models };
      ["analysis_problem_summary","analysis_key_assumptions","analysis_decision_variables","analysis_objective","analysis_constraints",
       "model_approach","model_innovation","model_solution_method","evaluation_strengths","evaluation_weaknesses","evaluation_lessons",
       "tags_problem_type","tags_core_models"].forEach(k => delete (data as any)[k]);
      await updatePaper(id, data);
    } else if (mgrType.value === "template") { delete data.id; await updateTemplate(id, data); }
    else if (mgrType.value === "problem") {
      data.tags = { ...data.tags, problem_type: data.tags_problem_type };
      delete data.tags_problem_type; delete data.id; await updateProblem(id, data);
    }
    editOpen.value = false; await loadMgrList(); await loadStats();
  } catch (e: any) { alert("保存失败: " + (e?.response?.data?.detail || e)); }
  finally { editSaving.value = false; }
}

// Delete
const delOpen = ref(false); const delTarget = ref<any>(null); const deleting = ref(false);
function confirmDel(e: any) { delTarget.value = e; delOpen.value = true; }
async function doDelete() {
  deleting.value = true;
  try {
    const id = delTarget.value.id;
    if (mgrType.value === "method") await deleteMethod(id); else if (mgrType.value === "paper") await deletePaper(id); else if (mgrType.value === "problem") await deleteProblem(id); else await deleteTemplate(id);
    delOpen.value = false; delTarget.value = null; await loadMgrList(); await loadStats();
  } catch (e: any) { alert(`删除失败: ${e?.response?.data?.detail||e}`); }
  finally { deleting.value = false; }
}

// Reindex
const reindexing = ref(false);
async function doReindex() {
  reindexing.value = true;
  try { const r = await reindexKB(); alert(r.data.message); await loadStats(); }
  catch { alert("重建索引失败"); }
  finally { reindexing.value = false; }
}

// ── Tab 3: Import ───────────────────────────────────────────────
// 题目/方法/模板上传
const impType = ref("problem"); const impText = ref(""); const impName = ref(""); const impFiles = ref<File[]>([]);
const dragOver = ref(false); const fileRef = ref<HTMLInputElement | null>(null);
const extracting = ref(false); const saving = ref(false); const extractPreview = ref(""); const extractError = ref("");
const impTypes = [{ label: "竞赛真题", value: "problem" }, { label: "方法卡片", value: "method" }, { label: "框架模板", value: "template" }];

// 论文上传（独立状态，关联到已导入的题目）
const paperText = ref(""); const paperName = ref(""); const paperFiles = ref<File[]>([]);
const paperDragOver = ref(false); const paperFileRef = ref<HTMLInputElement | null>(null);
const paperExtracting = ref(false); const paperSaving = ref(false); const paperPreview = ref(""); const paperError = ref("");
const impTypeLabel = computed(() => impTypes.find((o) => o.value === impType.value)?.label ?? "");
const impPlaceholder = computed(() => ({
  method: "粘贴方法描述...\n例如: 粒子群优化算法(PSO)是一种基于群体智能的启发式优化算法...",
  paper: "粘贴论文内容...\n例如: 2024年国赛A题优秀论文...",
  template: "粘贴分析框架描述...\n例如: 第一步: 问题识别...",
  problem: "粘贴竞赛真题...\n例如: 2024年国赛B题...",
}[impType.value]));

function triggerFileInput() { fileRef.value?.click(); }
function onFileSel(e: Event) { const fl = (e.target as HTMLInputElement).files; if (fl) addFiles(Array.from(fl)); }
function onDrop(e: DragEvent) { dragOver.value = false; if (e.dataTransfer?.files) addFiles(Array.from(e.dataTransfer.files)); }
function addFiles(newFiles: File[]) {
  const valid = newFiles.filter(f => f.size <= 10 * 1024 * 1024);
  if (valid.length < newFiles.length) extractError.value = "部分文件超过 10MB 已跳过";
  impFiles.value = [...impFiles.value, ...valid];
  if (!impName.value && valid.length > 0) impName.value = valid[0].name.replace(/\.[^.]+$/, "");
  // Pre-load small text files for preview; binary files handled by backend
  for (const f of valid) {
    const ext = f.name.split('.').pop()?.toLowerCase();
    if (ext && ["txt", "md", "tex", "csv"].includes(ext) && f.size < 500 * 1024) {
      const r = new FileReader(); r.onload = () => { if (!impText.value) impText.value = r.result as string; }; r.readAsText(f);
    }
  }
}
function removeFile(i: number) { impFiles.value.splice(i, 1); }
function clearAll() { impFiles.value = []; impText.value = ""; if (fileRef.value) fileRef.value.value = ""; }
// 追加论文: 记录最后导入的题目 ID
const lastProblemRef = ref("");
function fmtSize(b: number) { if (b<1024) return `${b}B`; if (b<1048576) return `${(b/1024).toFixed(1)}KB`; return `${(b/1048576).toFixed(1)}MB`; }

async function doExtract() {
  if (!impText.value.trim() && impFiles.value.length === 0) return;
  extracting.value = true; extractError.value = ""; extractPreview.value = "";
  try {
    const uploadParams: any = { text: impText.value.trim() || undefined, files: impFiles.value.length > 0 ? impFiles.value : undefined, kb_type: impType.value, name: impName.value };
    if (impType.value === 'paper' && lastProblemRef.value) {
      uploadParams.problem_ref = lastProblemRef.value;
    }
    const res = await uploadKnowledge(uploadParams);
    let tries = 0;
    while (tries < 60) {
      await new Promise(r => setTimeout(r, 1000));
      const job = await getExtractionJob(res.data.job_id);
      if (job.data.status === "completed") { extractPreview.value = job.data.result?.yaml_content || ""; break; }
      if (job.data.status === "error") { extractError.value = job.data.error || "提取失败"; break; }
      tries++;
    }
    if (tries >= 60) extractError.value = "提取超时";
  } catch (e: any) { extractError.value = `请求失败: ${e?.response?.data?.detail || e}`; }
  finally { extracting.value = false; }
}
async function doSaveExtract() {
  saving.value = true;
  // 从预览 YAML 中解析 entry_id
  const yamlMatch = extractPreview.value.match(/id:\s*["']?(prob_\d+|paper_\w+|mc_\d+|tpl_\w+)["']?/);
  const entryId = yamlMatch ? yamlMatch[1] : "";

  await loadStats(); await new Promise(r => setTimeout(r, 500));

  // 如果是题目导入，记录下来，方便后续追加论文
  if (impType.value === 'problem' && entryId) {
    lastProblemRef.value = entryId;
  }

  extractPreview.value = ""; extractError.value = ""; impText.value = ""; impName.value = ""; clearAll(); saving.value = false;

  if (impType.value === 'problem' && lastProblemRef.value) {
    // 不弹 alert，让用户在追加区域操作
  } else {
    alert("已保存到知识库,切换到「检索知识」可搜索验证。");
  }
}

// ── paper upload (independent from problem upload) ───────────────
function paperTriggerFile() { paperFileRef.value?.click(); }
function paperOnFileSel(e: Event) { const fl = (e.target as HTMLInputElement).files; if (fl) paperAddFiles(Array.from(fl)); }
function paperOnDrop(e: DragEvent) { paperDragOver.value = false; if (e.dataTransfer?.files) paperAddFiles(Array.from(e.dataTransfer.files)); }
function paperAddFiles(newFiles: File[]) {
  const valid = newFiles.filter(f => f.size <= 10 * 1024 * 1024);
  paperFiles.value = [...paperFiles.value, ...valid];
  if (!paperName.value && valid.length > 0) paperName.value = valid[0].name.replace(/\.[^.]+$/, "");
  for (const f of valid) {
    const ext = f.name.split('.').pop()?.toLowerCase();
    if (ext && ["txt", "md", "tex"].includes(ext) && f.size < 500 * 1024) {
      const r = new FileReader(); r.onload = () => { if (!paperText.value) paperText.value = r.result as string; }; r.readAsText(f);
    }
  }
}
function paperRemoveFile(i: number) { paperFiles.value.splice(i, 1); }
function paperClearAll() { paperFiles.value = []; paperText.value = ""; paperName.value = ""; if (paperFileRef.value) paperFileRef.value.value = ""; }

async function paperDoExtract() {
  if (!paperText.value.trim() && paperFiles.value.length === 0) return;
  paperExtracting.value = true; paperError.value = ""; paperPreview.value = "";
  try {
    const res = await uploadKnowledge({
      text: paperText.value.trim() || undefined,
      files: paperFiles.value.length > 0 ? paperFiles.value : undefined,
      kb_type: "paper", name: paperName.value,
      problem_ref: lastProblemRef.value || undefined,
    });
    let tries = 0;
    while (tries < 60) {
      await new Promise(r => setTimeout(r, 1000));
      const job = await getExtractionJob(res.data.job_id);
      if (job.data.status === "completed") { paperPreview.value = job.data.result?.yaml_content || ""; break; }
      if (job.data.status === "error") { paperError.value = job.data.error || "提取失败"; break; }
      tries++;
    }
    if (tries >= 60) paperError.value = "提取超时";
  } catch (e: any) { paperError.value = `请求失败: ${e?.response?.data?.detail || e}`; }
  finally { paperExtracting.value = false; }
}

async function paperDoSave() {
  paperSaving.value = true;
  await loadStats(); await new Promise(r => setTimeout(r, 500));
  paperPreview.value = ""; paperError.value = ""; paperText.value = ""; paperName.value = ""; paperClearAll(); paperSaving.value = false;
  alert("论文已保存并关联到题目！");
}

// ── shared ──────────────────────────────────────────────────────
const stats = ref<KBStats>({ methods_count:0,papers_count:0,templates_count:0,problems_count:0,total:0 });
async function loadStats() { try { const r = await getKBStats(); stats.value = r.data; } catch {/*ignore*/} }
onMounted(async () => {
  if (auth.token && !auth.user) await auth.checkSession();
  loadStats(); loadBrowseAll();
});
</script>
