<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createAdminUser,
  deleteAdminUser,
  listAdminUsers,
  STATUS_LABELS,
  updateAdminUser,
  type AdminUser,
} from '@/api/admin'

const props = defineProps<{
  role: 'student' | 'teacher'
  title: string
  subtitle: string
  createLabel: string
}>()

const loading = ref(false)
const users = ref<AdminUser[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const resetDialogVisible = ref(false)
const editing = ref<AdminUser | null>(null)

const searchForm = reactive({
  username: '',
  status: '' as '' | 'active' | 'disabled',
})

const createForm = reactive({
  username: '',
  password: '',
})

const resetForm = reactive({
  password: '',
})

function buildSearchParams() {
  const params: Record<string, string | number> = {
    role: props.role,
    page_num: page.value,
    page_size: pageSize.value,
  }
  if (searchForm.username.trim()) params.username = searchForm.username.trim()
  if (searchForm.status) params.status = searchForm.status
  return params
}

async function loadUsers() {
  loading.value = true
  try {
    const result = await listAdminUsers(buildSearchParams())
    users.value = result.list
    total.value = result.total
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载账号列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadUsers()
}

function handleReset() {
  searchForm.username = ''
  searchForm.status = ''
  page.value = 1
  loadUsers()
}

function handlePageChange(nextPage: number) {
  page.value = nextPage
  loadUsers()
}

function openCreateDialog() {
  createForm.username = ''
  createForm.password = ''
  dialogVisible.value = true
}

async function submitCreate() {
  if (!createForm.username.trim() || createForm.password.length < 6) {
    ElMessage.warning('请填写用户名（≥3 字符）和至少 6 位密码')
    return
  }
  try {
    await createAdminUser({
      username: createForm.username.trim(),
      password: createForm.password,
      role: props.role,
    })
    ElMessage.success('账号创建成功')
    dialogVisible.value = false
    await loadUsers()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '创建失败')
  }
}

async function toggleStatus(row: AdminUser) {
  const nextStatus = row.status === 'active' ? 'disabled' : 'active'
  const action = nextStatus === 'disabled' ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定${action}账号「${row.username}」吗？`, '提示', {
      type: 'warning',
    })
    await updateAdminUser(row.id, { status: nextStatus }, props.role)
    ElMessage.success(`已${action}`)
    await loadUsers()
  } catch (err: unknown) {
    if (err === 'cancel' || err === 'close') return
    ElMessage.error(err instanceof Error ? err.message : `${action}失败`)
  }
}

function openResetDialog(row: AdminUser) {
  editing.value = row
  resetForm.password = ''
  resetDialogVisible.value = true
}

async function submitResetPassword() {
  if (!editing.value) return
  if (resetForm.password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  try {
    await updateAdminUser(editing.value.id, { password: resetForm.password }, props.role)
    ElMessage.success('密码已重置')
    resetDialogVisible.value = false
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '重置失败')
  }
}

async function handleDelete(row: AdminUser) {
  try {
    await ElMessageBox.confirm(
      `确定删除账号「${row.username}」吗？删除后不可恢复登录。`,
      '删除确认',
      { type: 'warning' },
    )
    await deleteAdminUser(row.id, props.role)
    ElMessage.success('已删除')
    await loadUsers()
  } catch (err: unknown) {
    if (err === 'cancel' || err === 'close') return
    ElMessage.error(err instanceof Error ? err.message : '删除失败')
  }
}

function formatTime(iso: string): string {
  const dt = new Date(iso)
  if (Number.isNaN(dt.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1 class="title">{{ title }}</h1>
        <p class="subtitle">{{ subtitle }}</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">{{ createLabel }}</el-button>
    </header>

    <el-card shadow="never" class="search-card">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item label="用户名">
          <el-input v-model="searchForm.username" placeholder="模糊搜索" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="正常" value="active" />
            <el-option label="已禁用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" v-loading="loading">
      <el-table :data="users" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="160" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" effect="plain">
              {{ STATUS_LABELS[row.status] ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="160">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="toggleStatus(row)">
              {{ row.status === 'active' ? '禁用' : '启用' }}
            </el-button>
            <el-button link type="primary" @click="openResetDialog(row)">重置密码</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
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

    <el-dialog v-model="dialogVisible" :title="createLabel" width="480px" destroy-on-close>
      <el-form label-width="88px">
        <el-form-item label="用户名" required>
          <el-input v-model="createForm.username" placeholder="3～64 字符" maxlength="64" />
        </el-form-item>
        <el-form-item label="初始密码" required>
          <el-input
            v-model="createForm.password"
            type="password"
            show-password
            placeholder="至少 6 位"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="resetDialogVisible"
      :title="`重置密码 · ${editing?.username ?? ''}`"
      width="420px"
      destroy-on-close
    >
      <el-form label-width="88px">
        <el-form-item label="新密码" required>
          <el-input
            v-model="resetForm.password"
            type="password"
            show-password
            placeholder="至少 6 位"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitResetPassword">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
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
