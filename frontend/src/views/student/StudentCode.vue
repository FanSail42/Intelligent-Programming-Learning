<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import CodeResultPanel from '@/components/CodeResultPanel.vue'
import SplitPane from '@/components/SplitPane.vue'
import { CODE_LANGUAGE_OPTIONS, languageLabel } from '@/constants/codeLanguages'
import { getCodeResult, submitCode, type AnalysisResult } from '@/api/code'
import { checkCodeLanguage } from '@/utils/codeLanguageDetect'

const DEFAULT_SAMPLES: Record<string, string> = {
  python: `def greet(name):
    print("Hello", name)

greet("world")
`,
  java: `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
`,
  c: `#include <stdio.h>

int main() {
    printf("Hello\\n");
    return 0;
}
`,
  cpp: `#include <iostream>
using namespace std;

int main() {
    cout << "Hello" << endl;
    return 0;
}
`,
}

const route = useRoute()
const router = useRouter()
const language = ref('python')
const sourceCode = ref(DEFAULT_SAMPLES.python)
const activeTab = ref('syntax')
const submitting = ref(false)
const result = ref<AnalysisResult | null>(null)
const analysisStatus = ref<string>('')
const analysisError = ref<string | null>(null)

watch(language, (lang) => {
  if (!sourceCode.value.trim()) {
    sourceCode.value = DEFAULT_SAMPLES[lang] ?? ''
  }
})

async function loadSubmission(id: number) {
  try {
    const data = await getCodeResult(id)
    sourceCode.value = data.submission.source_code
    language.value = data.submission.language
    analysisStatus.value = data.analysis.status
    if (data.analysis.status === 'done' && data.analysis.result) {
      result.value = data.analysis.result
      analysisError.value = null
    } else {
      result.value = null
      analysisError.value = data.analysis.error_message
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '加载失败'
    ElMessage.error(msg)
  }
}

async function confirmLanguageMismatch(suggested: string, suggestedLabel: string) {
  try {
    await ElMessageBox.confirm(
      `检测到代码更像 ${suggestedLabel}，与当前选择的 ${languageLabel(language.value)} 不一致。请重新选择语言后再提交。`,
      '语言不匹配',
      {
        confirmButtonText: `切换为 ${suggestedLabel}`,
        cancelButtonText: '继续编辑',
        type: 'warning',
      },
    )
    language.value = suggested
    ElMessage.info(`已切换为 ${suggestedLabel}，请确认后重新提交`)
    return false
  } catch {
    return false
  }
}

async function validateLanguageBeforeSubmit(): Promise<boolean> {
  const check = checkCodeLanguage(sourceCode.value, language.value)
  if (check.match) return true
  return confirmLanguageMismatch(check.suggested, check.suggestedLabel)
}

async function handleSubmit() {
  if (!sourceCode.value.trim()) {
    ElMessage.warning('请输入代码')
    return
  }

  const langOk = await validateLanguageBeforeSubmit()
  if (!langOk) return

  submitting.value = true
  result.value = null
  analysisError.value = null
  try {
    const data = await submitCode({
      language: language.value,
      source_code: sourceCode.value,
    })
    analysisStatus.value = data.analysis.status
    if (data.analysis.status === 'done' && data.analysis.result) {
      result.value = data.analysis.result
    } else {
      analysisError.value = data.analysis.error_message || '分析失败'
    }
    router.replace({ path: '/student/code' })
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '提交失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

function openHistory() {
  router.push('/student/code/history')
}

onMounted(() => {
  const rawId = route.query.id
  const submissionId = typeof rawId === 'string' ? Number(rawId) : NaN
  if (!Number.isNaN(submissionId) && submissionId > 0) {
    loadSubmission(submissionId)
  }
})

watch(
  () => route.query.id,
  (rawId) => {
    const submissionId = typeof rawId === 'string' ? Number(rawId) : NaN
    if (!Number.isNaN(submissionId) && submissionId > 0) {
      loadSubmission(submissionId)
    }
  },
)
</script>

<template>
  <div class="code-page">
    <el-card class="toolbar" shadow="never">
      <div class="toolbar-row">
        <el-form inline class="toolbar-form">
          <el-form-item label="语言">
            <el-select v-model="language" style="width: 140px">
              <el-option
                v-for="opt in CODE_LANGUAGE_OPTIONS"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <div class="toolbar-actions">
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            提交分析
          </el-button>
          <el-button @click="openHistory">提交历史</el-button>
        </div>
      </div>
    </el-card>

    <SplitPane :initial-left-percent="52">
      <template #left>
        <el-card class="panel-card editor-card" shadow="never">
          <template #header>代码编辑器</template>
          <div class="editor-scroll">
            <textarea
              v-model="sourceCode"
              class="code-editor"
              spellcheck="false"
              placeholder="在此粘贴或编写代码..."
            />
          </div>
        </el-card>
      </template>
      <template #right>
        <el-card class="panel-card result-card" shadow="never">
          <template #header>
            <span>讲解结果</span>
            <el-tag v-if="analysisStatus" size="small" class="status-tag">
              {{ analysisStatus }}
            </el-tag>
          </template>

          <CodeResultPanel
            v-model:active-tab="activeTab"
            :result="result"
            :analysis-status="analysisStatus"
            :analysis-error="analysisError"
            :language="language"
          />
        </el-card>
      </template>
    </SplitPane>
  </div>
</template>

<style scoped>
.code-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.toolbar-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
}

.panel-card {
  height: 100%;
  min-height: 520px;
}

.panel-card :deep(.el-card__body) {
  height: calc(100% - 52px);
  box-sizing: border-box;
}

.editor-scroll {
  height: 100%;
  overflow: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
}

.code-editor {
  display: block;
  width: 100%;
  min-width: 100%;
  min-height: 440px;
  height: 100%;
  padding: 12px;
  margin: 0;
  border: none;
  outline: none;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.55;
  white-space: pre;
  overflow-wrap: normal;
  word-break: normal;
  resize: none;
  box-sizing: border-box;
  background: transparent;
}

.status-tag {
  margin-left: 8px;
}
</style>
