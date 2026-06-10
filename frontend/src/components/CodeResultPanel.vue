<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentCopy } from '@element-plus/icons-vue'
import type { AnalysisResult } from '@/api/code'

const props = defineProps<{
  result: AnalysisResult | null
  analysisStatus?: string
  analysisError?: string | null
  language?: string
}>()

const activeTab = defineModel<string>('activeTab', { default: 'syntax' })
const copying = ref(false)

const scoreTagType = (score: string) => {
  if (score === 'error') return 'danger'
  if (score === 'warning') return 'warning'
  return 'success'
}

const scoreLabel = (score: string) => {
  if (score === 'error') return '有问题'
  if (score === 'warning') return '需注意'
  return '正常'
}

function splitParagraphs(text: string): string[] {
  return text
    .split(/\n+/)
    .flatMap((block) => block.split(/(?<=[。！？；])\s+/))
    .map((s) => s.trim())
    .filter(Boolean)
}

async function copyReferenceCode() {
  const code = props.result?.fixed_code
  if (!code) return
  copying.value = true
  try {
    await navigator.clipboard.writeText(code)
    ElMessage.success('参考代码已复制')
  } catch {
    ElMessage.error('复制失败，请手动选择复制')
  } finally {
    copying.value = false
  }
}
</script>

<template>
  <div class="result-panel">
    <el-alert
      v-if="analysisError"
      type="error"
      :title="analysisError"
      show-icon
      :closable="false"
      class="mb-12"
    />

    <div v-if="result" class="result-scroll">
      <div class="summary-block">
        <h4 class="block-title">总评</h4>
        <p v-for="(line, i) in splitParagraphs(result.summary)" :key="i" class="summary-line">
          {{ line }}
        </p>
      </div>

      <el-alert
        v-if="result.truncated"
        type="warning"
        title="代码过长已截断，仅分析可见部分"
        show-icon
        :closable="false"
        class="mb-12"
      />

      <el-tabs v-model="activeTab" class="result-tabs">
        <el-tab-pane label="语法" name="syntax">
          <div class="level-head">
            <el-tag :type="scoreTagType(result.levels.syntax.score)">
              {{ scoreLabel(result.levels.syntax.score) }}
            </el-tag>
          </div>
          <div v-if="result.levels.syntax.issues.length" class="issue-stack">
            <div
              v-for="(item, i) in result.levels.syntax.issues"
              :key="i"
              class="issue-card"
            >
              <div class="issue-message">
                <span v-if="item.line" class="issue-line">第 {{ item.line }} 行</span>
                <span>{{ item.message }}</span>
              </div>
              <p v-if="item.hint" class="issue-detail">{{ item.hint }}</p>
            </div>
          </div>
          <p v-else class="empty-hint">未发现明显语法问题</p>
          <ul v-if="result.levels.syntax.suggestions?.length" class="suggest-list">
            <li v-for="(s, i) in result.levels.syntax.suggestions" :key="i">{{ s }}</li>
          </ul>
        </el-tab-pane>

        <el-tab-pane label="语义" name="semantic">
          <div class="level-head">
            <el-tag :type="scoreTagType(result.levels.semantic.score)">
              {{ scoreLabel(result.levels.semantic.score) }}
            </el-tag>
          </div>
          <div v-if="result.levels.semantic.issues.length" class="issue-stack">
            <div
              v-for="(item, i) in result.levels.semantic.issues"
              :key="i"
              class="issue-card"
            >
              <div class="issue-message">{{ item.message }}</div>
              <p v-if="item.explanation" class="issue-detail">{{ item.explanation }}</p>
            </div>
          </div>
          <p v-else class="empty-hint">逻辑结构基本合理</p>
          <ul v-if="result.levels.semantic.suggestions?.length" class="suggest-list">
            <li v-for="(s, i) in result.levels.semantic.suggestions" :key="i">{{ s }}</li>
          </ul>
        </el-tab-pane>

        <el-tab-pane label="运行" name="runtime">
          <div class="level-head">
            <el-tag :type="scoreTagType(result.levels.runtime.score)">
              {{ scoreLabel(result.levels.runtime.score) }}
            </el-tag>
          </div>
          <p class="runtime-note">基于静态分析推断，未真实执行代码</p>
          <div v-if="result.levels.runtime.issues.length" class="issue-stack">
            <div
              v-for="(item, i) in result.levels.runtime.issues"
              :key="i"
              class="issue-card"
            >
              <div class="issue-message">{{ item.message }}</div>
              <p v-if="item.explanation" class="issue-detail">{{ item.explanation }}</p>
            </div>
          </div>
          <p v-else class="empty-hint">未发现明显运行风险</p>
          <p v-if="result.levels.runtime.stderr_hint" class="stderr">
            {{ result.levels.runtime.stderr_hint }}
          </p>
        </el-tab-pane>
      </el-tabs>

      <div v-if="result.fixed_code" class="reference-block">
        <div class="reference-header">
          <h4 class="block-title">参考代码</h4>
          <el-button
            size="small"
            :icon="DocumentCopy"
            :loading="copying"
            @click="copyReferenceCode"
          >
            一键复制
          </el-button>
        </div>
        <pre class="reference-code">{{ result.fixed_code }}</pre>
      </div>

      <div v-if="result.examples?.length" class="examples-block">
        <h4 class="block-title">常见错误参考</h4>
        <ul class="examples-list">
          <li v-for="(ex, i) in result.examples" :key="i">
            <p v-for="(line, j) in splitParagraphs(ex)" :key="j" class="example-line">{{ line }}</p>
          </li>
        </ul>
      </div>
    </div>

    <el-empty v-else-if="!analysisError" description="提交代码后查看分级讲解" />
  </div>
</template>

<style scoped>
.result-panel {
  min-height: 0;
  height: 100%;
}

.result-scroll {
  max-height: 480px;
  overflow-y: auto;
  padding: 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background: #fafafa;
}

.block-title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.summary-block {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.summary-line {
  margin: 0 0 8px;
  font-size: 14px;
  line-height: 1.75;
  color: #303133;
}

.summary-line:last-child {
  margin-bottom: 0;
}

.level-head {
  margin-bottom: 10px;
}

.issue-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.issue-card {
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}

.issue-message {
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
}

.issue-line {
  display: inline-block;
  margin-right: 8px;
  padding: 0 6px;
  font-size: 12px;
  color: #409eff;
  background: #ecf5ff;
  border-radius: 4px;
}

.issue-detail {
  margin: 8px 0 0;
  padding-top: 8px;
  border-top: 1px dashed #ebeef5;
  font-size: 13px;
  line-height: 1.7;
  color: #606266;
}

.suggest-list {
  margin: 12px 0 0;
  padding-left: 20px;
}

.suggest-list li {
  margin-bottom: 6px;
  line-height: 1.65;
  color: #606266;
}

.empty-hint {
  color: #909399;
  margin: 8px 0;
  line-height: 1.6;
}

.runtime-note {
  font-size: 12px;
  color: #909399;
  margin: 0 0 10px;
  line-height: 1.5;
}

.stderr {
  margin-top: 10px;
  padding: 10px 12px;
  background: #fef0f0;
  border-radius: 4px;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.reference-block {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.reference-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.reference-code {
  margin: 0;
  padding: 12px;
  background: #1e1e1e;
  color: #d4d4d4;
  border-radius: 6px;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.55;
  white-space: pre;
  overflow-x: auto;
  max-height: 280px;
}

.examples-block {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.examples-list {
  margin: 0;
  padding-left: 20px;
}

.examples-list li {
  margin-bottom: 12px;
}

.example-line {
  margin: 0 0 6px;
  line-height: 1.7;
  color: #606266;
}

.mb-12 {
  margin-bottom: 12px;
}
</style>
