<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listAdminLogs, LOG_ACTION_LABELS, type OperationLogItem } from '@/api/admin'

const loading = ref(false)
const logs = ref<OperationLogItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(15)

const searchForm = reactive({
  action: '',
  username: '',
})

function buildParams() {
  const params: Record<string, string | number> = {
    page_num: page.value,
    page_size: pageSize.value,
  }
  if (searchForm.action) params.action = searchForm.action
  if (searchForm.username.trim()) params.username = searchForm.username.trim()
  return params
}

async function loadLogs() {
  loading.value = true
  try {
    const result = await listAdminLogs(buildParams())
    logs.value = result.list
    total.value = result.total
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载日志失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadLogs()
}

function handleReset() {
  searchForm.action = ''
  searchForm.username = ''
  page.value = 1
  loadLogs()
}

function handlePageChange(nextPage: number) {
  page.value = nextPage
  loadLogs()
}

function formatTime(iso: string): string {
  const dt = new Date(iso)
  if (Number.isNaN(dt.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`
}

onMounted(() => {
  loadLogs()
})
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1 class="title">操作日志</h1>
        <p class="subtitle">登录、账号变更等系统操作审计记录</p>
      </div>
    </header>

    <el-card shadow="never" class="search-card">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item label="操作类型">
          <el-select v-model="searchForm.action" placeholder="全部" clearable style="width: 160px">
            <el-option
              v-for="(label, key) in LOG_ACTION_LABELS"
              :key="key"
              :label="label"
              :value="key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="操作者">
          <el-input v-model="searchForm.username" placeholder="用户名模糊搜索" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" v-loading="loading">
      <el-table :data="logs" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="action_label" label="操作" width="120" />
        <el-table-column prop="username" label="操作者" width="120">
          <template #default="{ row }">{{ row.username || '—' }}</template>
        </el-table-column>
        <el-table-column prop="detail" label="详情" min-width="220" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="130">
          <template #default="{ row }">{{ row.ip || '—' }}</template>
        </el-table-column>
        <el-table-column label="时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="total"
          :current-page="page"
          :page-size="pageSize"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 16px;
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

.search-card {
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
