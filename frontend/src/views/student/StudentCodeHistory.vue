<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listCodeSubmissions, type SubmissionListItem } from '@/api/code'
import { languageLabel } from '@/constants/codeLanguages'

const router = useRouter()
const loading = ref(false)
const history = ref<SubmissionListItem[]>([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)

async function loadHistory() {
  loading.value = true
  try {
    const data = await listCodeSubmissions(pageNum.value, pageSize.value)
    history.value = data.list
    total.value = data.total
  } catch (err: unknown) {
    history.value = []
    total.value = 0
    const msg = err instanceof Error ? err.message : '加载提交历史失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/student/code')
}

function viewDetail(row: SubmissionListItem) {
  router.push({ path: '/student/code', query: { id: String(row.id) } })
}

function onPageChange(page: number) {
  pageNum.value = page
  loadHistory()
}

onMounted(loadHistory)
</script>

<template>
  <div class="history-page">
    <el-card shadow="never">
      <template #header>
        <div class="header-row">
          <span>提交历史</span>
          <el-button link type="primary" @click="goBack">返回代码讲解</el-button>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="history"
        size="default"
        stripe
        @row-click="viewDetail"
      >
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column label="语言" width="100">
          <template #default="{ row }">
            {{ languageLabel(row.language) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="summary" label="摘要" show-overflow-tooltip />
        <el-table-column prop="created_at" label="提交时间" width="180" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="viewDetail(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="total > pageSize" class="pager">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="pageNum"
          @current-change="onPageChange"
        />
      </div>

      <el-empty v-if="!loading && history.length === 0" description="暂无提交记录" />
    </el-card>
  </div>
</template>

<style scoped>
.history-page {
  max-width: 1100px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.history-page :deep(.el-table__row) {
  cursor: pointer;
}

.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
