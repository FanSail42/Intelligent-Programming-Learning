<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCourses, type Course } from '@/api/course'
import {
  deleteMaterial,
  getMaterialStatus,
  listMaterials,
  retryMaterial,
  uploadMaterial,
  type Material,
} from '@/api/material'

const courses = ref<Course[]>([])
const selectedCourseId = ref<number | null>(null)
const materials = ref<Material[]>([])
const loading = ref(false)
const uploading = ref(false)
const pollingId = ref<number | null>(null)

async function loadCourses() {
  const page = await getCourses({ page_num: 1, page_size: 100 })
  courses.value = page.list
  if (page.list.length && !selectedCourseId.value) {
    selectedCourseId.value = page.list[0].id
    await loadMaterials()
  }
}

async function loadMaterials() {
  if (!selectedCourseId.value) return
  loading.value = true
  try {
    materials.value = await listMaterials(selectedCourseId.value)
  } finally {
    loading.value = false
  }
}

function statusTagType(status: string) {
  if (status === 'READY') return 'success'
  if (status === 'FAILED') return 'danger'
  return 'warning'
}

async function pollStatus(materialId: number) {
  pollingId.value = materialId
  const timer = setInterval(async () => {
    try {
      const st = await getMaterialStatus(materialId)
      const row = materials.value.find((m) => m.id === materialId)
      if (row) row.status = st.status
      if (st.status === 'READY' || st.status === 'FAILED') {
        clearInterval(timer)
        pollingId.value = null
        await loadMaterials()
      }
    } catch {
      clearInterval(timer)
      pollingId.value = null
    }
  }, 2000)
}

async function onFileChange(uploadFile: { raw?: File }) {
  if (!selectedCourseId.value || !uploadFile.raw) return
  uploading.value = true
  try {
    const result = await uploadMaterial(selectedCourseId.value, uploadFile.raw)
    ElMessage.success('上传成功，正在处理')
    await loadMaterials()
    pollStatus(result.material_id)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '上传失败')
  } finally {
    uploading.value = false
  }
}

async function onRetry(row: Material) {
  try {
    await retryMaterial(row.id)
    ElMessage.success('已重新提交处理')
    await loadMaterials()
    pollStatus(row.id)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '重试失败')
  }
}

async function onDelete(row: Material) {
  try {
    await ElMessageBox.confirm(
      `确定删除资料「${row.original_name}」？删除后无法恢复，向量数据将一并清除。`,
      '删除资料',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
    await deleteMaterial(row.id)
    ElMessage.success('已删除')
    await loadMaterials()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e instanceof Error ? e.message : '删除失败')
    }
  }
}

onMounted(loadCourses)
</script>

<template>
  <div>
    <div class="toolbar">
      <h3>课程资料</h3>
      <el-select
        v-model="selectedCourseId"
        placeholder="选择课程"
        style="width: 260px"
        @change="loadMaterials"
      >
        <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
    </div>

    <el-upload
      :auto-upload="false"
      :show-file-list="false"
      accept=".pdf,.txt,.md"
      :disabled="!selectedCourseId || uploading"
      @change="onFileChange"
    >
      <el-button type="primary" :loading="uploading">上传 PDF/TXT/MD</el-button>
    </el-upload>

    <el-table v-loading="loading" :data="materials" stripe class="table">
      <el-table-column prop="original_name" label="文件名" />
      <el-table-column prop="type" label="类型" width="80" />
      <el-table-column label="状态" width="140">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'FAILED'"
            link
            type="primary"
            @click="onRetry(row)"
          >
            重试
          </el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
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

.table {
  margin-top: 16px;
}
</style>
