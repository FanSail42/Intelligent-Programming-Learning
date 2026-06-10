<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import type { WrongBookStats } from '@/api/learning'
import { languageLabel } from '@/constants/codeLanguages'
import {
  DASHBOARD_PALETTE,
  DASHBOARD_GRADIENT,
  linearGradient,
} from '@/constants/dashboardTheme'

const props = withDefaults(
  defineProps<{
    stats: WrongBookStats
    showSummary?: boolean
    courseId?: number | null
  }>(),
  {
    showSummary: true,
    courseId: null,
  },
)

const router = useRouter()

const SOURCE_ORDER = [
  { source_type: 'code_submission', label: '代码讲解' },
  { source_type: 'chat_message', label: 'AI 对话' },
] as const

const trendRef = ref<HTMLElement | null>(null)
const masteryRef = ref<HTMLElement | null>(null)
const sourceRef = ref<HTMLElement | null>(null)
const categoryRef = ref<HTMLElement | null>(null)

let charts: echarts.ECharts[] = []
let resizeObserver: ResizeObserver | null = null

function disposeCharts() {
  charts.forEach((c) => c.dispose())
  charts = []
}

function initChart(el: HTMLElement | null): echarts.ECharts | null {
  if (!el) return null
  const existing = echarts.getInstanceByDom(el)
  if (existing) existing.dispose()
  const instance = echarts.init(el)
  charts.push(instance)
  return instance
}

async function renderAll() {
  await nextTick()
  await new Promise<void>((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()))
  })

  disposeCharts()
  const s = props.stats

  const sourceMap = new Map(s.by_source.map((item) => [item.source_type, item.count]))
  const sourceData = SOURCE_ORDER.map((item, idx) => ({
    name: item.label,
    value: sourceMap.get(item.source_type) ?? 0,
    itemStyle: { color: DASHBOARD_PALETTE[idx] },
  }))

  const topCats = [...s.by_category]
    .sort((a, b) => b.total - a.total)
    .slice(0, 6)

  const trend = initChart(trendRef.value)
  trend?.setOption({
    color: [DASHBOARD_PALETTE[0]],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#eee',
      textStyle: { color: '#333' },
    },
    grid: { left: 12, right: 20, top: 36, bottom: 28, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: s.trend.map((t) => t.date.slice(5)),
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisLabel: { color: '#909399', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { type: 'dashed', color: '#ebeef5' } },
      axisLabel: { color: '#909399', fontSize: 11 },
    },
    series: [
      {
        name: '新增错题',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: s.trend.some((t) => t.count > 0),
        lineStyle: { width: 3, color: DASHBOARD_PALETTE[0] },
        itemStyle: { color: DASHBOARD_PALETTE[0], borderWidth: 2, borderColor: '#fff' },
        areaStyle: {
          color: linearGradient(echarts, DASHBOARD_GRADIENT.info, true),
          opacity: 0.35,
        },
        data: s.trend.map((t) => t.count),
      },
    ],
  })

  const masteryRate = s.summary.mastery_rate
  const mastery = initChart(masteryRef.value)
  mastery?.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    color: [DASHBOARD_PALETTE[2], DASHBOARD_PALETTE[1]],
    series: [
      {
        type: 'pie',
        radius: ['58%', '78%'],
        center: ['50%', '48%'],
        avoidLabelOverlap: true,
        label: { show: false },
        data: s.mastered_pie.filter((i) => i.value > 0).length
          ? s.mastered_pie.filter((i) => i.value > 0)
          : [{ name: '暂无', value: 1, itemStyle: { color: '#e4e7ed' } }],
      },
    ],
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '42%',
        style: {
          text: `${masteryRate}%`,
          fill: '#303133',
          fontSize: 22,
          fontWeight: 700,
        },
      },
      {
        type: 'text',
        left: 'center',
        top: '54%',
        style: {
          text: '掌握率',
          fill: '#909399',
          fontSize: 11,
        },
      },
    ],
  })

  const source = initChart(sourceRef.value)
  source?.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 道 ({d}%)' },
    color: [DASHBOARD_PALETTE[0], DASHBOARD_PALETTE[7]],
    legend: {
      bottom: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { fontSize: 11, color: '#606266' },
    },
    series: [
      {
        type: 'pie',
        radius: ['42%', '62%'],
        center: ['50%', '44%'],
        label: {
          show: true,
          formatter: '{b}\n{c}',
          fontSize: 11,
          color: '#606266',
        },
        labelLine: { length: 8, length2: 6 },
        data: sourceData,
      },
    ],
  })

  const category = initChart(categoryRef.value)
  category?.setOption({
    color: DASHBOARD_PALETTE,
    tooltip: { trigger: 'item', formatter: '{b}<br/>错题 {c} 道 ({d}%)' },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 4,
      top: 'middle',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { fontSize: 11, color: '#606266' },
    },
    series: [
      {
        name: '错题类别',
        type: 'pie',
        radius: ['18%', '68%'],
        center: ['38%', '50%'],
        roseType: 'area',
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        data: topCats.length
          ? topCats.map((c) => ({ name: c.label, value: c.total }))
          : [{ name: '暂无类别', value: 1, itemStyle: { color: '#e4e7ed' } }],
      },
    ],
  })

  charts.forEach((c) => c.resize())
}

function handleResize() {
  charts.forEach((c) => c.resize())
}

function setupResizeObserver() {
  resizeObserver?.disconnect()
  resizeObserver = new ResizeObserver(() => handleResize())
  for (const el of [trendRef.value, masteryRef.value, sourceRef.value, categoryRef.value]) {
    if (el) resizeObserver.observe(el)
  }
}

function goWrongBook() {
  router.push({
    path: '/student/wrong-book',
    query: props.courseId ? { course_id: String(props.courseId) } : {},
  })
}

watch(
  () => props.stats,
  () => void renderAll().then(setupResizeObserver),
  { deep: true },
)

onMounted(() => {
  void renderAll().then(setupResizeObserver)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  resizeObserver?.disconnect()
  disposeCharts()
})

const hasLanguage = () => props.stats.by_language.length > 0
</script>

<template>
  <div class="analytics-wrap">
    <div v-if="showSummary" class="summary-row">
      <div v-for="(item, idx) in [
        { n: stats.summary.total, l: '错题总数', cls: '' },
        { n: stats.summary.unmastered, l: '未掌握', cls: 'warn' },
        { n: stats.summary.mastered, l: '已掌握', cls: 'ok' },
        { n: `${stats.summary.mastery_rate}%`, l: '掌握率', cls: 'rate' },
      ]" :key="idx" class="mini-stat" :class="item.cls">
        <div class="mini-num">{{ item.n }}</div>
        <div class="mini-label">{{ item.l }}</div>
      </div>
    </div>

    <div class="analytics-grid">
      <div class="panel panel-trend">
        <div class="panel-head">
          <span class="panel-title">近 30 日新增趋势</span>
          <span class="panel-desc">折线面积图 · 观察错题积累节奏</span>
        </div>
        <div ref="trendRef" class="chart-trend" />
      </div>

      <div class="panel-col-rings">
        <div class="panel panel-ring">
          <div class="panel-title">掌握占比</div>
          <div ref="masteryRef" class="chart-ring" />
        </div>
        <div class="panel panel-ring">
          <div class="panel-title">来源构成</div>
          <div ref="sourceRef" class="chart-ring" />
        </div>
      </div>

      <div class="panel panel-rose">
        <div class="panel-head">
          <span class="panel-title">类别分布 TOP6</span>
          <span class="panel-desc">南丁格尔玫瑰图 · 面积越大占比越高</span>
        </div>
        <div ref="categoryRef" class="chart-rose" />
      </div>
    </div>

    <div class="analytics-footer">
      <div v-if="hasLanguage()" class="lang-row">
        <span class="lang-title">编程语言</span>
        <el-tag
          v-for="item in stats.by_language"
          :key="item.language"
          size="small"
          effect="plain"
          round
        >
          {{ languageLabel(item.language) }} · {{ item.count }}
        </el-tag>
      </div>
      <el-button type="primary" link @click="goWrongBook">查看错题详情 →</el-button>
    </div>
  </div>
</template>

<style scoped>
.analytics-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.mini-stat {
  text-align: center;
  padding: 10px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f5f7fa 0%, #eef1f6 100%);
}

.mini-stat.warn {
  background: linear-gradient(135deg, #fff7e6 0%, #ffe7ba33 100%);
}

.mini-stat.ok {
  background: linear-gradient(135deg, #f0f9eb 0%, #d9f7be33 100%);
}

.mini-stat.rate {
  background: linear-gradient(135deg, #e8f4ff 0%, #bae0ff33 100%);
}

.mini-num {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}

.mini-label {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.analytics-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  grid-template-rows: auto auto;
  gap: 14px;
}

.panel {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 14px 16px 10px;
  box-shadow: 0 2px 12px rgba(84, 112, 198, 0.06);
}

.panel-head {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 4px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.panel-desc {
  font-size: 11px;
  color: #a8abb2;
}

.panel-trend {
  grid-row: span 2;
  display: flex;
  flex-direction: column;
}

.chart-trend {
  flex: 1;
  width: 100%;
  min-height: 300px;
  height: 300px;
}

.panel-col-rings {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.panel-ring {
  flex: 1;
  min-height: 0;
}

.chart-ring {
  width: 100%;
  height: 138px;
  min-height: 138px;
}

.panel-rose {
  grid-column: 1 / -1;
}

.chart-rose {
  width: 100%;
  height: 220px;
  min-height: 220px;
}

.analytics-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.lang-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.lang-title {
  font-size: 12px;
  color: #909399;
}

@media (max-width: 960px) {
  .summary-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .analytics-grid {
    grid-template-columns: 1fr;
  }

  .panel-trend {
    grid-row: auto;
  }
}
</style>
