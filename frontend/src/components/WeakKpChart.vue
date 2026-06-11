<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { WeakKpItem } from '@/api/learning'
import {
  linearGradient,
  scoreColor,
} from '@/constants/dashboardTheme'

const props = defineProps<{
  items: WeakKpItem[]
}>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

function buildOption(items: WeakKpItem[]): echarts.EChartsOption {
  const sorted = [...items].sort((a, b) => a.score - b.score).slice(0, 8)
  const names = sorted.map((i) => i.name)
  const scores = sorted.map((i) => i.score)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: unknown) => {
        const row = (params as { name: string; value: number }[])[0]
        if (!row) return ''
        const level = row.value < 60 ? '薄弱' : row.value < 80 ? '待巩固' : '良好'
        return `${row.name}<br/>掌握度 <b>${row.value}</b> · ${level}`
      },
    },
    grid: { left: 8, right: 40, top: 16, bottom: 8, containLabel: true },
    xAxis: {
      type: 'value',
      max: 100,
      splitLine: { lineStyle: { type: 'dashed', color: '#ebeef5' } },
      axisLabel: { color: '#909399', fontSize: 11 },
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: { width: 88, overflow: 'truncate', fontSize: 12, color: '#606266' },
      axisTick: { show: false },
      axisLine: { show: false },
    },
    series: [
      {
        name: '掌握度',
        type: 'bar',
        data: scores.map((s) => ({
          value: s,
          itemStyle: {
            color: linearGradient(echarts, [scoreColor(s), `${scoreColor(s)}55`]),
            borderRadius: [0, 8, 8, 0],
          },
        })),
        barMaxWidth: 18,
        showBackground: true,
        backgroundStyle: { color: 'rgba(180, 180, 180, 0.12)', borderRadius: [0, 8, 8, 0] },
        label: {
          show: true,
          position: 'right',
          formatter: '{c}',
          color: '#606266',
          fontSize: 11,
        },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { type: 'dashed', color: '#dcdfe6' },
          label: { fontSize: 10, color: '#c0c4cc' },
          data: [
            { xAxis: 60, name: '薄弱线' },
            { xAxis: 80, name: '巩固线' },
          ],
        },
      },
    ],
  }
}

async function renderChart() {
  await nextTick()
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  if (!props.items.length) {
    chart.clear()
    return
  }
  chart.setOption(buildOption(props.items), true)
  chart.resize()
}

function handleResize() {
  chart?.resize()
}

watch(
  () => props.items,
  () => void renderChart(),
  { deep: true },
)

onMounted(() => {
  void renderChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="weak-kp-wrap">
    <div v-if="items.length" ref="chartRef" class="chart-box" />
    <el-empty v-else description="暂无知识点数据，选课后将展示课程知识点掌握情况" />
    <div v-if="items.length" class="legend">
      <span><i class="dot weak" /> &lt;60 薄弱</span>
      <span><i class="dot mid" /> 60–79 待巩固</span>
      <span><i class="dot good" /> ≥80 良好</span>
    </div>
  </div>
</template>

<style scoped>
.weak-kp-wrap {
  min-height: 280px;
}

.chart-box {
  width: 100%;
  height: min(360px, 42vh);
  min-height: 260px;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;
}

.dot.weak {
  background: #ee6666;
}

.dot.mid {
  background: #fac858;
}

.dot.good {
  background: #91cc75;
}
</style>
