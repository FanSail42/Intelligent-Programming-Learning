<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import WeakKpChart from '@/components/WeakKpChart.vue'
import WrongBookCharts from '@/components/WrongBookCharts.vue'
import { getMyCourses, type Course } from '@/api/course'
import {
  getDashboard,
  getRecommendations,
  getWrongBookStats,
  type DashboardData,
  type RecommendationItem,
  type WrongBookStats,
} from '@/api/learning'

const router = useRouter()
const loading = ref(false)
const statsLoading = ref(false)
const dashboard = ref<DashboardData | null>(null)
const wrongBookStats = ref<WrongBookStats | null>(null)
const courses = ref<Course[]>([])
const selectedCourseId = ref<number | null>(null)
const recommendations = ref<RecommendationItem[]>([])
const recLoading = ref(false)
const statsScopeHint = ref('')
const statsIsGlobalFallback = ref(false)
const TREND_DAYS = 7

const EVENT_ICONS: Record<string, string> = {
  code: '💻',
  warning: '⚠️',
  chat: '💬',
  material: '📄',
  default: '📌',
}

const TONE_CLASS: Record<string, string> = {
  primary: 'tone-primary',
  danger: 'tone-danger',
  warning: 'tone-warning',
  info: 'tone-info',
  success: 'tone-success',
}

const ACTION_LABELS: Record<string, string> = {
  review_wrong_book: '复习错题',
  review_material: '学习资料',
  practice_code: '代码练习',
}

const PRIORITY_LABELS: Record<string, string> = {
  high: '优先',
  medium: '建议',
  low: '巩固',
}

const PRIORITY_TYPES: Record<string, 'danger' | 'warning' | 'success'> = {
  high: 'danger',
  medium: 'warning',
  low: 'success',
}

const ACTION_ICONS: Record<string, string> = {
  review_wrong_book: '📕',
  review_material: '📄',
  practice_code: '💻',
}

function localDateKey(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function formatActivityTime(iso: string): string {
  const dt = new Date(iso)
  if (Number.isNaN(dt.getTime())) return iso
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  const clock = `${pad(dt.getHours())}:${pad(dt.getMinutes())}`
  const isToday = localDateKey(dt) === localDateKey(now)
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  const isYesterday = localDateKey(dt) === localDateKey(yesterday)

  const diffMs = now.getTime() - dt.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return `刚刚 · ${clock}`
  if (isToday) return diffMin < 60 ? `${diffMin} 分钟前` : `今天 ${clock}`
  if (isYesterday) return `昨天 ${clock}`
  const diffDay = Math.floor(diffMin / 60 / 24)
  if (diffDay < 7) return `${diffDay} 天前 · ${clock}`
  return `${dt.getMonth() + 1}-${pad(dt.getDate())} ${clock}`
}

function activityIcon(evt: { icon?: string | null; event_type: string }) {
  return EVENT_ICONS[evt.icon || ''] ?? EVENT_ICONS.default
}

function activityToneClass(evt: { tone?: string | null }) {
  return TONE_CLASS[evt.tone || ''] ?? 'tone-info'
}

function activityTitle(evt: { title?: string | null; event_type: string }) {
  return evt.title || evt.event_type
}

const weakKps = computed(() => dashboard.value?.weak_kps ?? [])

const sortedRecentEvents = computed(() => {
  const events = dashboard.value?.recent_events ?? []
  return [...events].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )
})

const avgMastery = computed(() => {
  const list = weakKps.value
  if (!list.length) return null
  return Math.round(list.reduce((acc, kp) => acc + kp.score, 0) / list.length)
})

const selectedCourseName = computed(() => {
  if (!selectedCourseId.value) return ''
  return courses.value.find((c) => c.id === selectedCourseId.value)?.name ?? ''
})

async function loadWrongBookStats() {
  statsLoading.value = true
  statsScopeHint.value = ''
  statsIsGlobalFallback.value = false
  try {
    const globalWrong = dashboard.value?.summary.wrong_count ?? 0
    const scoped = await getWrongBookStats({
      course_id: selectedCourseId.value ?? undefined,
      days: TREND_DAYS,
    })
    if (selectedCourseId.value && scoped.summary.total === 0 && globalWrong > 0) {
      wrongBookStats.value = await getWrongBookStats({ days: TREND_DAYS })
      statsIsGlobalFallback.value = true
      statsScopeHint.value = '当前课程暂无错题，展示全部课程汇总'
    } else {
      wrongBookStats.value = scoped
    }
  } catch (err: unknown) {
    wrongBookStats.value = null
    ElMessage.error(err instanceof Error ? err.message : '加载错题统计失败')
  } finally {
    statsLoading.value = false
  }
}

async function loadDashboard() {
  loading.value = true
  try {
    dashboard.value = await getDashboard(selectedCourseId.value ?? undefined)
  } catch (err: unknown) {
    dashboard.value = null
    ElMessage.error(err instanceof Error ? err.message : '加载仪表盘失败')
  } finally {
    loading.value = false
  }
}

async function loadCourses() {
  try {
    const result = await getMyCourses({ page_num: 1, page_size: 50 })
    courses.value = result.list
    if (result.list.length > 0 && !selectedCourseId.value) {
      selectedCourseId.value = result.list[0].id
    }
  } catch {
    courses.value = []
  }
}

async function loadRecommendations() {
  if (!selectedCourseId.value) {
    recommendations.value = []
    return
  }
  recLoading.value = true
  try {
    recommendations.value = await getRecommendations(selectedCourseId.value)
  } catch (err: unknown) {
    recommendations.value = []
    ElMessage.error(err instanceof Error ? err.message : '加载推荐失败')
  } finally {
    recLoading.value = false
  }
}

async function reloadCourseScoped() {
  await Promise.all([loadDashboard(), loadWrongBookStats(), loadRecommendations()])
}

function handleRecommendationAction(item: RecommendationItem) {
  if (item.action_type === 'review_wrong_book') {
    router.push({
      path: '/student/wrong-book',
      query: selectedCourseId.value ? { course_id: String(selectedCourseId.value) } : {},
    })
    return
  }
  if (item.action_type === 'practice_code') {
    router.push('/student/code')
    return
  }
  router.push({
    path: '/student/chat',
    query: selectedCourseId.value ? { course_id: String(selectedCourseId.value) } : {},
  })
}

function actionButtonText(item: RecommendationItem) {
  if (item.action_type === 'review_wrong_book') return '去错题本'
  if (item.action_type === 'practice_code') return '去代码讲解'
  return '向 AI 提问'
}

watch(selectedCourseId, () => {
  void reloadCourseScoped()
})

onMounted(async () => {
  await loadCourses()
  await reloadCourseScoped()
})
</script>

<template>
  <div class="dashboard-page">
    <!-- 顶部横幅 -->
    <header class="hero-banner">
      <div class="hero-text">
        <h1 class="hero-title">学习仪表盘</h1>
        <p class="hero-sub">汇总学习行为、错题洞察与复习路径，助你高效提升</p>
      </div>
      <div class="hero-actions">
        <span class="toolbar-label">当前课程</span>
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

    <p v-if="courses.length === 0" class="hint-banner">请先选课后查看学情与推荐</p>

    <!-- 指标卡片 -->
    <section class="metrics-row">
      <div class="metric-card metric-events" v-loading="loading">
        <div class="metric-icon">📊</div>
        <div class="metric-body">
          <div class="metric-value">{{ dashboard?.summary.total_events_7d ?? 0 }}</div>
          <div class="metric-label">近 7 日学习事件</div>
        </div>
      </div>
      <div class="metric-card metric-wrong" v-loading="loading || statsLoading">
        <div class="metric-icon">📝</div>
        <div class="metric-body">
          <div class="metric-value">{{ wrongBookStats?.summary.total ?? dashboard?.summary.wrong_count ?? 0 }}</div>
          <div class="metric-label">错题总数</div>
        </div>
      </div>
      <div class="metric-card metric-unmastered" v-loading="loading || statsLoading">
        <div class="metric-icon">⚠️</div>
        <div class="metric-body">
          <div class="metric-value">{{ wrongBookStats?.summary.unmastered ?? '—' }}</div>
          <div class="metric-label">未掌握</div>
        </div>
      </div>
      <div class="metric-card metric-rate" v-loading="loading || statsLoading">
        <div class="metric-icon">✅</div>
        <div class="metric-body">
          <div class="metric-value">
            {{ wrongBookStats ? `${wrongBookStats.summary.mastery_rate}%` : '—' }}
          </div>
          <div class="metric-label">错题掌握率</div>
        </div>
      </div>
    </section>

    <!-- 错题洞察 -->
    <section class="section-card" v-loading="statsLoading">
      <div class="section-header">
        <div>
          <h2 class="section-title">错题洞察</h2>
          <p class="section-desc">{{ statsScopeHint || `${selectedCourseName || '全部课程'} · 近 7 日` }}</p>
        </div>
      </div>
      <WrongBookCharts
        v-if="wrongBookStats && wrongBookStats.summary.total > 0"
        :stats="wrongBookStats"
        :show-summary="false"
        :course-id="statsIsGlobalFallback ? null : selectedCourseId"
      />
      <el-empty
        v-else-if="!statsLoading"
        class="section-empty"
        :description="
          (dashboard?.summary.wrong_count ?? 0) > 0
            ? '当前课程暂无错题，可切换课程或在代码讲解中提交错误代码'
            : '暂无错题。在「代码讲解」提交含错误的代码后，此处将展示趋势与环图分析'
        "
      />
    </section>

    <!-- 薄弱知识点 + 近期活动 -->
    <section class="dual-row">
      <div class="section-card dual-main" v-loading="loading">
        <div class="section-header">
          <div>
            <h2 class="section-title">薄弱知识点</h2>
            <p class="section-desc">掌握度由低到高 · 背景条对比满分 100</p>
          </div>
          <el-tag
            v-if="avgMastery !== null"
            :type="avgMastery < 60 ? 'danger' : avgMastery < 80 ? 'warning' : 'success'"
            effect="light"
            round
          >
            平均 {{ avgMastery }}
          </el-tag>
        </div>
        <WeakKpChart :items="weakKps" />
      </div>

      <div class="section-card dual-side" v-loading="loading">
        <div class="section-header">
          <h2 class="section-title">近期活动</h2>
          <p class="section-desc">近 7 日</p>
        </div>
        <div v-if="sortedRecentEvents.length" class="activity-list">
          <article
            v-for="(evt, idx) in sortedRecentEvents"
            :key="`${evt.event_type}-${evt.created_at}-${idx}`"
            class="activity-card"
            :class="activityToneClass(evt)"
          >
            <div class="activity-icon">{{ activityIcon(evt) }}</div>
            <div class="activity-body">
              <div class="activity-head">
                <span class="activity-title">{{ activityTitle(evt) }}</span>
                <time class="activity-time">{{ formatActivityTime(evt.created_at) }}</time>
              </div>
              <p v-if="evt.detail" class="activity-detail">{{ evt.detail }}</p>
              <div class="activity-meta">
                <el-tag v-if="evt.kp_name" size="small" effect="plain" round>
                  {{ evt.kp_name }}
                </el-tag>
                <span v-if="evt.course_name" class="activity-course">{{ evt.course_name }}</span>
              </div>
            </div>
          </article>
        </div>
        <el-empty v-else description="近 7 日暂无活动" :image-size="72" />
      </div>
    </section>

    <!-- 复习推荐 -->
    <section class="section-card rec-section" v-loading="recLoading">
      <div class="section-header">
        <div>
          <h2 class="section-title">复习推荐</h2>
          <p class="section-desc">基于薄弱知识点与错题情况生成的学习路径</p>
        </div>
      </div>

      <div v-if="recommendations.length" class="rec-grid">
        <article
          v-for="(item, idx) in recommendations"
          :key="idx"
          class="rec-card"
          :class="`rec-${item.priority}`"
        >
          <div class="rec-top">
            <span class="rec-icon">{{ ACTION_ICONS[item.action_type] ?? '📌' }}</span>
            <el-tag size="small" :type="PRIORITY_TYPES[item.priority] ?? 'info'" effect="dark" round>
              {{ PRIORITY_LABELS[item.priority] ?? item.priority }}
            </el-tag>
          </div>
          <h3 class="rec-kp">{{ item.kp_name }}</h3>
          <p class="rec-type">{{ ACTION_LABELS[item.action_type] ?? item.action_type }}</p>
          <div class="rec-score-bar">
            <div class="rec-score-track">
              <div
                class="rec-score-fill"
                :style="{
                  width: `${item.score}%`,
                  background: item.score < 60 ? '#ee6666' : item.score < 80 ? '#fac858' : '#91cc75',
                }"
              />
            </div>
            <span class="rec-score-num">{{ item.score }}</span>
          </div>
          <p class="rec-reason">{{ item.reason }}</p>
          <div v-if="item.wrong_count > 0" class="rec-badge">未掌握错题 {{ item.wrong_count }} 道</div>
          <div v-if="item.material_name" class="rec-material" :title="item.material_name">
            📎 {{ item.material_name }}
          </div>
          <el-button type="primary" round size="small" class="rec-btn" @click="handleRecommendationAction(item)">
            {{ actionButtonText(item) }}
          </el-button>
        </article>
      </div>

      <el-empty
        v-else-if="!recLoading && selectedCourseId"
        description="暂无推荐，继续学习或提交代码后将自动生成"
        :image-size="80"
      />
    </section>
  </div>
</template>

<style scoped>
.dashboard-page {
  max-width: 1240px;
  margin: 0 auto;
  padding-bottom: 32px;
}

.hero-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  padding: 24px 28px;
  margin-bottom: 20px;
  border-radius: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.35);
}

.hero-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
}

.hero-sub {
  margin: 6px 0 0;
  font-size: 13px;
  opacity: 0.88;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-label {
  font-size: 13px;
  opacity: 0.9;
}

.course-select {
  width: 280px;
}

.hint-banner {
  margin: -8px 0 16px;
  padding: 10px 16px;
  background: #fdf6ec;
  color: #e6a23c;
  border-radius: 8px;
  font-size: 13px;
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #ebeef5;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}

.metric-icon {
  font-size: 28px;
  line-height: 1;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.1;
}

.metric-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.metric-events .metric-value {
  color: #5470c6;
}

.metric-wrong .metric-value {
  color: #fc8452;
}

.metric-unmastered .metric-value {
  color: #ee6666;
}

.metric-rate .metric-value {
  color: #91cc75;
}

.section-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 16px rgba(84, 112, 198, 0.05);
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.section-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #303133;
}

.section-desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: #a8abb2;
}

.section-empty {
  padding: 24px 0;
}

.dual-row {
  display: grid;
  grid-template-columns: 1.55fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.dual-main,
.dual-side {
  margin-bottom: 0;
  min-height: 380px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 340px;
  overflow-y: auto;
  padding-right: 4px;
}

.activity-card {
  display: flex;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #ebeef5;
  background: #fafbfc;
  transition: box-shadow 0.15s, transform 0.15s;
}

.activity-card:hover {
  box-shadow: 0 4px 14px rgba(84, 112, 198, 0.1);
  transform: translateY(-1px);
}

.activity-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: #eef2ff;
}

.activity-body {
  flex: 1;
  min-width: 0;
}

.activity-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.activity-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.activity-time {
  flex-shrink: 0;
  font-size: 12px;
  color: #a8abb2;
}

.activity-detail {
  margin: 0 0 8px;
  font-size: 13px;
  line-height: 1.5;
  color: #606266;
}

.activity-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.activity-course {
  font-size: 12px;
  color: #909399;
}

.tone-danger .activity-icon {
  background: #fef0f0;
}

.tone-warning .activity-icon {
  background: #fdf6ec;
}

.tone-success .activity-icon {
  background: #f0f9eb;
}

.tone-info .activity-icon {
  background: #ecf5ff;
}

.tone-primary .activity-icon {
  background: #eef2ff;
}

.rec-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.rec-card {
  display: flex;
  flex-direction: column;
  padding: 20px;
  border-radius: 14px;
  border: 1px solid #ebeef5;
  background: linear-gradient(160deg, #fafbff 0%, #f5f7fa 100%);
  transition: box-shadow 0.2s, transform 0.2s;
}

.rec-card:hover {
  box-shadow: 0 8px 24px rgba(84, 112, 198, 0.12);
  transform: translateY(-2px);
}

.rec-high {
  border-color: #fde2e2;
  background: linear-gradient(160deg, #fff5f5 0%, #fef0f0 100%);
}

.rec-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.rec-icon {
  font-size: 22px;
}

.rec-kp {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.rec-type {
  margin: 0 0 12px;
  font-size: 12px;
  color: #909399;
}

.rec-score-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.rec-score-track {
  flex: 1;
  height: 8px;
  background: #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.rec-score-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.rec-score-num {
  font-size: 14px;
  font-weight: 700;
  color: #606266;
  min-width: 28px;
}

.rec-reason {
  flex: 1;
  margin: 0 0 10px;
  font-size: 13px;
  color: #606266;
  line-height: 1.55;
}

.rec-badge {
  font-size: 12px;
  color: #e6a23c;
  margin-bottom: 6px;
}

.rec-material {
  font-size: 12px;
  color: #5470c6;
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rec-btn {
  align-self: flex-start;
  margin-top: auto;
}

@media (max-width: 1024px) {
  .metrics-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .dual-row {
    grid-template-columns: 1fr;
  }

  .rec-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .metrics-row {
    grid-template-columns: 1fr;
  }

  .hero-banner {
    padding: 18px;
  }

  .course-select {
    width: 100%;
  }
}
</style>
