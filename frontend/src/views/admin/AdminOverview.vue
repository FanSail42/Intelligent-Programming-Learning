<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAdminOverview, type AdminOverview } from '@/api/admin'

const router = useRouter()
const loading = ref(false)
const overview = ref<AdminOverview | null>(null)

async function loadOverview() {
  loading.value = true
  try {
    overview.value = await getAdminOverview()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载概览失败')
  } finally {
    loading.value = false
  }
}

function formatTime(iso: string): string {
  const dt = new Date(iso)
  if (Number.isNaN(dt.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`
}

function go(path: string) {
  router.push(path)
}

onMounted(() => {
  loadOverview()
})
</script>

<template>
  <div class="page" v-loading="loading">
    <header class="page-header">
      <div>
        <h1 class="title">系统管理概览</h1>
        <p class="subtitle">账户、课程与近期系统操作一览</p>
      </div>
    </header>

    <section v-if="overview" class="metrics-grid">
      <div class="metric-card student" @click="go('/admin/students')">
        <div class="metric-icon">🎓</div>
        <div class="metric-body">
          <div class="metric-value">{{ overview.students.total }}</div>
          <div class="metric-label">学生账号</div>
          <div class="metric-sub">正常 {{ overview.students.active }} · 禁用 {{ overview.students.disabled }}</div>
        </div>
        <span class="metric-link">管理 →</span>
      </div>

      <div class="metric-card teacher" @click="go('/admin/teachers')">
        <div class="metric-icon">👨‍🏫</div>
        <div class="metric-body">
          <div class="metric-value">{{ overview.teachers.total }}</div>
          <div class="metric-label">教师账号</div>
          <div class="metric-sub">正常 {{ overview.teachers.active }} · 禁用 {{ overview.teachers.disabled }}</div>
        </div>
        <span class="metric-link">管理 →</span>
      </div>

      <div class="metric-card course" @click="go('/teacher/courses')">
        <div class="metric-icon">📚</div>
        <div class="metric-body">
          <div class="metric-value">{{ overview.courses.total }}</div>
          <div class="metric-label">课程总数</div>
          <div class="metric-sub">已发布 {{ overview.courses.published }}</div>
        </div>
        <span class="metric-link">课程 →</span>
      </div>

      <div class="metric-card enroll">
        <div class="metric-icon">📋</div>
        <div class="metric-body">
          <div class="metric-value">{{ overview.enrollment_total }}</div>
          <div class="metric-label">选课记录</div>
          <div class="metric-sub">累计选课人次</div>
        </div>
      </div>

      <div class="metric-card login" @click="go('/admin/logs')">
        <div class="metric-icon">🔐</div>
        <div class="metric-body">
          <div class="metric-value">{{ overview.login_events_7d }}</div>
          <div class="metric-label">近 7 日登录</div>
          <div class="metric-sub">登录事件次数</div>
        </div>
        <span class="metric-link">日志 →</span>
      </div>
    </section>

    <el-card shadow="never" class="recent-card">
      <template #header>
        <div class="card-head">
          <span>近期操作</span>
          <el-button link type="primary" @click="go('/admin/logs')">查看全部日志</el-button>
        </div>
      </template>
      <el-table v-if="overview?.recent_logs.length" :data="overview.recent_logs" stripe>
        <el-table-column prop="action_label" label="操作" width="120" />
        <el-table-column prop="username" label="操作者" width="120">
          <template #default="{ row }">{{ row.username || '—' }}</template>
        </el-table-column>
        <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="120">
          <template #default="{ row }">{{ row.ip || '—' }}</template>
        </el-table-column>
        <el-table-column label="时间" width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无操作记录" :image-size="72" />
    </el-card>

    <section class="quick-links">
      <h2 class="section-title">快捷入口</h2>
      <div class="link-grid">
        <el-button @click="go('/admin/ai-models')">AI 模型管理</el-button>
        <el-button @click="go('/admin/ai-usage')">AI 用量监控</el-button>
        <el-button @click="go('/admin/students')">学生账号管理</el-button>
        <el-button @click="go('/admin/teachers')">教师账号管理</el-button>
        <el-button @click="go('/admin/logs')">操作日志</el-button>
        <el-button @click="go('/teacher/courses')">课程管理</el-button>
        <el-button @click="go('/teacher/dashboard')">班级学情</el-button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
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
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}

.metric-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 18px 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
  position: relative;
}

.metric-card:hover {
  box-shadow: 0 4px 14px rgba(64, 158, 255, 0.12);
  transform: translateY(-1px);
}

.metric-card.enroll {
  cursor: default;
}

.metric-card.enroll:hover {
  transform: none;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.metric-icon {
  font-size: 28px;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.metric-label {
  font-size: 13px;
  color: #606266;
  margin-top: 2px;
}

.metric-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.metric-link {
  position: absolute;
  right: 14px;
  bottom: 14px;
  font-size: 12px;
  color: #409eff;
}

.recent-card {
  margin-bottom: 20px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.quick-links {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.section-title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.link-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
