<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  approveCreateCourse,
  approvePublishCourse,
  createCourse,
  CREATE_APPROVAL_LABELS,
  deleteCourse,
  getCourses,
  getTeachers,
  PUBLISH_APPROVAL_LABELS,
  requestPublishCourse,
  STATUS_LABELS,
  updateCourse,
  type Course,
  type TeacherOption,
} from '@/api/course'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const isAdmin = computed(() => auth.role === 'admin')
const isTeacher = computed(() => auth.role === 'teacher')

const loading = ref(false)
const courses = ref<Course[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const teachers = ref<TeacherOption[]>([])
const dialogVisible = ref(false)
const editing = ref<Course | null>(null)
const showPendingOnly = ref(false)

const searchForm = reactive({
  course_id: '',
  name: '',
  teacher_name: '',
  status: '',
  publishedRange: [] as string[],
})

const form = reactive({
  name: '',
  description: '',
  status: 'draft',
  teacher_id: null as number | null,
})

function buildSearchParams() {
  const params: Record<string, string | number | boolean> = {
    page_num: page.value,
    page_size: pageSize.value,
  }
  if (isAdmin.value && showPendingOnly.value) params.pending_only = true
  if (searchForm.course_id.trim()) params.course_id = searchForm.course_id.trim()
  if (searchForm.name.trim()) params.name = searchForm.name.trim()
  if (searchForm.teacher_name.trim()) params.teacher_name = searchForm.teacher_name.trim()
  if (searchForm.status) params.status = searchForm.status
  if (searchForm.publishedRange.length === 2) {
    params.published_from = searchForm.publishedRange[0]
    params.published_to = searchForm.publishedRange[1]
  }
  return params
}

async function loadCourses() {
  loading.value = true
  try {
    const result = await getCourses(buildSearchParams())
    courses.value = result.list
    total.value = result.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadCourses()
}

function handleReset() {
  searchForm.course_id = ''
  searchForm.name = ''
  searchForm.teacher_name = ''
  searchForm.status = ''
  searchForm.publishedRange = []
  page.value = 1
  loadCourses()
}

function handlePageChange(nextPage: number) {
  page.value = nextPage
  loadCourses()
}

function handlePendingToggle() {
  page.value = 1
  loadCourses()
}

async function loadTeachers() {
  if (!isAdmin.value) return
  teachers.value = await getTeachers()
}

function openCreate() {
  editing.value = null
  form.name = ''
  form.description = ''
  form.status = 'draft'
  form.teacher_id = teachers.value[0]?.id ?? null
  dialogVisible.value = true
}

function openEdit(row: Course) {
  editing.value = row
  form.name = row.name
  form.description = row.description || ''
  form.status = row.status
  dialogVisible.value = true
}

function canEdit(row: Course) {
  if (isAdmin.value) return true
  return row.create_approval !== 'rejected'
}

function canRequestPublish(row: Course) {
  return (
    isTeacher.value &&
    row.create_approval === 'approved' &&
    row.status !== 'published' &&
    row.publish_approval !== 'pending'
  )
}

async function submitForm() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入课程名称')
    return
  }
  if (isAdmin.value && !editing.value && !form.teacher_id) {
    ElMessage.warning('请选择授课教师')
    return
  }
  try {
    if (editing.value) {
      await updateCourse(editing.value.id, {
        name: form.name,
        description: form.description,
        status: form.status,
      })
      ElMessage.success('已更新')
    } else {
      await createCourse({
        name: form.name,
        description: form.description,
        status: form.status,
        ...(isAdmin.value ? { teacher_id: form.teacher_id! } : {}),
      })
      ElMessage.success(isTeacher.value ? '已提交审核' : '已创建')
    }
    dialogVisible.value = false
    await loadCourses()
  } catch {
    // error toast handled by request interceptor
  }
}

async function handleDelete(row: Course) {
  await ElMessageBox.confirm(
    `确定删除课程「${row.name}」？删除后无法恢复。`,
    '删除课程',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
  )
  await deleteCourse(row.id)
  ElMessage.success('已删除')
  await loadCourses()
}

async function handleRequestPublish(row: Course) {
  await ElMessageBox.confirm(`确定申请发布课程「${row.name}」？`, '申请发布', { type: 'info' })
  await requestPublishCourse(row.id)
  ElMessage.success('发布申请已提交')
  await loadCourses()
}

async function handleApproveCreate(row: Course, approved: boolean) {
  const action = approved ? '通过' : '驳回'
  await ElMessageBox.confirm(`确定${action}课程「${row.name}」的新建申请？`, '新建审核', {
    type: approved ? 'success' : 'warning',
  })
  await approveCreateCourse(row.id, approved)
  ElMessage.success(`新建审核已${action}`)
  await loadCourses()
}

async function handleApprovePublish(row: Course, approved: boolean) {
  const action = approved ? '通过' : '驳回'
  await ElMessageBox.confirm(`确定${action}课程「${row.name}」的发布申请？`, '发布审核', {
    type: approved ? 'success' : 'warning',
  })
  await approvePublishCourse(row.id, approved)
  ElMessage.success(`发布审核已${action}`)
  await loadCourses()
}

async function publishDirect(row: Course) {
  await updateCourse(row.id, { status: 'published' })
  ElMessage.success('已发布')
  await loadCourses()
}

onMounted(async () => {
  await Promise.all([loadCourses(), loadTeachers()])
})
</script>

<template>
  <div>
    <div class="toolbar">
      <h3>课程管理</h3>
      <div class="toolbar-actions">
        <el-switch
          v-if="isAdmin"
          v-model="showPendingOnly"
          active-text="仅待审核"
          inactive-text="全部"
          @change="handlePendingToggle"
        />
        <el-button type="primary" @click="openCreate">新建课程</el-button>
      </div>
    </div>

    <el-form :inline="true" class="search-form" @submit.prevent="handleSearch">
      <el-form-item label="课程 ID">
        <el-input
          v-model="searchForm.course_id"
          placeholder="模糊搜索"
          clearable
          style="width: 120px"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item label="课程名称">
        <el-input
          v-model="searchForm.name"
          placeholder="模糊搜索"
          clearable
          style="width: 140px"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item v-if="isAdmin" label="授课教师">
        <el-input
          v-model="searchForm.teacher_name"
          placeholder="模糊搜索"
          clearable
          style="width: 120px"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item label="课程状态">
        <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 110px">
          <el-option label="已发布" value="published" />
          <el-option label="草稿" value="draft" />
          <el-option label="已归档" value="archived" />
        </el-select>
      </el-form-item>
      <el-form-item label="发布时间">
        <el-date-picker
          v-model="searchForm.publishedRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始"
          end-placeholder="结束"
          value-format="YYYY/MM/DD"
          style="width: 240px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="courses" stripe empty-text="暂无课程或调整搜索条件">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="课程名称" min-width="140" />
      <el-table-column prop="teacher_name" label="授课教师姓名" width="130" />
      <el-table-column label="课程状态" width="100">
        <template #default="{ row }">{{ STATUS_LABELS[row.status] || row.status }}</template>
      </el-table-column>
      <el-table-column label="新建审核" width="100">
        <template #default="{ row }">
          {{ CREATE_APPROVAL_LABELS[row.create_approval] || row.create_approval }}
        </template>
      </el-table-column>
      <el-table-column label="发布审核" width="100">
        <template #default="{ row }">
          {{ PUBLISH_APPROVAL_LABELS[row.publish_approval] || row.publish_approval }}
        </template>
      </el-table-column>
      <el-table-column prop="published_at" label="课程发布时间" width="180">
        <template #default="{ row }">{{ row.published_at || '-' }}</template>
      </el-table-column>
      <el-table-column prop="description" label="简介" show-overflow-tooltip min-width="120" />
      <el-table-column label="操作" width="320" fixed="right">
        <template #default="{ row }">
          <el-button v-if="canEdit(row)" link type="primary" @click="openEdit(row)">编辑</el-button>

          <template v-if="isTeacher && row.create_approval === 'pending'">
            <el-tag size="small" type="warning">新建审核中</el-tag>
          </template>

          <el-button
            v-if="canRequestPublish(row)"
            link
            type="success"
            @click="handleRequestPublish(row)"
          >
            申请发布
          </el-button>
          <el-tag
            v-else-if="isTeacher && row.publish_approval === 'pending'"
            size="small"
            type="warning"
          >
            发布审核中
          </el-tag>

          <template v-if="isAdmin && row.create_approval === 'pending'">
            <el-button link type="success" @click="handleApproveCreate(row, true)">通过新建</el-button>
            <el-button link type="warning" @click="handleApproveCreate(row, false)">驳回新建</el-button>
          </template>

          <template v-if="isAdmin && row.publish_approval === 'pending'">
            <el-button link type="success" @click="handleApprovePublish(row, true)">通过发布</el-button>
            <el-button link type="warning" @click="handleApprovePublish(row, false)">驳回发布</el-button>
          </template>

          <el-button
            v-if="isAdmin && row.status !== 'published' && row.create_approval === 'approved' && row.publish_approval !== 'pending'"
            link
            type="success"
            @click="publishDirect(row)"
          >
            直接发布
          </el-button>

          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="total > pageSize" class="pagination">
      <el-pagination
        background
        layout="prev, pager, next, total"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="handlePageChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑课程' : '新建课程'" width="480px">
      <el-form label-width="90px">
        <el-form-item v-if="isAdmin && !editing" label="授课教师">
          <el-select v-model="form.teacher_id" placeholder="请选择教师" style="width: 100%">
            <el-option
              v-for="t in teachers"
              :key="t.id"
              :label="t.username"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item v-if="isAdmin" label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-alert
          v-if="isTeacher && !editing"
          title="教师新建课程需管理员审核通过后生效"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.toolbar h3 {
  margin: 0;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.search-form {
  margin-bottom: 12px;
  padding: 12px 12px 0;
  background: #fff;
  border-radius: 4px;
}
</style>
