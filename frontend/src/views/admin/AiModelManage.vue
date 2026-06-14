<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  addCustomChatModel,
  deleteCustomChatModel,
  getAiConfig,
  getAiModels,
  updateAiConfig,
  type AiConfig,
  type AiModelCatalog,
  type AiModelItem,
} from '@/api/admin'

const loading = ref(false)
const saving = ref(false)
const catalog = ref<AiModelCatalog | null>(null)
const config = ref<AiConfig | null>(null)

const customDialogVisible = ref(false)
const customSubmitting = ref(false)
const customForm = reactive({
  id: '',
  name: '',
  description: '',
})

const form = reactive({
  llm_model: '',
  llm_base_url: '',
  llm_api_key: '',
  embedding_model: '',
  embedding_base_url: '',
  embedding_api_key: '',
  llm_daily_limit: 100,
  update_llm_key: false,
  update_embedding_key: false,
})

const chatModelOptions = computed(() => catalog.value?.chat_models ?? [])

const currentChatModel = computed(() =>
  chatModelOptions.value.find((m) => m.id === form.llm_model),
)

const customModels = computed(() => chatModelOptions.value.filter((m) => m.custom))

async function loadAll() {
  loading.value = true
  try {
    const [models, cfg] = await Promise.all([getAiModels(), getAiConfig()])
    catalog.value = models
    config.value = cfg
    form.llm_model = cfg.llm_model
    form.llm_base_url = cfg.llm_base_url
    form.embedding_model = cfg.embedding_model
    form.embedding_base_url = cfg.embedding_base_url
    form.llm_daily_limit = cfg.llm_daily_limit
    form.llm_api_key = ''
    form.embedding_api_key = ''
    form.update_llm_key = false
    form.update_embedding_key = false
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载 AI 配置失败')
  } finally {
    loading.value = false
  }
}

function openCustomDialog() {
  customForm.id = ''
  customForm.name = ''
  customForm.description = ''
  customDialogVisible.value = true
}

async function submitCustomModel() {
  const id = customForm.id.trim()
  if (!id) {
    ElMessage.warning('请填写模型 ID（与百炼控制台一致）')
    return
  }
  customSubmitting.value = true
  try {
    const created = await addCustomChatModel({
      id,
      name: customForm.name.trim() || undefined,
      description: customForm.description.trim() || undefined,
    })
    catalog.value = await getAiModels()
    form.llm_model = created.id
    customDialogVisible.value = false
    ElMessage.success(`已添加自定义模型 ${created.id}`)
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '添加失败')
  } finally {
    customSubmitting.value = false
  }
}

async function handleRemoveCustom(model: AiModelItem) {
  try {
    await ElMessageBox.confirm(`确定删除自定义模型「${model.name}」？`, '删除确认', {
      type: 'warning',
    })
    await deleteCustomChatModel(model.id)
    catalog.value = await getAiModels()
    if (form.llm_model === model.id) {
      form.llm_model = catalog.value.chat_models[0]?.id ?? ''
    }
    ElMessage.success('已删除')
  } catch {
    // cancelled
  }
}

async function handleSave() {
  saving.value = true
  try {
    const payload: Parameters<typeof updateAiConfig>[0] = {
      llm_model: form.llm_model,
      llm_base_url: form.llm_base_url,
      embedding_model: form.embedding_model,
      embedding_base_url: form.embedding_base_url,
      llm_daily_limit: form.llm_daily_limit,
    }
    if (form.update_llm_key && form.llm_api_key.trim()) {
      payload.llm_api_key = form.llm_api_key.trim()
    }
    if (form.update_embedding_key && form.embedding_api_key.trim()) {
      payload.embedding_api_key = form.embedding_api_key.trim()
    }
    config.value = await updateAiConfig(payload)
    form.llm_api_key = ''
    form.embedding_api_key = ''
    form.update_llm_key = false
    form.update_embedding_key = false
    ElMessage.success('AI 配置已保存，新请求将立即生效')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadAll()
})
</script>

<template>
  <div class="page" v-loading="loading">
    <header class="page-header">
      <div>
        <h1 class="title">AI 模型管理</h1>
        <p class="subtitle">
          对接
          <a :href="catalog?.console_url" target="_blank" rel="noopener">阿里云百炼模型广场</a>
          ，配置对话/向量模型、API 密钥与调用限额
        </p>
      </div>
      <div class="header-actions">
        <el-button @click="loadAll">刷新</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存配置</el-button>
      </div>
    </header>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="15">
        <el-card shadow="never" class="section-card">
          <template #header><span>对话模型（LLM）</span></template>
          <el-form label-width="120px" label-position="left">
            <el-form-item label="当前模型">
              <div class="model-select-row">
                <el-select v-model="form.llm_model" filterable style="flex: 1">
                  <el-option
                    v-for="m in chatModelOptions"
                    :key="m.id"
                    :label="`${m.name} (${m.id})`"
                    :value="m.id"
                  >
                    <div class="model-option">
                      <span>{{ m.name }}</span>
                      <div class="model-tags">
                        <el-tag v-if="m.recommended" size="small" type="success">推荐</el-tag>
                        <el-tag v-if="m.custom" size="small" type="warning">自定义</el-tag>
                      </div>
                    </div>
                  </el-option>
                </el-select>
                <el-button type="primary" plain @click="openCustomDialog">添加自定义</el-button>
              </div>
            </el-form-item>
            <el-alert
              v-if="currentChatModel"
              :title="currentChatModel.description"
              type="info"
              :closable="false"
              show-icon
              class="model-hint"
            />
            <el-form-item v-if="customModels.length" label="自定义列表">
              <div class="custom-model-list">
                <div v-for="m in customModels" :key="m.id" class="custom-model-chip">
                  <span>{{ m.id }}</span>
                  <el-button link type="danger" size="small" @click="handleRemoveCustom(m)">
                    删除
                  </el-button>
                </div>
              </div>
            </el-form-item>
            <el-form-item label="API Base URL">
              <el-input v-model="form.llm_base_url" placeholder="百炼 OpenAI 兼容端点" />
            </el-form-item>
            <el-form-item label="LLM API Key">
              <div class="key-row">
                <span v-if="config?.llm_api_key_configured" class="key-masked">
                  已配置：{{ config.llm_api_key_masked }}
                </span>
                <span v-else class="key-empty">未配置（演示模式）</span>
              </div>
              <el-checkbox v-model="form.update_llm_key">更新密钥</el-checkbox>
              <el-input
                v-if="form.update_llm_key"
                v-model="form.llm_api_key"
                type="password"
                show-password
                placeholder="sk-..."
                class="key-input"
              />
              <div v-if="catalog" class="help-link">
                <a :href="catalog.api_key_url" target="_blank" rel="noopener">获取百炼 API Key →</a>
              </div>
            </el-form-item>
            <el-form-item label="日调用限额">
              <el-input-number v-model="form.llm_daily_limit" :min="1" :max="10000" />
              <span class="field-hint">每位用户每日 AI 对话/代码讲解次数上限</span>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never" class="section-card">
          <template #header><span>向量模型（Embedding / RAG）</span></template>
          <el-form label-width="120px" label-position="left">
            <el-form-item label="向量模型">
              <el-select v-model="form.embedding_model" filterable style="width: 100%">
                <el-option
                  v-for="m in catalog?.embedding_models ?? []"
                  :key="m.id"
                  :label="`${m.name} (${m.id})`"
                  :value="m.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="API Base URL">
              <el-input v-model="form.embedding_base_url" />
            </el-form-item>
            <el-form-item label="Embedding Key">
              <div class="key-row">
                <span v-if="config?.embedding_api_key_configured" class="key-masked">
                  已配置：{{ config.embedding_api_key_masked }}
                </span>
                <span v-else class="key-empty">未单独配置（将复用 LLM Key）</span>
              </div>
              <el-checkbox v-model="form.update_embedding_key">更新密钥</el-checkbox>
              <el-input
                v-if="form.update_embedding_key"
                v-model="form.embedding_api_key"
                type="password"
                show-password
                placeholder="可与 LLM Key 相同"
                class="key-input"
              />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="config" shadow="never" class="section-card meta-card">
          <template #header><span>配置来源</span></template>
          <p>
            当前生效来源：<el-tag size="small">{{ config.config_source }}</el-tag>
          </p>
          <p class="meta-hint">
            管理员保存后写入 <code>sys_config</code> 并加密存储密钥；Token 用量请前往
            <router-link to="/admin/ai-usage">AI 用量监控</router-link>。
          </p>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="9">
        <el-card shadow="never" class="section-card catalog-card">
          <template #header><span>百炼模型广场</span></template>
          <p class="bailian-desc">
            系统预置常用百炼模型，新模型可通过「添加自定义」录入 Model ID。
          </p>
          <div class="catalog-actions">
            <el-button type="primary" tag="a" :href="catalog?.console_url" target="_blank" rel="noopener">
              打开模型广场
            </el-button>
            <el-button tag="a" :href="catalog?.docs_url" target="_blank" rel="noopener">模型文档</el-button>
          </div>
          <el-divider />
          <div class="model-list">
            <div v-for="m in chatModelOptions" :key="m.id" class="model-item">
              <div class="model-item-head">
                <strong>{{ m.name }}</strong>
                <el-tag v-if="m.custom" size="small" type="warning">自定义</el-tag>
                <el-tag v-else size="small">{{ m.tier }}</el-tag>
              </div>
              <div class="model-id">{{ m.id }}</div>
              <div class="model-desc">{{ m.description }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="customDialogVisible" title="添加自定义对话模型" width="480px">
      <el-form label-width="100px">
        <el-form-item label="模型 ID" required>
          <el-input v-model="customForm.id" placeholder="如 kimi-k2.6" />
        </el-form-item>
        <el-form-item label="展示名称">
          <el-input v-model="customForm.name" placeholder="可选" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="customForm.description" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="customDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="customSubmitting" @click="submitCustomModel">添加</el-button>
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
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.title {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 700;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  color: #909399;
}

.subtitle a {
  color: #409eff;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.section-card {
  margin-bottom: 16px;
}

.catalog-card {
  position: sticky;
  top: 16px;
}

.model-select-row {
  display: flex;
  gap: 8px;
  width: 100%;
}

.model-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.model-tags {
  display: flex;
  gap: 4px;
}

.custom-model-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.custom-model-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: #fdf6ec;
  border-radius: 6px;
  font-size: 12px;
  font-family: monospace;
}

.model-hint {
  margin-bottom: 16px;
}

.key-row {
  margin-bottom: 8px;
  font-size: 13px;
}

.key-masked {
  color: #606266;
}

.key-empty {
  color: #e6a23c;
}

.key-input {
  margin-top: 8px;
}

.help-link {
  margin-top: 6px;
  font-size: 12px;
}

.help-link a {
  color: #409eff;
}

.field-hint {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.bailian-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.catalog-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.model-list {
  max-height: calc(100vh - 280px);
  overflow-y: auto;
}

.model-item {
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
}

.model-item:last-child {
  border-bottom: none;
}

.model-item-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-id {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}

.model-desc {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
}

.meta-hint {
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}

.meta-hint a {
  color: #409eff;
}
</style>
