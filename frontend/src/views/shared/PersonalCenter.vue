<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, DataAnalysis } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  changePassword,
  getProfileSummary,
  updateUsername,
  type ProfileSummary,
} from '@/api/profile'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(true)
const summary = ref<ProfileSummary | null>(null)
const usernameSaving = ref(false)
const passwordSaving = ref(false)

const usernameForm = reactive({
  newUsername: '',
  currentPassword: '',
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const roleLabel = computed(() => {
  const map: Record<string, string> = {
    student: '学生',
    teacher: '教师',
    admin: '管理员',
  }
  return map[summary.value?.role ?? ''] ?? summary.value?.role ?? ''
})

const statusLabel = computed(() => (summary.value?.status === 'active' ? '正常' : '已禁用'))

const aiQuotaPercent = computed(() => {
  const usage = summary.value?.ai_usage
  if (!usage || !usage.daily_limit) return 0
  return Math.min(100, Math.round((usage.quota_used_today / usage.daily_limit) * 100))
})

function formatTime(value: string | null | undefined) {
  if (!value) return '—'
  return value.replace('T', ' ').slice(0, 19)
}

async function loadSummary() {
  loading.value = true
  try {
    summary.value = await getProfileSummary()
    usernameForm.newUsername = summary.value.username
  } finally {
    loading.value = false
  }
}

async function onUpdateUsername() {
  if (!usernameForm.newUsername.trim() || usernameForm.currentPassword.length < 6) {
    ElMessage.warning('请填写新用户名并输入当前密码')
    return
  }
  usernameSaving.value = true
  try {
    const user = await updateUsername(usernameForm.newUsername.trim(), usernameForm.currentPassword)
    ElMessage.success('用户名已更新')
    usernameForm.currentPassword = ''
    if (auth.user) {
      auth.user.username = user.username
    }
    await loadSummary()
  } finally {
    usernameSaving.value = false
  }
}

async function onChangePassword() {
  if (passwordForm.newPassword.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  passwordSaving.value = true
  try {
    await changePassword(passwordForm.currentPassword, passwordForm.newPassword)
    ElMessage.success('密码已修改，请重新登录')
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    auth.logout()
    await router.push('/login')
  } finally {
    passwordSaving.value = false
  }
}

onMounted(loadSummary)
</script>

<template>
  <div v-loading="loading" class="profile-page">
    <header class="page-head">
      <h1 class="page-title">个人中心</h1>
      <p class="page-subtitle">管理账号信息、安全设置，并查看账户概览</p>
    </header>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="8">
        <el-card class="profile-card" shadow="never">
          <div class="avatar-block">
            <div class="avatar-ring">
              <span class="avatar-text">{{ (summary?.username ?? '?').slice(0, 1).toUpperCase() }}</span>
            </div>
            <h2 class="profile-name">{{ summary?.username ?? '—' }}</h2>
            <div class="profile-tags">
              <el-tag type="primary" effect="plain">{{ roleLabel }}</el-tag>
              <el-tag :type="summary?.status === 'active' ? 'success' : 'danger'" effect="plain">
                {{ statusLabel }}
              </el-tag>
            </div>
          </div>

          <el-descriptions :column="1" border size="small" class="meta-desc">
            <el-descriptions-item label="用户 ID">{{ summary?.id ?? '—' }}</el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ formatTime(summary?.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="累计登录">{{ summary?.login_count ?? 0 }} 次</el-descriptions-item>
            <el-descriptions-item label="最近登录">{{ formatTime(summary?.last_login_at) }}</el-descriptions-item>
            <el-descriptions-item label="最近 IP">{{ summary?.last_login_ip || '—' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card v-if="summary?.ai_usage" class="profile-card ai-card" shadow="never">
          <template #header>
            <div class="card-head">
              <el-icon><DataAnalysis /></el-icon>
              <span>AI 用量概览</span>
            </div>
          </template>
          <div class="ai-stat-grid">
            <div class="ai-stat">
              <span class="ai-stat-val">{{ summary.ai_usage.tokens_today }}</span>
              <span class="ai-stat-label">今日 Token</span>
            </div>
            <div class="ai-stat">
              <span class="ai-stat-val">{{ summary.ai_usage.tokens_total }}</span>
              <span class="ai-stat-label">累计 Token</span>
            </div>
            <div class="ai-stat">
              <span class="ai-stat-val">{{ summary.ai_usage.calls_today }}</span>
              <span class="ai-stat-label">今日调用</span>
            </div>
          </div>
          <div class="quota-block">
            <div class="quota-head">
              <span>今日配额</span>
              <span>{{ summary.ai_usage.quota_used_today }} / {{ summary.ai_usage.daily_limit }}</span>
            </div>
            <el-progress :percentage="aiQuotaPercent" :stroke-width="10" :show-text="false" />
          </div>
          <p v-if="summary.ai_usage.last_scene_label" class="ai-last">
            最近：{{ summary.ai_usage.last_scene_label }}
            <template v-if="summary.ai_usage.last_model_name">
              · {{ summary.ai_usage.last_model_name }}
            </template>
            <br />
            <span class="ai-last-time">{{ formatTime(summary.ai_usage.last_invoke_at) }}</span>
          </p>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card class="profile-card" shadow="never">
          <template #header>
            <div class="card-head">
              <el-icon><User /></el-icon>
              <span>修改用户名</span>
            </div>
          </template>
          <el-form label-width="96px" @submit.prevent="onUpdateUsername">
            <el-form-item label="当前用户名">
              <el-input :model-value="summary?.username" disabled />
            </el-form-item>
            <el-form-item label="新用户名">
              <el-input
                v-model="usernameForm.newUsername"
                placeholder="3～64 字符"
                maxlength="64"
                clearable
              />
            </el-form-item>
            <el-form-item label="当前密码">
              <el-input
                v-model="usernameForm.currentPassword"
                type="password"
                show-password
                placeholder="验证身份"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="usernameSaving" @click="onUpdateUsername">
                保存用户名
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="profile-card" shadow="never">
          <template #header>
            <div class="card-head">
              <el-icon><Lock /></el-icon>
              <span>修改密码</span>
            </div>
          </template>
          <el-alert
            type="info"
            :closable="false"
            show-icon
            title="修改成功后将自动退出，需使用新密码重新登录。"
            class="pwd-alert"
          />
          <el-form label-width="96px" @submit.prevent="onChangePassword">
            <el-form-item label="当前密码">
              <el-input
                v-model="passwordForm.currentPassword"
                type="password"
                show-password
                placeholder="请输入当前密码"
              />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input
                v-model="passwordForm.newPassword"
                type="password"
                show-password
                placeholder="至少 6 位"
              />
            </el-form-item>
            <el-form-item label="确认新密码">
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                show-password
                placeholder="再次输入新密码"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="passwordSaving" @click="onChangePassword">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 1100px;
}

.page-head {
  margin-bottom: 20px;
}

.profile-card {
  margin-bottom: 20px;
}

.avatar-block {
  text-align: center;
  padding: 8px 0 20px;
}

.avatar-ring {
  width: 72px;
  height: 72px;
  margin: 0 auto 12px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb, #06b6d4);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.25);
}

.avatar-text {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
}

.profile-name {
  margin: 0 0 10px;
  font-size: 20px;
  font-weight: 700;
}

.profile-tags {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
}

.meta-desc {
  margin-top: 4px;
}

.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.ai-card :deep(.el-card__header) {
  padding-bottom: 8px;
}

.ai-stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.ai-stat {
  text-align: center;
  padding: 12px 8px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid var(--hb-border);
}

.ai-stat-val {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--hb-primary);
}

.ai-stat-label {
  font-size: 12px;
  color: var(--hb-text-secondary);
}

.quota-block {
  margin-bottom: 12px;
}

.quota-head {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 8px;
  color: var(--hb-text-secondary);
}

.ai-last {
  margin: 0;
  font-size: 13px;
  color: var(--hb-text-secondary);
  line-height: 1.6;
}

.ai-last-time {
  font-size: 12px;
  opacity: 0.85;
}

.pwd-alert {
  margin-bottom: 20px;
}
</style>
