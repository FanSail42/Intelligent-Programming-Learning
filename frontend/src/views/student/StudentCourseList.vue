<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getMyCourses,
  leaveCourse,
  STATUS_LABELS,
  type Course,
  type MyCourseSearch,
} from '@/api/course'

const loading = ref(false)
const courses = ref<Course[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const leavingId = ref<number | null>(null)

const searchForm = reactive({
  name: '',
  teacher_name: '',
  status: '',
  publishedRange: [] as string[],
})

function buildSearchParams(): MyCourseSearch {
  const params: MyCourseSearch = {
    page_num: page.value,
    page_size: pageSize.value,
  }
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
    const result = await getMyCourses(buildSearchParams())
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

async function handleLeave(row: Course) {
  await ElMessageBox.confirm(`确定退选课程「${row.name}」？`, '退课确认', { type: 'warning' })
  leavingId.value = row.id
  try {
    await leaveCourse(row.id)
    ElMessage.success('退课成功')
    if (courses.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await loadCourses()
  } finally {
    leavingId.value = null
  }
}

onMounted(loadCourses)
</script>

<template>
  <div>
    <h3>我的课程</h3>

    <el-form :inline="true" class="search-form" @submit.prevent="handleSearch">
      <el-form-item label="课程名称">
        <el-input
          v-model="searchForm.name"
          placeholder="模糊搜索课程名"
          clearable
          style="width: 160px"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item label="授课教师">
        <el-input
          v-model="searchForm.teacher_name"
          placeholder="模糊搜索教师姓名"
          clearable
          style="width: 160px"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item label="课程状态">
        <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
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
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY/MM/DD"
          style="width: 260px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="courses" stripe empty-text="暂无课程，请前往「选课查询」选课">
      <el-table-column prop="id" label="课程 ID" width="90" />
      <el-table-column prop="name" label="课程名称" min-width="140" />
      <el-table-column prop="teacher_name" label="授课教师姓名" width="130" />
      <el-table-column label="课程状态" width="100">
        <template #default="{ row }">{{ STATUS_LABELS[row.status] || row.status }}</template>
      </el-table-column>
      <el-table-column prop="published_at" label="课程发布时间" width="180">
        <template #default="{ row }">{{ row.published_at || '-' }}</template>
      </el-table-column>
      <el-table-column prop="description" label="简介" show-overflow-tooltip min-width="120" />
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button
            link
            type="danger"
            :loading="leavingId === row.id"
            @click="handleLeave(row)"
          >
            退课
          </el-button>
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
  </div>
</template>

<style scoped>
.search-form {
  margin-bottom: 12px;
  padding: 12px 12px 0;
  background: #fff;
  border-radius: 4px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
