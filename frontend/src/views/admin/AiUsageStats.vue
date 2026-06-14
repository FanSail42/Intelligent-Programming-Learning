<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  getAiUsage,
  getStudentAiUsage,
  type AiUsage,
  type StudentTokenUsage,
} from '@/api/admin'

const loading = ref(false)
const studentLoading = ref(false)
const usage = ref<AiUsage | null>(null)
const studentUsage = ref<StudentTokenUsage[]>([])
const studentTotal = ref(0)
const studentPage = ref(1)
const studentPageSize = ref(10)
const studentKeyword = ref('')

const trendRef = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null

const TIER_LABELS: Record<string, string> = {
  fast: '高速',
  balanced: '均衡',
  premium: '旗舰',
  reasoning: '推理',
  code: '代码',
  custom: '自定义',
  long_context: '长上下文',
  standard: '标准',
}

const CATEGORY_LABELS: Record<string, string> = {
  chat: '对话',
  code: '代码',
  reasoning: '推理',
}

function tierLabel(tier?: string | null) {
  if (!tier) return '—'
  return TIER_LABELS[tier] ?? tier
}

function categoryLabel(cat?: string | null) {
  if (!cat) return '—'
  return CATEGORY_LABELS[cat] ?? cat
}

function formatTime(iso?: string | null) {
  if (!iso) return '—'
  const dt = new Date(iso)
  if (Number.isNaN(dt.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`
}

async function loadStudentUsage() {
  studentLoading.value = true
  try {
    const page = await getStudentAiUsage({
      username: studentKeyword.value.trim() || undefined,
      page_num: studentPage.value,
      page_size: studentPageSize.value,
    })
    studentUsage.value = page.list
    studentTotal.value = page.total
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载学生用量失败')
  } finally {
    studentLoading.value = false
  }
}

function renderTrendChart() {
  if (!trendRef.value || !usage.value) return
  if (!trendChart) trendChart = echarts.init(trendRef.value)
  const dates = usage.value.daily_tokens_7d.map((d) => d.date.slice(5))
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['Token', '调用次数'], bottom: 0 },
    grid: { left: 48, right: 24, top: 24, bottom: 48 },
    xAxis: { type: 'category', data: dates },
    yAxis: [
      { type: 'value', name: 'Token' },
      { type: 'value', name: '次数', splitLine: { show: false } },
    ],
    series: [
      {
        name: 'Token',
        type: 'line',
        smooth: true,
        data: usage.value.daily_tokens_7d.map((d) => d.tokens),
        areaStyle: { opacity: 0.12 },
        itemStyle: { color: '#409eff' },
      },
      {
        name: '调用次数',
        type: 'bar',
        yAxisIndex: 1,
        data: usage.value.daily_calls_7d.map((d) => d.calls),
        itemStyle: { color: '#67c23a', opacity: 0.75 },
      },
    ],
  })
}

async function loadAll() {
  loading.value = true
  try {
    usage.value = await getAiUsage()
    await loadStudentUsage()
    await nextTick()
    renderTrendChart()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载用量数据失败')
  } finally {
    loading.value = false
  }
}

function onStudentSearch() {
  studentPage.value = 1
  loadStudentUsage()
}

function onStudentPageChange(page: number) {
  studentPage.value = page
  loadStudentUsage()
}

const hasStudentData = computed(() => studentUsage.value.some((s) => s.tokens_today > 0))

watch(usage, () => nextTick(renderTrendChart))

onMounted(() => {
  loadAll()
  window.addEventListener('resize', renderTrendChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderTrendChart)
  trendChart?.dispose()
})
</script>

<template>
  <div class="page" v-loading="loading">
    <header class="page-header">
      <div>
        <h1 class="title">AI 用量监控</h1>
        <p class="subtitle">查看全站与学生 Token 消耗、调用场景及模型分布</p>
      </div>
      <el-button @click="loadAll">刷新</el-button>
    </header>

    <section v-if="usage" class="metrics-grid">
      <div class="metric-card primary">
        <div class="metric-value">{{ usage.tokens_today.toLocaleString() }}</div>
        <div class="metric-label">今日 Token</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">{{ usage.calls_today.toLocaleString() }}</div>
        <div class="metric-label">今日调用</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">{{ usage.tokens_total.toLocaleString() }}</div>
        <div class="metric-label">累计 Token</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">{{ usage.daily_limit_per_user }}</div>
        <div class="metric-label">每用户日限额（次）</div>
      </div>
    </section>

    <el-row :gutter="16" class="top-row">
      <el-col :xs="24" :lg="16">
        <el-card shadow="never" class="section-card">
          <template #header>
            <span>近 7 日 Token 趋势</span>
          </template>
          <div ref="trendRef" class="trend-chart" />
          <el-table :data="usage?.daily_tokens_7d ?? []" size="small" stripe class="trend-table">
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column label="Token">
              <template #default="{ row }">{{ row.tokens.toLocaleString() }}</template>
            </el-table-column>
            <el-table-column label="调用次数">
              <template #default="{ row }">
                {{
                  usage?.daily_calls_7d.find((d) => d.date === row.date)?.calls?.toLocaleString() ??
                  0
                }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="section-card active-model-card">
          <template #header>
            <span>当前系统模型</span>
          </template>
          <div v-if="usage" class="active-model">
            <div class="active-name">{{ usage.active_llm_model_name }}</div>
            <div class="active-id">{{ usage.active_llm_model }}</div>
            <p class="active-hint">学生在 AI 对话 / 代码讲解中实际调用的默认对话模型</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="section-card student-card" v-loading="studentLoading">
      <template #header>
        <div class="card-head">
          <span>学生 Token 用量</span>
          <el-input
            v-model="studentKeyword"
            placeholder="搜索学生用户名"
            clearable
            style="width: 220px"
            @keyup.enter="onStudentSearch"
            @clear="onStudentSearch"
          />
        </div>
      </template>

      <el-empty v-if="!hasStudentData && !studentLoading" description="暂无学生调用记录" />

      <el-table v-else :data="studentUsage" stripe row-key="user_id">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-panel">
              <div class="expand-block">
                <h4>今日按模型</h4>
                <el-table v-if="row.models_today.length" :data="row.models_today" size="small">
                  <el-table-column prop="model_name" label="模型" min-width="140" />
                  <el-table-column prop="model_id" label="Model ID" min-width="120" />
                  <el-table-column label="类别" width="80">
                    <template #default="{ row: m }">{{ categoryLabel(m.model_category) }}</template>
                  </el-table-column>
                  <el-table-column label="档位" width="80">
                    <template #default="{ row: m }">{{ tierLabel(m.model_tier) }}</template>
                  </el-table-column>
                  <el-table-column label="Token" width="90">
                    <template #default="{ row: m }">{{ m.tokens.toLocaleString() }}</template>
                  </el-table-column>
                  <el-table-column prop="calls" label="次数" width="70" />
                </el-table>
                <span v-else class="empty-hint">今日暂无模型调用</span>
              </div>
              <div class="expand-block">
                <h4>今日按场景</h4>
                <el-table v-if="row.scenes_today.length" :data="row.scenes_today" size="small">
                  <el-table-column prop="scene_label" label="场景" />
                  <el-table-column prop="scene" label="标识" />
                  <el-table-column label="Token" width="90">
                    <template #default="{ row: s }">{{ s.tokens.toLocaleString() }}</template>
                  </el-table-column>
                  <el-table-column prop="calls" label="次数" width="70" />
                </el-table>
                <span v-else class="empty-hint">今日暂无场景记录</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="学生" width="110" fixed />
        <el-table-column label="今日 Token" width="110">
          <template #default="{ row }">{{ row.tokens_today.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="累计 Token" width="110">
          <template #default="{ row }">{{ row.tokens_total.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="今日调用" width="100">
          <template #default="{ row }">
            {{ row.calls_today }} / {{ row.daily_limit ?? usage?.daily_limit_per_user ?? '—' }}
          </template>
        </el-table-column>
        <el-table-column label="最近模型" min-width="130">
          <template #default="{ row }">
            <span v-if="row.last_model_name">{{ row.last_model_name }}</span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="模型类别" width="90">
          <template #default="{ row }">{{ categoryLabel(row.last_model_category) }}</template>
        </el-table-column>
        <el-table-column label="最近场景" width="100">
          <template #default="{ row }">{{ row.last_scene_label ?? '—' }}</template>
        </el-table-column>
        <el-table-column label="最近 Token" width="100">
          <template #default="{ row }">{{ row.last_tokens?.toLocaleString() ?? 0 }}</template>
        </el-table-column>
        <el-table-column label="最近调用" width="110">
          <template #default="{ row }">{{ formatTime(row.last_invoke_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="studentPage"
          :page-size="studentPageSize"
          :total="studentTotal"
          layout="total, prev, pager, next"
          @current-change="onStudentPageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page {
  max-width: 1280px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.title {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 700;
  color: #303133;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  color: #909399;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

@media (max-width: 900px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.metric-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.metric-card.primary {
  border-left: 3px solid #409eff;
}

.metric-value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.top-row {
  margin-bottom: 16px;
}

.section-card {
  margin-bottom: 16px;
}

.trend-chart {
  height: 260px;
  width: 100%;
}

.trend-table {
  margin-top: 12px;
}

.active-model-card {
  height: 100%;
}

.active-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.active-id {
  font-family: monospace;
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.active-hint {
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
  margin-top: 12px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.expand-panel {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 8px 12px 12px;
}

@media (max-width: 768px) {
  .expand-panel {
    grid-template-columns: 1fr;
  }
}

.expand-block h4 {
  margin: 0 0 8px;
  font-size: 13px;
  color: #606266;
}

.empty-hint {
  font-size: 12px;
  color: #909399;
}

.muted {
  color: #909399;
}
</style>
