<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  COURSE_SUBJECT_LABEL,
  createWarehouse,
  deleteWarehouse,
  listWarehouses,
  updateWarehouse,
  type Warehouse,
} from '@/api/warehouse'

const router = useRouter()
const auth = useAuthStore()
const isAdmin = computed(() => auth.role === 'admin')

const warehouses = ref<Warehouse[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)

const fileTypeWarehouses = computed(() =>
  warehouses.value.filter((w) => w.warehouse_kind === 'file_type'),
)
const courseWarehouses = computed(() =>
  warehouses.value.filter((w) => w.warehouse_kind === 'course'),
)

const form = reactive({
  name: '',
  description: '',
  warehouse_kind: 'file_type' as 'file_type' | 'course',
  course_subject: 'python',
  material_type: 'pdf',
  icon: '📦',
  color: '#409eff',
  sort_order: 0,
})

const typeOptions = [
  { label: 'PDF', value: 'pdf', icon: '📕', color: '#e74c3c' },
  { label: 'TXT', value: 'txt', icon: '📄', color: '#3498db' },
  { label: 'MD', value: 'md', icon: '📝', color: '#2ecc71' },
  { label: 'PPTX', value: 'pptx', icon: '📊', color: '#9b59b6' },
]

const subjectOptions = [
  { label: 'Python', value: 'python', icon: '🐍', color: '#3776ab' },
  { label: 'Java', value: 'java', icon: '☕', color: '#f89820' },
  { label: 'C/C++', value: 'cpp', icon: '⚙️', color: '#00599c' },
]

function warehouseLabel(wh: Warehouse) {
  if (wh.warehouse_kind === 'course' && wh.course_subject) {
    return `${COURSE_SUBJECT_LABEL[wh.course_subject] || wh.course_subject} 课程`
  }
  return `${wh.material_type.toUpperCase()} 格式`
}

function resetForm() {
  form.name = ''
  form.description = ''
  form.warehouse_kind = 'file_type'
  form.course_subject = 'python'
  form.material_type = 'pdf'
  form.icon = '📦'
  form.color = '#409eff'
  form.sort_order = 0
  editingId.value = null
}

async function loadWarehouses() {
  loading.value = true
  try {
    warehouses.value = await listWarehouses()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(wh: Warehouse) {
  editingId.value = wh.id
  form.name = wh.name
  form.description = wh.description || ''
  form.warehouse_kind = wh.warehouse_kind
  form.course_subject = wh.course_subject || 'python'
  form.material_type = wh.material_type
  form.icon = wh.icon
  form.color = wh.color
  form.sort_order = wh.sort_order
  dialogVisible.value = true
}

async function onSubmit() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入仓库名称')
    return
  }
  try {
    const payload = { ...form }
    if (editingId.value) {
      await updateWarehouse(editingId.value, payload)
      ElMessage.success('仓库已更新')
    } else {
      await createWarehouse(payload)
      ElMessage.success('仓库已创建')
    }
    dialogVisible.value = false
    await loadWarehouses()
  } catch {
    // handled by interceptor
  }
}

async function onDelete(wh: Warehouse) {
  try {
    await ElMessageBox.confirm(
      `确定删除仓库「${wh.name}」？若仓内仍有资料将无法删除。`,
      '删除仓库',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
    await deleteWarehouse(wh.id)
    ElMessage.success('已删除')
    await loadWarehouses()
  } catch {
    // cancel or error
  }
}

function enterWarehouse(wh: Warehouse) {
  router.push(`/teacher/warehouses/${wh.id}`)
}

function onTypeChange(val: string) {
  const opt = typeOptions.find((o) => o.value === val)
  if (opt) {
    form.icon = opt.icon
    form.color = opt.color
  }
}

function onSubjectChange(val: string) {
  const opt = subjectOptions.find((o) => o.value === val)
  if (opt) {
    form.icon = opt.icon
    form.color = opt.color
  }
}

onMounted(loadWarehouses)
</script>

<template>
  <div class="warehouse-page">
    <div class="page-header">
      <div>
        <h2>资料仓库</h2>
        <p class="subtitle">格式仓库自动归集上传资料；课程仓库由管理员手动分派</p>
      </div>
      <el-button v-if="isAdmin" type="primary" @click="openCreate">新建仓库</el-button>
    </div>

    <section v-loading="loading" class="warehouse-section">
      <h3 class="section-title">格式资料仓库</h3>
      <div class="warehouse-grid">
        <div
          v-for="wh in fileTypeWarehouses"
          :key="wh.id"
          class="warehouse-block"
          :style="{ '--wh-color': wh.color }"
          @click="enterWarehouse(wh)"
        >
          <div class="block-roof" />
          <div class="block-body">
            <div class="block-icon">{{ wh.icon }}</div>
            <div class="block-name">{{ wh.name }}</div>
            <div class="block-type">{{ warehouseLabel(wh) }}</div>
            <div class="block-count">{{ wh.material_count }} 份资料</div>
            <p v-if="wh.description" class="block-desc">{{ wh.description }}</p>
          </div>
          <div v-if="isAdmin" class="block-actions" @click.stop>
            <el-button link type="primary" @click="openEdit(wh)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(wh)">删除</el-button>
          </div>
        </div>
      </div>
    </section>

    <section v-loading="loading" class="warehouse-section">
      <h3 class="section-title">课程资料仓库 <span class="section-hint">（管理员手动分派）</span></h3>
      <div class="warehouse-grid course-grid">
        <div
          v-for="wh in courseWarehouses"
          :key="wh.id"
          class="warehouse-block course-block"
          :style="{ '--wh-color': wh.color }"
          @click="enterWarehouse(wh)"
        >
          <div class="block-roof" />
          <div class="block-body">
            <div class="block-icon">{{ wh.icon }}</div>
            <div class="block-name">{{ wh.name }}</div>
            <div class="block-type">{{ warehouseLabel(wh) }}</div>
            <div class="block-count">{{ wh.material_count }} 份资料</div>
            <p v-if="wh.description" class="block-desc">{{ wh.description }}</p>
          </div>
          <div v-if="isAdmin" class="block-actions" @click.stop>
            <el-button link type="primary" @click="openEdit(wh)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(wh)">删除</el-button>
          </div>
        </div>
      </div>
      <div v-if="!loading && courseWarehouses.length === 0" class="empty-hint">
        暂无课程资料仓库
      </div>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑仓库' : '新建仓库'"
      width="480px"
      @closed="resetForm"
    >
      <el-form label-width="90px">
        <el-form-item v-if="!editingId" label="仓库类型" required>
          <el-radio-group v-model="form.warehouse_kind">
            <el-radio value="file_type">格式资料仓库</el-radio>
            <el-radio value="course">课程资料仓库</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="仓库名称" required>
          <el-input v-model="form.name" placeholder="如：PDF 文献库" />
        </el-form-item>
        <el-form-item v-if="form.warehouse_kind === 'course' && !editingId" label="课程科目" required>
          <el-select v-model="form.course_subject" style="width: 100%" @change="onSubjectChange">
            <el-option
              v-for="opt in subjectOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.warehouse_kind === 'file_type'" label="资料格式" required>
          <el-select v-model="form.material_type" style="width: 100%" @change="onTypeChange">
            <el-option
              v-for="opt in typeOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="form.icon" placeholder="emoji 如 📦" />
        </el-form-item>
        <el-form-item label="主题色">
          <el-color-picker v-model="form.color" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.warehouse-page {
  padding: 4px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 6px;
  font-size: 22px;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.warehouse-section {
  margin-bottom: 32px;
}

.section-title {
  margin: 0 0 16px;
  font-size: 16px;
  color: #303133;
}

.section-hint {
  font-size: 13px;
  font-weight: 400;
  color: #909399;
}

.warehouse-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
  min-height: 80px;
}

.course-grid .warehouse-block {
  min-height: 200px;
}

.warehouse-block {
  position: relative;
  cursor: pointer;
  border-radius: 4px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
  overflow: hidden;
}

.warehouse-block:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.block-roof {
  height: 12px;
  background: var(--wh-color, #409eff);
  border-bottom: 3px solid color-mix(in srgb, var(--wh-color) 80%, #000);
}

.block-body {
  padding: 20px 16px 16px;
  text-align: center;
  border: 2px solid #ebeef5;
  border-top: none;
}

.block-icon {
  font-size: 40px;
  line-height: 1;
  margin-bottom: 10px;
}

.block-name {
  font-size: 17px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}

.block-type {
  font-size: 12px;
  color: var(--wh-color, #409eff);
  font-weight: 600;
  margin-bottom: 8px;
}

.block-count {
  font-size: 14px;
  color: #606266;
  padding: 6px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  display: inline-block;
}

.block-desc {
  margin: 10px 0 0;
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.block-actions {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding: 8px;
  border-top: 1px solid #ebeef5;
  background: #fafafa;
}

.empty-hint {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}
</style>
