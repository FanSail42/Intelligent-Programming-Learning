<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import AppLogo from '@/components/AppLogo.vue'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const demoAccounts = [
  { role: '学生', user: 'student', pass: 'Student123!' },
  { role: '教师', user: 'teacher', pass: 'Teacher123!' },
  { role: '管理员', user: 'admin', pass: 'Admin123!' },
]

function fillDemo(item: (typeof demoAccounts)[0]) {
  form.username = item.user
  form.password = item.pass
}

async function onSubmit() {
  loading.value = true
  try {
    const user = await auth.login(form.username, form.password)
    ElMessage.success('登录成功')
    if (user?.role === 'student') {
      await router.push('/student/courses')
    } else if (user?.role === 'teacher') {
      await router.push('/teacher/courses')
    } else if (user?.role === 'admin') {
      await router.push('/admin/overview')
    } else {
      await router.push('/teacher/courses')
    }
  } catch {
    // error handled by axios interceptor
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-bg" aria-hidden="true" />
    <div class="login-overlay" aria-hidden="true" />

    <div class="login-shell">
      <section class="login-hero">
        <AppLogo size="lg" light />
        <h1 class="hero-title">智能编程学习助教</h1>
        <p class="hero-desc">
          基于 RAG 的课程知识库、AI 对话辅导、代码讲解与学习分析，助力高校计算机类课程教学。
        </p>
        <ul class="hero-features">
          <li>📚 课程资料向量检索</li>
          <li>🤖 百炼大模型 AI 辅导</li>
          <li>📊 学情仪表盘与错题本</li>
        </ul>
      </section>

      <section class="login-panel">
        <div class="panel-inner">
          <div class="panel-head">
            <AppLogo size="md" :show-text="false" />
            <div>
              <h2 class="panel-title">欢迎登录</h2>
              <p class="panel-sub">慧编学伴 · 教学管理平台</p>
            </div>
          </div>

          <el-form class="login-form" label-position="top" @submit.prevent="onSubmit">
            <el-form-item label="用户名">
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                size="large"
                clearable
              />
            </el-form-item>
            <el-form-item label="密码">
              <el-input
                v-model="form.password"
                type="password"
                show-password
                placeholder="请输入密码"
                size="large"
              />
            </el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              native-type="submit"
              class="submit-btn"
            >
              登 录
            </el-button>
          </el-form>

          <div class="demo-block">
            <span class="demo-label">演示账号（点击填充）</span>
            <div class="demo-chips">
              <button
                v-for="item in demoAccounts"
                :key="item.user"
                type="button"
                class="demo-chip"
                @click="fillDemo(item)"
              >
                {{ item.role }}
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}

.login-bg {
  position: fixed;
  inset: 0;
  background: url('/login-bg.jpg') center / cover no-repeat;
  transform: scale(1.02);
}

.login-overlay {
  position: fixed;
  inset: 0;
  background: linear-gradient(
    115deg,
    rgba(15, 23, 42, 0.88) 0%,
    rgba(30, 58, 138, 0.72) 45%,
    rgba(6, 182, 212, 0.35) 100%
  );
}

.login-shell {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 440px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 48px 32px;
  gap: 48px;
  align-items: center;
}

.login-hero {
  color: #fff;
  padding-right: 24px;
}

.hero-title {
  margin: 28px 0 12px;
  font-size: 32px;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: 0.02em;
}

.hero-desc {
  margin: 0 0 24px;
  font-size: 15px;
  line-height: 1.75;
  opacity: 0.92;
  max-width: 480px;
}

.hero-features {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 14px;
  opacity: 0.9;
}

.login-panel {
  display: flex;
  justify-content: center;
}

.panel-inner {
  width: 100%;
  max-width: 400px;
  padding: 36px 32px 28px;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(16px);
  border-radius: var(--hb-radius-lg);
  box-shadow: var(--hb-shadow-lg);
  border: 1px solid rgba(255, 255, 255, 0.6);
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.panel-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--hb-text);
}

.panel-sub {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--hb-text-secondary);
}

.login-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--hb-text);
}

.submit-btn {
  width: 100%;
  margin-top: 8px;
  height: 44px;
  font-size: 15px;
  letter-spacing: 0.12em;
  border-radius: 10px;
}

.demo-block {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px dashed var(--hb-border);
}

.demo-label {
  font-size: 12px;
  color: var(--hb-text-secondary);
}

.demo-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.demo-chip {
  padding: 6px 14px;
  font-size: 12px;
  border: 1px solid var(--hb-border);
  border-radius: 999px;
  background: #f8fafc;
  color: var(--hb-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.demo-chip:hover {
  background: #eff6ff;
  border-color: var(--hb-primary-light);
}

@media (max-width: 960px) {
  .login-shell {
    grid-template-columns: 1fr;
    padding: 32px 20px;
    justify-items: center;
  }

  .login-hero {
    display: none;
  }

  .panel-inner {
    max-width: 420px;
  }
}
</style>
