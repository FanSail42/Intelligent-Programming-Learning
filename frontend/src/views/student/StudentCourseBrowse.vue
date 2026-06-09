<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  browseCourses,
  joinCourse,
  type BrowseCourse,
  type BrowseCourseSearch,
} from '@/api/course'

const loading = ref(false)
const courses = ref<BrowseCourse[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const joiningId = ref<number | null>(null)

const searchForm = reactive({
  course_id: '',
  name: '',
  teacher_name: '',
  publishedRange: [] as string[],
})

function buildSearchParams(): BrowseCourseSearch {
  const params: BrowseCourseSearch = {
    page_num: page.value,
    page_size: pageSize.value,
  }
  if (searchForm.course_id.trim()) params.course_id = searchForm.course_id.trim()
  if (searchForm.name.trim()) params.name = searchForm.name.trim()
  if (searchForm.teacher_name.trim()) params.teacher_name = searchForm.teacher_name.trim()
  if (searchForm.publishedRange.length === 2) {
    params.published_from = searchForm.publishedRange[0]
    params.published_to = searchForm.publishedRange[1]
  }
  return params
}

async function loadCourses() {
  loading.value = true
  try {
    const result = await browseCourses(buildSearchParams())
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
  searchForm.publishedRange = []
  page.value = 1
  loadCourses()
}

function handlePageChange(nextPage: number) {
  page.value = nextPage
  loadCourses()
}

async function handleJoin(row: BrowseCourse) {
  if (row.enrolled) return
  joiningId.value = row.id
  try {
    await joinCourse(row.id)
    ElMessage.success('选课成功')
    row.enrolled = true
  } finally {
    joiningId.value = null
  }
}

onMounted(loadCourses)
</script>

<template>
  <div>
    <h3>选课查询</h3>
    <p class="tip">搜索已发布且通过审核的课程，可直接选课</p>

    <el-form :inline="true" class="search-form" @submit.prevent="handleSearch">
      <el-form-item label="课程 ID">
        <el-input
          v-model="searchForm.course_id"
          placeholder="模糊搜索课程 ID"
          clearable
          style="width: 140px"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
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

    <el-table
      v-loading="loading"
      :data="courses"
      stripe
      empty-text="未找到符合条件的已发布课程"
    >
      <el-table-column prop="id" label="课程 ID" width="90" />
      <el-table-column prop="name" label="课程名称" min-width="140" />
      <el-table-column prop="teacher_name" label="授课教师姓名" width="130" />
      <el-table-column prop="published_at" label="课程发布时间" width="180">
        <template #default="{ row }">{{ row.published_at || '-' }}</template>
      </el-table-column>
      <el-table-column prop="description" label="简介" show-overflow-tooltip min-width="120" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.enrolled" link type="info" disabled>已选</el-button>
          <el-button
            v-else
            link
            type="primary"
            :loading="joiningId === row.id"
            @click="handleJoin(row)"
          >
            选课
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

.tip {
  color: #909399;
  font-size: 13px;
  margin: 0 0 12px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
