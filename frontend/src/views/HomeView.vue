<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { healthCheck } from '@/api/health'

const loading = ref(true)
const healthStatus = ref<string>('检查中...')
const errorMessage = ref<string>('')
const apiBase = import.meta.env.VITE_API_BASE

onMounted(async () => {
  try {
    const data = await healthCheck()
    healthStatus.value = data.status
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '后端连接失败'
    healthStatus.value = '不可用'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="brand">
        <span class="logo">慧编学伴</span>
        <span class="subtitle">智能编程学习助教系统</span>
      </div>
    </el-header>

    <el-main class="main">
      <el-card shadow="never" class="welcome-card">
        <template #header>
          <span>Phase 0 — 工程奠基</span>
        </template>

        <el-skeleton :loading="loading" animated>
          <template #default>
            <p>前端工程已就绪，当前为空白布局页。</p>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="后端健康状态">
                <el-tag :type="healthStatus === 'healthy' ? 'success' : 'danger'">
                  {{ healthStatus }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="API 地址">
                {{ apiBase }}
              </el-descriptions-item>
              <el-descriptions-item v-if="errorMessage" label="连接提示">
                {{ errorMessage }}
              </el-descriptions-item>
            </el-descriptions>
          </template>
        </el-skeleton>
      </el-card>
    </el-main>
  </el-container>
</template>

<style scoped>
.layout {
  min-height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}

.brand {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: #409eff;
}

.subtitle {
  font-size: 14px;
  color: #909399;
}

.main {
  max-width: 960px;
  margin: 0 auto;
  width: 100%;
}

.welcome-card {
  margin-top: 24px;
}
</style>
