<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getMyCourses, type Course } from '@/api/course'
import {
  getWrongBookStats,
  listWrongBook,
  updateWrongBookMastered,
  type WrongBookCategoryStat,
  type WrongBookItem,
  type WrongBookStats,
} from '@/api/learning'
import { languageLabel } from '@/constants/codeLanguages'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const items = ref<WrongBookItem[]>([])
const stats = ref<WrongBookStats | null>(null)
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(10)
const courses = ref<Course[]>([])
const filterCourseId = ref<number | undefined>()
const filterMastered = ref<boolean | undefined>()
const activeCategory = ref<string>('')

const SOURCE_LABELS: Record<string, string> = {
  code_submission: '代码讲解',
  chat_message: 'AI 对话',
}

const LEVEL_LABELS: Record<string, string> = {
  syntax: '语法',
  semantic: '语义',
  runtime: '运行',
}

const categoryTabs = computed(() => {
  const tabs: Array<{ key: string; label: string; count: number }> = [
    { key: '', label: '全部', count: stats.value?.summary.total ?? total.value },
  ]
  for (const cat of stats.value?.by_category ?? []) {
    tabs.push({ key: cat.category, label: cat.label, count: cat.total })
  }
  return tabs
})

const activeCategoryAnalysis = computed((): WrongBookCategoryStat | null => {
  if (!activeCategory.value || !stats.value) return null
  return stats.value.by_category.find((c) => c.category === activeCategory.value) ?? null
})

async function loadCourses() {
  try {
    const result = await getMyCourses({ page_num: 1, page_size: 50 })
    courses.value = result.list
  } catch {
    courses.value = []
  }
}

async function loadStats() {
  try {
    stats.value = await getWrongBookStats({
      course_id: filterCourseId.value,
      days: 30,
    })
  } catch {
    stats.value = null
  }
}

async function loadList() {
  loading.value = true
  try {
    const data = await listWrongBook({
      course_id: filterCourseId.value,
      mastered: filterMastered.value,
      category: activeCategory.value || undefined,
      page_num: pageNum.value,
      page_size: pageSize.value,
    })
    items.value = data.list
    total.value = data.total
  } catch (err: unknown) {
    items.value = []
    total.value = 0
    ElMessage.error(err instanceof Error ? err.message : '加载错题本失败')
  } finally {
    loading.value = false
  }
}

async function reloadAll() {
  await Promise.all([loadStats(), loadList()])
}

function handleSearch() {
  pageNum.value = 1
  reloadAll()
}

function handleReset() {
  filterCourseId.value = undefined
  filterMastered.value = undefined
  activeCategory.value = ''
  pageNum.value = 1
  reloadAll()
}

function onPageChange(page: number) {
  pageNum.value = page
  loadList()
}

function selectCategory(key: string) {
  activeCategory.value = key
  pageNum.value = 1
  loadList()
}

async function toggleMastered(row: WrongBookItem) {
  const next = !row.mastered
  try {
    await updateWrongBookMastered(row.id, next)
    row.mastered = next
    ElMessage.success(next ? '已标记掌握' : '已取消掌握')
    await loadStats()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '更新失败')
  }
}

function viewSource(row: WrongBookItem) {
  if (row.source_type === 'code_submission') {
    router.push({ path: '/student/code', query: { id: String(row.ref_id) } })
  } else {
    router.push('/student/chat')
  }
}

watch(filterCourseId, () => {
  /* 由查询按钮触发，避免重复请求 */
})

onMounted(async () => {
  const q = route.query.course_id
  if (typeof q === 'string' && q) {
    const parsed = Number(q)
    if (!Number.isNaN(parsed)) filterCourseId.value = parsed
  }
  await loadCourses()
  await reloadAll()
})
</script>

<template>
  <div class="wrong-book-page">
    <el-card shadow="never" class="filter-card">
      <template #header>
        <div class="filter-header">
          <span>错题本</span>
          <router-link to="/student/dashboard" class="dash-link">查看错题分析图表 →</router-link>
        </div>
      </template>

      <el-form inline class="filter-form">
        <el-form-item label="课程">
          <el-select
            v-model="filterCourseId"
            clearable
            placeholder="全部"
            style="width: 220px"
          >
            <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="掌握状态">
          <el-select
            v-model="filterMastered"
            clearable
            placeholder="全部"
            style="width: 140px"
          >
            <el-option label="未掌握" :value="false" />
            <el-option label="已掌握" :value="true" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="activeCategoryAnalysis" shadow="never" class="analysis-card">
      <template #header>
        <span>{{ activeCategoryAnalysis.label }} · 类别分析</span>
      </template>
      <p class="analysis-text">{{ activeCategoryAnalysis.analysis }}</p>
      <div v-if="activeCategoryAnalysis.sample_issues.length" class="sample-issues">
        <span class="sample-title">常见表现：</span>
        <el-tag
          v-for="(issue, idx) in activeCategoryAnalysis.sample_issues"
          :key="idx"
          type="danger"
          effect="plain"
          size="small"
          class="issue-tag"
        >
          {{ issue }}
        </el-tag>
      </div>
    </el-card>

    <el-card shadow="never">
      <div class="category-tabs">
        <el-check-tag
          v-for="tab in categoryTabs"
          :key="tab.key"
          :checked="activeCategory === tab.key"
          class="cat-tag"
          @click="selectCategory(tab.key)"
        >
          {{ tab.label }} ({{ tab.count }})
        </el-check-tag>
      </div>

      <el-table v-loading="loading" :data="items" stripe class="wrong-table">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-panel">
              <p v-if="row.review_tip" class="review-tip">
                <strong>复习建议：</strong>{{ row.review_tip }}
              </p>
              <p v-if="row.summary" class="summary-line">
                <strong>问题摘要：</strong>{{ row.summary }}
              </p>
              <div v-if="row.kp_name" class="meta-line">
                <strong>关联知识点：</strong>{{ row.kp_name }}
              </div>
              <div v-if="row.issues.length" class="issues-block">
                <strong>具体问题：</strong>
                <ul>
                  <li v-for="(issue, idx) in row.issues" :key="idx">
                    <el-tag size="small" type="info">{{ LEVEL_LABELS[issue.level] ?? issue.level }}</el-tag>
                    <span v-if="issue.line">第 {{ issue.line }} 行 · </span>
                    {{ issue.message }}
                    <span v-if="issue.explanation" class="explain">（{{ issue.explanation }}）</span>
                  </li>
                </ul>
              </div>
              <div v-if="row.suggestions.length" class="suggest-block">
                <strong>改进方向：</strong>
                <ul>
                  <li v-for="(s, idx) in row.suggestions" :key="idx">{{ s }}</li>
                </ul>
              </div>
              <p v-if="row.has_fixed_code" class="fixed-hint">
                可在「代码讲解」中查看 AI 给出的修正参考代码。
              </p>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="类别" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.category_label ?? '—' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="100">
          <template #default="{ row }">
            {{ SOURCE_LABELS[row.source_type] ?? row.source_type }}
          </template>
        </el-table-column>
        <el-table-column label="语言" width="80">
          <template #default="{ row }">
            {{ row.language ? languageLabel(row.language) : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" show-overflow-tooltip />
        <el-table-column label="掌握" width="90">
          <template #default="{ row }">
            <el-tag :type="row.mastered ? 'success' : 'warning'" size="small">
              {{ row.mastered ? '已掌握' : '未掌握' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="记录时间" width="170" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewSource(row)">查看</el-button>
            <el-button link type="primary" @click="toggleMastered(row)">
              {{ row.mastered ? '标为未掌握' : '标为已掌握' }}
            </el-button>
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

      <el-empty v-if="!loading && items.length === 0" description="暂无错题记录" />
    </el-card>
  </div>
</template>

<style scoped>
.wrong-book-page {
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-form {
  margin-bottom: 0;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.dash-link {
  font-size: 13px;
  color: #409eff;
  text-decoration: none;
}

.dash-link:hover {
  text-decoration: underline;
}

.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.cat-tag {
  cursor: pointer;
}

.analysis-card {
  border-left: 3px solid #409eff;
}

.analysis-text {
  margin: 0 0 8px;
  color: #606266;
  line-height: 1.6;
}

.sample-issues {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.sample-title {
  font-size: 13px;
  color: #909399;
}

.issue-tag {
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expand-panel {
  padding: 8px 16px 12px 48px;
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
}

.review-tip {
  color: #409eff;
  margin: 0 0 8px;
}

.summary-line,
.meta-line {
  margin: 0 0 8px;
}

.issues-block ul,
.suggest-block ul {
  margin: 6px 0 0;
  padding-left: 18px;
}

.explain {
  color: #909399;
}

.fixed-hint {
  margin: 8px 0 0;
  color: #67c23a;
}

.pager {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
</style>
