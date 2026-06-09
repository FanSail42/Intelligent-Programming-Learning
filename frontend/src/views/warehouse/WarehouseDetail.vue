<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { downloadMaterial } from '@/api/material'
import {
  assignMaterials,
  COURSE_SUBJECT_LABEL,
  getWarehouse,
  listAssignableMaterials,
  listWarehouseMaterials,
  unassignMaterials,
  type Warehouse,
  type WarehouseMaterial,
} from '@/api/warehouse'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const isAdmin = computed(() => auth.role === 'admin')
const warehouseId = computed(() => Number(route.params.id))

const warehouse = ref<Warehouse | null>(null)
const materials = ref<WarehouseMaterial[]>([])
const total = ref(0)
const loading = ref(false)
const downloadingId = ref<number | null>(null)
const selectedIds = ref<number[]>([])

const assignVisible = ref(false)
const assignLoading = ref(false)
const assignMaterials_ = ref<WarehouseMaterial[]>([])
const assignTotal = ref(0)
const assignSelected = ref<number[]>([])
const assignSearch = reactive({ material_name: '', course_name: '', page_num: 1, page_size: 10 })

const search = reactive({
  material_name: '',
  course_name: '',
  teacher_name: '',
  created_from: '',
  created_to: '',
  page_num: 1,
  page_size: 10,
})

const isCourseWarehouse = computed(() => warehouse.value?.warehouse_kind === 'course')

const warehouseSubtitle = computed(() => {
  if (!warehouse.value) return ''
  if (warehouse.value.warehouse_kind === 'course') {
    const sub = warehouse.value.course_subject
      ? COURSE_SUBJECT_LABEL[warehouse.value.course_subject] || warehouse.value.course_subject
      : '课程'
    return `${sub} 课程资料仓库 · 管理员手动分派 · 共 ${warehouse.value.material_count} 份`
  }
  return `${warehouse.value.material_type.toUpperCase()} 格式 · 共 ${warehouse.value.material_count} 份资料`
})

function statusTagType(status: string) {
  if (status === 'READY') return 'success'
  if (status === 'FAILED') return 'danger'
  return 'warning'
}

function formatDate(val: string) {
  if (!val) return ''
  return val.replace('T', ' ').slice(0, 19)
}

async function loadWarehouse() {
  warehouse.value = await getWarehouse(warehouseId.value)
}

async function loadMaterials() {
  loading.value = true
  try {
    const params: Record<string, string | number> = {
      page_num: search.page_num,
      page_size: search.page_size,
    }
    if (search.material_name.trim()) params.material_name = search.material_name.trim()
    if (search.course_name.trim()) params.course_name = search.course_name.trim()
    if (search.teacher_name.trim()) params.teacher_name = search.teacher_name.trim()
    if (search.created_from) params.created_from = search.created_from
    if (search.created_to) params.created_to = search.created_to

    const page = await listWarehouseMaterials(warehouseId.value, params)
    materials.value = page.list
    total.value = page.total
  } finally {
    loading.value = false
  }
}

async function loadAssignable() {
  assignLoading.value = true
  try {
    const params: Record<string, string | number> = {
      page_num: assignSearch.page_num,
      page_size: assignSearch.page_size,
    }
    if (assignSearch.material_name.trim()) params.material_name = assignSearch.material_name.trim()
    if (assignSearch.course_name.trim()) params.course_name = assignSearch.course_name.trim()

    const page = await listAssignableMaterials(warehouseId.value, params)
    assignMaterials_.value = page.list
    assignTotal.value = page.total
  } finally {
    assignLoading.value = false
  }
}

function onSearch() {
  search.page_num = 1
  loadMaterials()
}

function onReset() {
  search.material_name = ''
  search.course_name = ''
  search.teacher_name = ''
  search.created_from = ''
  search.created_to = ''
  search.page_num = 1
  loadMaterials()
}

function onPageChange(page: number) {
  search.page_num = page
  loadMaterials()
}

function onSizeChange(size: number) {
  search.page_size = size
  search.page_num = 1
  loadMaterials()
}

function goBack() {
  router.push('/teacher/warehouses')
}

function openAssign() {
  assignSelected.value = []
  assignSearch.material_name = ''
  assignSearch.course_name = ''
  assignSearch.page_num = 1
  assignVisible.value = true
  loadAssignable()
}

async function confirmAssign() {
  if (!assignSelected.value.length) {
    ElMessage.warning('请选择要分派的资料')
    return
  }
  try {
    await assignMaterials(warehouseId.value, assignSelected.value)
    ElMessage.success(`已分派 ${assignSelected.value.length} 份资料`)
    assignVisible.value = false
    await loadWarehouse()
    await loadMaterials()
  } catch {
    // handled
  }
}

async function onUnassign() {
  if (!selectedIds.value.length) return
  try {
    await ElMessageBox.confirm(
      `确定将选中的 ${selectedIds.value.length} 份资料移出本仓库？移出后将归还对应格式仓库。`,
      '移出资料',
      { type: 'warning', confirmButtonText: '移出', cancelButtonText: '取消' },
    )
    await unassignMaterials(warehouseId.value, selectedIds.value)
    ElMessage.success('已移出，资料已归还格式仓库')
    selectedIds.value = []
    await loadWarehouse()
    await loadMaterials()
  } catch {
    // cancel
  }
}

function onSelectionChange(rows: WarehouseMaterial[]) {
  selectedIds.value = rows.map((r) => r.id)
}

async function onDownload(row: WarehouseMaterial) {
  downloadingId.value = row.id
  try {
    await downloadMaterial(row.id, row.original_name)
    ElMessage.success('已开始下载')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '下载失败')
  } finally {
    downloadingId.value = null
  }
}

async function init() {
  try {
    await loadWarehouse()
    await loadMaterials()
  } catch {
    ElMessage.error('仓库不存在或无权访问')
    goBack()
  }
}

watch(warehouseId, () => {
  if (warehouseId.value) init()
})

onMounted(init)
</script>

<template>
  <div class="detail-page">
    <div class="detail-header">
      <el-button link type="primary" @click="goBack">← 返回仓库列表</el-button>
      <div v-if="warehouse" class="warehouse-info" :style="{ '--wh-color': warehouse.color }">
        <span class="wh-icon">{{ warehouse.icon }}</span>
        <div class="info-main">
          <h2>{{ warehouse.name }}</h2>
          <p>{{ warehouseSubtitle }}</p>
          <p v-if="warehouse.description" class="wh-desc">{{ warehouse.description }}</p>
          <el-tag v-if="isCourseWarehouse" type="warning" size="small">手动分派</el-tag>
        </div>
        <div v-if="isAdmin && isCourseWarehouse" class="info-actions">
          <el-button type="primary" @click="openAssign">分派资料</el-button>
          <el-button :disabled="!selectedIds.length" @click="onUnassign">移出仓库</el-button>
        </div>
      </div>
    </div>

    <el-card class="search-card" shadow="never">
      <el-form :inline="true" @submit.prevent="onSearch">
        <el-form-item label="资料名称">
          <el-input
            v-model="search.material_name"
            placeholder="模糊搜索"
            clearable
            style="width: 150px"
          />
        </el-form-item>
        <el-form-item label="课程名称">
          <el-input
            v-model="search.course_name"
            placeholder="模糊搜索"
            clearable
            style="width: 150px"
          />
        </el-form-item>
        <el-form-item label="上传教师">
          <el-input
            v-model="search.teacher_name"
            placeholder="模糊搜索"
            clearable
            style="width: 130px"
          />
        </el-form-item>
        <el-form-item label="上传时间">
          <el-date-picker
            v-model="search.created_from"
            type="date"
            placeholder="开始"
            value-format="YYYY-MM-DD"
            style="width: 130px"
          />
          <span class="date-sep">至</span>
          <el-date-picker
            v-model="search.created_to"
            type="date"
            placeholder="结束"
            value-format="YYYY-MM-DD"
            style="width: 130px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">查询</el-button>
          <el-button @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table
      v-loading="loading"
      :data="materials"
      stripe
      class="material-table"
      @selection-change="onSelectionChange"
    >
      <el-table-column v-if="isAdmin && isCourseWarehouse" type="selection" width="48" />
      <el-table-column prop="original_name" label="资料名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="course_name" label="所属课程" min-width="140" show-overflow-tooltip />
      <el-table-column prop="uploader_name" label="上传教师" width="110" />
      <el-table-column prop="type" label="类型" width="70" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="上传时间" width="165">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            :loading="downloadingId === row.id"
            @click="onDownload(row)"
          >
            下载
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="search.page_num"
        v-model:page-size="search.page_size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        background
        @current-change="onPageChange"
        @size-change="onSizeChange"
      />
    </div>

    <el-dialog v-model="assignVisible" title="分派资料到本仓库" width="720px">
      <el-form :inline="true" @submit.prevent="loadAssignable">
        <el-form-item label="资料名称">
          <el-input v-model="assignSearch.material_name" placeholder="模糊搜索" clearable />
        </el-form-item>
        <el-form-item label="课程名称">
          <el-input v-model="assignSearch.course_name" placeholder="模糊搜索" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadAssignable">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="assignLoading"
        :data="assignMaterials_"
        max-height="360"
        @selection-change="(rows: WarehouseMaterial[]) => (assignSelected = rows.map((r) => r.id))"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="original_name" label="资料名称" show-overflow-tooltip />
        <el-table-column prop="course_name" label="课程" show-overflow-tooltip />
        <el-table-column prop="uploader_name" label="上传教师" width="100" />
        <el-table-column prop="type" label="类型" width="70" />
      </el-table>

      <div class="assign-pagination">
        <el-pagination
          v-model:current-page="assignSearch.page_num"
          :page-size="assignSearch.page_size"
          :total="assignTotal"
          layout="total, prev, pager, next"
          small
          background
          @current-change="loadAssignable"
        />
      </div>

      <template #footer>
        <el-button @click="assignVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!assignSelected.length" @click="confirmAssign">
          分派选中（{{ assignSelected.length }}）
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.detail-page {
  padding: 4px;
}

.detail-header {
  margin-bottom: 16px;
}

.warehouse-info {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-top: 12px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 8px;
  border-left: 4px solid var(--wh-color, #409eff);
}

.wh-icon {
  font-size: 48px;
  line-height: 1;
}

.info-main {
  flex: 1;
}

.info-main h2 {
  margin: 0 0 6px;
  font-size: 20px;
}

.info-main p {
  margin: 0 0 4px;
  color: #606266;
  font-size: 14px;
}

.wh-desc {
  color: #909399 !important;
}

.info-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-card {
  margin-bottom: 16px;
}

.date-sep {
  margin: 0 8px;
  color: #909399;
}

.material-table {
  background: #fff;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.assign-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
