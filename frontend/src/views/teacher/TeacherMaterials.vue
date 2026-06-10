<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCourses, type Course } from '@/api/course'
import {
  deleteMaterial,
  getMaterialStatus,
  listMaterials,
  MATERIAL_DUPLICATE_CODE,
  MaterialUploadError,
  MAX_UPLOAD_BYTES,
  retryMaterial,
  uploadMaterial,
  type Material,
} from '@/api/material'

const courses = ref<Course[]>([])
const selectedCourseId = ref<number | null>(null)
const materials = ref<Material[]>([])
const loading = ref(false)
const uploadingCount = ref(0)
const processingIds = ref<Set<number>>(new Set())

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
  processingIds.value.add(materialId)
  let intervalMs = 2000

  const tick = async () => {
    if (!processingIds.value.has(materialId)) return
    try {
      const st = await getMaterialStatus(materialId)
      const row = materials.value.find((m) => m.id === materialId)
      if (row) row.status = st.status
      if (st.status === 'READY' || st.status === 'FAILED') {
        processingIds.value.delete(materialId)
        await loadMaterials()
        if (st.status === 'FAILED' && st.error_message) {
          ElMessage.error(`资料处理失败：${st.error_message}`)
        }
        return
      }
      intervalMs = Math.min(intervalMs + 1000, 5000)
      setTimeout(tick, intervalMs)
    } catch {
      processingIds.value.delete(materialId)
    }
  }

  setTimeout(tick, intervalMs)
}

function validateBeforeUpload(file: File): string | null {
  const name = file.name.toLowerCase()
  const allowed = ['.pdf', '.txt', '.md', '.pptx']
  if (!allowed.some((ext) => name.endsWith(ext))) {
    return '仅支持 pdf、txt、md、pptx 文件；PPT 请另存为 .pptx 后上传'
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return '文件大小不能超过 10MB'
  }
  if (file.size === 0) {
    return '文件为空，请选择有效文件'
  }
  return null
}

async function onFileChange(uploadFile: { raw?: File }) {
  if (!selectedCourseId.value || !uploadFile.raw) return

  const validationError = validateBeforeUpload(uploadFile.raw)
  if (validationError) {
    ElMessage.warning(validationError)
    return
  }

  uploadingCount.value += 1
  try {
    const result = await uploadMaterial(selectedCourseId.value, uploadFile.raw)
    if (result.linked) {
      ElMessage.success('已关联已有同名资料到本课程，无需重复上传')
    } else {
      ElMessage.success('上传成功，正在后台处理（可继续上传其他文件）')
    }
    materials.value.unshift({
      id: result.material_id,
      course_id: selectedCourseId.value,
      type: uploadFile.raw.name.split('.').pop()?.toLowerCase() || '',
      original_name: uploadFile.raw.name,
      status: 'UPLOADED',
      version: 1,
      error_message: null,
      created_at: new Date().toISOString(),
    })
    pollStatus(result.material_id)
    void loadMaterials()
  } catch (e) {
    if (e instanceof MaterialUploadError && e.code === MATERIAL_DUPLICATE_CODE) {
      await ElMessageBox.alert(
        e.message,
        '资料已存在',
        { type: 'warning', confirmButtonText: '我知道了' },
      )
    } else {
      ElMessage.error(e instanceof Error ? e.message : '上传失败，请重新上传')
    }
  } finally {
    uploadingCount.value = Math.max(0, uploadingCount.value - 1)
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
      accept=".pdf,.txt,.md,.pptx"
      :disabled="!selectedCourseId"
      @change="onFileChange"
    >
      <el-button type="primary" :loading="uploadingCount > 0">上传 PDF/TXT/MD/PPTX</el-button>
    </el-upload>
    <p class="hint">单文件不超过 10MB；同名资料在同一课程不可重复上传，跨课程将自动关联已有文件</p>

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

.hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #718096;
}

.table {
  margin-top: 16px;
}
</style>
