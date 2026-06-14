<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import WeakKpChart from '@/components/WeakKpChart.vue'
import WrongBookCharts from '@/components/WrongBookCharts.vue'
import { getCourses, type Course } from '@/api/course'
import {
  getTeacherCourseOverview,
  type TeacherCourseOverview,
} from '@/api/teacher'
import { DASHBOARD_PALETTE } from '@/constants/dashboardTheme'

const loading = ref(false)
const courses = ref<Course[]>([])
const selectedCourseId = ref<number | null>(null)
const overview = ref<TeacherCourseOverview | null>(null)
const TREND_DAYS = 7
const studentDialogVisible = ref(false)

const eventTrendRef = ref<HTMLElement | null>(null)
let eventChart: echarts.ECharts | null = null

const selectedCourseName = computed(
  () => overview.value?.course.name ?? courses.value.find((c) => c.id === selectedCourseId.value)?.name ?? '',
)

const weakKps = computed(() => overview.value?.weak_kps ?? [])
const wrongBookStats = computed(() => overview.value?.wrong_book_stats ?? null)
const enrolledStudents = computed(() => overview.value?.students ?? [])

const wrongBookScopeDesc = computed(() => {
  const count = overview.value?.summary.student_count ?? 0
  return count > 0
    ? `班级全体 ${count} 人错题汇总 · 折线图为近 ${TREND_DAYS} 日新增`
    : `班级全体错题汇总 · 折线图为近 ${TREND_DAYS} 日新增`
})

function formatJoinedAt(iso: string): string {
  const dt = new Date(iso)
  if (Number.isNaN(dt.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`
}

function openStudentDialog() {
  studentDialogVisible.value = true
}

const avgMastery = computed(() => {
  const list = weakKps.value
  if (!list.length) return null
  return Math.round(list.reduce((acc, kp) => acc + kp.score, 0) / list.length)
})

function localDateKey(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

async function renderEventTrend() {
  await nextTick()
  if (!eventTrendRef.value || !overview.value) return

  const trend = overview.value.event_trend
  if (!eventChart) eventChart = echarts.init(eventTrendRef.value)
  if (!trend.length) {
    eventChart.clear()
    return
  }

  const todayKey = localDateKey(new Date())
  const weekdayLabels = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const trendDates = trend.map((t) => t.date)
  const todayIdx = trendDates.length - 1
  const counts = trend.map((t) => t.count)
  const maxCount = Math.max(0, ...counts)
  const yMax = Math.max(3, Math.ceil(maxCount * 1.3))

  const xLabels = trend.map((t) => {
    const md = t.date.slice(5)
    if (t.date === todayKey) return `${md} 今日`
    const wd = weekdayLabels[new Date(`${t.date}T12:00:00`).getDay()]
    return `${md} ${wd}`
  })

  eventChart.setOption(
    {
      color: [DASHBOARD_PALETTE[4]],
      tooltip: {
        trigger: 'axis',
        formatter: (params: unknown) => {
          const row = (params as { dataIndex: number; value: number }[])[0]
          if (!row) return ''
          const date = trendDates[row.dataIndex] ?? ''
          const suffix = date === todayKey ? '（今日）' : ''
          return `${date}${suffix}<br/>学习事件 <b>${row.value}</b> 次`
        },
      },
      grid: { left: 12, right: 24, top: 40, bottom: 32, containLabel: true },
      xAxis: {
        type: 'category',
        data: xLabels,
        axisLabel: {
          fontSize: 11,
          color: '#909399',
          formatter: (value: string) =>
            value.includes('今日') ? `{today|${value}}` : value,
          rich: { today: { color: '#5470c6', fontWeight: 'bold' } },
        },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: yMax,
        minInterval: 1,
        splitLine: { lineStyle: { type: 'dashed', color: '#ebeef5' } },
      },
      series: [
        {
          name: '学习事件',
          type: 'bar',
          data: counts.map((v, idx) => ({
            value: v,
            itemStyle: {
              color: idx === todayIdx ? DASHBOARD_PALETTE[3] : DASHBOARD_PALETTE[4],
              borderRadius: [4, 4, 0, 0],
            },
          })),
          barMaxWidth: 28,
        },
      ],
    },
    true,
  )
  eventChart.resize()
}

async function loadCourses() {
  try {
    const result = await getCourses({ page_num: 1, page_size: 50 })
    courses.value = result.list
    if (result.list.length > 0 && !selectedCourseId.value) {
      selectedCourseId.value = result.list[0].id
    }
  } catch {
    courses.value = []
  }
}

async function loadOverview() {
  if (!selectedCourseId.value) {
    overview.value = null
    return
  }
  loading.value = true
  try {
    overview.value = await getTeacherCourseOverview(selectedCourseId.value, TREND_DAYS)
    await renderEventTrend()
  } catch (err: unknown) {
    overview.value = null
    ElMessage.error(err instanceof Error ? err.message : '加载班级学情失败')
  } finally {
    loading.value = false
  }
}

function handleResize() {
  eventChart?.resize()
}

watch(selectedCourseId, () => {
  void loadOverview()
})

onMounted(async () => {
  await loadCourses()
  await loadOverview()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  eventChart?.dispose()
  eventChart = null
})
</script>

<template>
  <div class="dashboard-page">
    <header class="hero-banner">
      <div class="hero-text">
        <h1 class="hero-title">班级学情</h1>
        <p class="hero-sub">班级视角汇总选课人数、错题分布与知识点掌握情况</p>
      </div>
      <div class="hero-actions">
        <span class="toolbar-label">选择课程</span>
        <el-select
          v-model="selectedCourseId"
          placeholder="选择课程"
          class="course-select"
          :disabled="courses.length === 0"
        >
          <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </div>
    </header>

    <p v-if="courses.length === 0" class="hint-banner">请先创建或发布课程后查看班级学情</p>

    <section class="metrics-row">
      <div class="metric-card metric-students clickable" v-loading="loading" @click="openStudentDialog">
        <div class="metric-icon">👥</div>
        <div class="metric-body">
          <div class="metric-value">{{ overview?.summary.student_count ?? 0 }}</div>
          <div class="metric-label">选课人数</div>
        </div>
        <el-button link type="primary" class="metric-action" @click.stop="openStudentDialog">
          查看
        </el-button>
      </div>
      <div class="metric-card metric-active" v-loading="loading">
        <div class="metric-icon">🔥</div>
        <div class="metric-body">
          <div class="metric-value">{{ overview?.summary.active_students_7d ?? 0 }}</div>
          <div class="metric-label">近 7 日活跃</div>
        </div>
      </div>
      <div class="metric-card metric-events" v-loading="loading">
        <div class="metric-icon">📊</div>
        <div class="metric-body">
          <div class="metric-value">{{ overview?.summary.total_events_7d ?? 0 }}</div>
          <div class="metric-label">近 7 日事件</div>
        </div>
      </div>
      <div class="metric-card metric-wrong" v-loading="loading">
        <div class="metric-icon">📝</div>
        <div class="metric-body">
          <div class="metric-value">{{ overview?.summary.wrong_total ?? 0 }}</div>
          <div class="metric-label">班级错题</div>
        </div>
      </div>
      <div class="metric-card metric-rate" v-loading="loading">
        <div class="metric-icon">✅</div>
        <div class="metric-body">
          <div class="metric-value">
            {{ overview ? `${overview.summary.mastery_rate}%` : '—' }}
          </div>
          <div class="metric-label">错题掌握率</div>
        </div>
      </div>
    </section>

    <section class="section-card" v-loading="loading">
      <div class="section-header">
        <div>
          <h2 class="section-title">近 7 日学习事件</h2>
          <p class="section-desc">{{ selectedCourseName || '当前课程' }} · 班级全体学生</p>
        </div>
      </div>
      <div ref="eventTrendRef" class="event-chart" />
      <el-empty
        v-if="!loading && overview && overview.summary.total_events_7d === 0"
        description="近 7 日暂无学习事件"
        :image-size="72"
      />
    </section>

    <section class="section-card" v-loading="loading">
      <div class="section-header">
        <div>
          <h2 class="section-title">班级错题洞察</h2>
          <p class="section-desc">
            班级全体 {{ overview?.summary.student_count ?? 0 }} 人 · 累计错题
            {{ overview?.summary.wrong_total ?? 0 }} 道 · 未掌握
            {{ overview?.summary.wrong_unmastered ?? 0 }} 道
          </p>
        </div>
      </div>
      <WrongBookCharts
        v-if="wrongBookStats && wrongBookStats.summary.total > 0"
        :stats="wrongBookStats"
        :show-summary="true"
        :hide-detail-link="true"
        :scope-desc="wrongBookScopeDesc"
        :course-id="selectedCourseId"
      />
      <el-empty
        v-else-if="!loading"
        description="班级暂无错题记录，学生提交代码讲解或 AI 对话后将在此汇总"
      />
    </section>

    <section class="section-card" v-loading="loading">
      <div class="section-header">
        <div>
          <h2 class="section-title">班级薄弱知识点</h2>
          <p class="section-desc">各知识点平均掌握度（越低越需关注）</p>
        </div>
        <el-tag
          v-if="avgMastery !== null"
          :type="avgMastery < 60 ? 'danger' : avgMastery < 80 ? 'warning' : 'success'"
          effect="light"
          round
        >
          班级平均 {{ avgMastery }}
        </el-tag>
      </div>
      <WeakKpChart :items="weakKps" />
    </section>

    <el-dialog
      v-model="studentDialogVisible"
      :title="`选课名单 · ${selectedCourseName || '当前课程'}`"
      width="640px"
      destroy-on-close
    >
      <div v-if="overview" class="roster-meta">
        <div class="roster-item">
          <span class="roster-label">授课教师</span>
          <span class="roster-value">{{ overview.course.teacher_name || '—' }}</span>
        </div>
        <div class="roster-item">
          <span class="roster-label">选课人数</span>
          <span class="roster-value">{{ overview.summary.student_count }} 人</span>
        </div>
      </div>

      <el-table v-if="enrolledStudents.length" :data="enrolledStudents" stripe>
        <el-table-column prop="username" label="学生账号" min-width="120" />
        <el-table-column label="选课时间" min-width="160">
          <template #default="{ row }">
            {{ formatJoinedAt(row.joined_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="wrong_count" label="本课错题" width="100" align="center" />
        <el-table-column prop="unmastered_count" label="未掌握" width="100" align="center" />
      </el-table>
      <el-empty v-else description="暂无学生选课" :image-size="80" />
    </el-dialog>
  </div>
</template>

<style scoped>
.dashboard-page {
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 32px;
}

.hero-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  padding: 24px 28px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.hero-title {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 700;
}

.hero-sub {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-label {
  font-size: 13px;
  opacity: 0.95;
}

.course-select {
  width: 240px;
}

.hint-banner {
  margin: 0 0 16px;
  padding: 10px 14px;
  background: #fdf6ec;
  color: #e6a23c;
  border-radius: 8px;
  font-size: 13px;
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 16px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.metric-card.clickable {
  cursor: pointer;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.metric-card.clickable:hover {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
  transform: translateY(-1px);
}

.metric-action {
  margin-left: auto;
  font-size: 13px;
}

.metric-icon {
  font-size: 28px;
}

.metric-value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.section-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  margin: 0 0 4px;
  font-size: 17px;
  font-weight: 600;
  color: #303133;
}

.section-desc {
  margin: 0;
  font-size: 13px;
  color: #909399;
}

.event-chart {
  width: 100%;
  height: 280px;
  min-height: 240px;
}

.roster-meta {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding: 12px 14px;
  background: #f5f7fa;
  border-radius: 8px;
}

.roster-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.roster-label {
  font-size: 12px;
  color: #909399;
}

.roster-value {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
</style>
