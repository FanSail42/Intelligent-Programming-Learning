<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Plus, Promotion } from '@element-plus/icons-vue'
import ChatMarkdown from '@/components/ChatMarkdown.vue'
import { getMyCourses, type Course } from '@/api/course'
import {
  createSession,
  deleteSession,
  getChatSuggestions,
  listSessionMessages,
  listSessions,
  streamChatMessage,
  type ChatSession,
  type Citation,
} from '@/api/chat'

interface Bubble {
  id?: number
  role: 'user' | 'assistant'
  content: string
  reasoning?: string
  streaming?: boolean
  showReasoningLive?: boolean
  reasoningExpanded?: boolean
  citations?: Citation[]
  contextRelevant?: boolean
}

const courses = ref<Course[]>([])
const courseId = ref<number | null>(null)
const sessions = ref<ChatSession[]>([])
const activeSessionId = ref<number | null>(null)
const input = ref('')
const sending = ref(false)
const loadingMessages = ref(false)
const messages = ref<Bubble[]>([])
const suggestions = ref<string[]>([])
const emptyDraftIds = ref<Set<number>>(new Set())
const chatBox = ref<HTMLElement | null>(null)

function markDraftSession(sessionId: number) {
  emptyDraftIds.value = new Set(emptyDraftIds.value).add(sessionId)
}

function clearDraftSession(sessionId: number) {
  if (!emptyDraftIds.value.has(sessionId)) return
  const next = new Set(emptyDraftIds.value)
  next.delete(sessionId)
  emptyDraftIds.value = next
}

async function cleanupEmptyDraftSession(sessionId: number | null) {
  if (!sessionId || sending.value || !emptyDraftIds.value.has(sessionId)) return
  try {
    await deleteSession(sessionId)
    emptyDraftIds.value = new Set(
      [...emptyDraftIds.value].filter((id) => id !== sessionId),
    )
    sessions.value = sessions.value.filter((s) => s.id !== sessionId)
    if (activeSessionId.value === sessionId) {
      activeSessionId.value = null
      messages.value = []
    }
  } catch {
    // ignore cleanup errors on navigation
  }
}

function displayCitations(citations?: Citation[]): Citation[] {
  if (!citations?.length) return []
  const seen = new Set<string>()
  const result: Citation[] = []
  for (const c of citations) {
    const name = c.material_name?.trim() || '课程资料'
    if (seen.has(name)) continue
    seen.add(name)
    result.push({ ...c, material_name: name })
    if (result.length >= 3) break
  }
  return result
}

async function loadSuggestions() {
  if (!courseId.value) {
    suggestions.value = []
    return
  }
  try {
    suggestions.value = await getChatSuggestions(courseId.value)
  } catch {
    suggestions.value = []
  }
}

async function loadCourses() {
  const result = await getMyCourses({ page_num: 1, page_size: 100 })
  courses.value = result.list
  if (courses.value.length && !courseId.value) {
    courseId.value = courses.value[0].id
    await loadSuggestions()
    await loadSessions()
  }
}

async function loadSessionMessages(sessionId: number) {
  loadingMessages.value = true
  try {
    const rows = await listSessionMessages(sessionId)
    messages.value = rows.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      citations: m.citations,
      contextRelevant: m.context_relevant,
      reasoningExpanded: false,
    }))
    if (messages.value.length === 0) {
      const session = sessions.value.find((s) => s.id === sessionId)
      if (session?.title === '新对话') {
        markDraftSession(sessionId)
      }
    } else {
      clearDraftSession(sessionId)
    }
    await scrollBottom()
  } catch (err: unknown) {
    messages.value = []
    const msg = err instanceof Error ? err.message : '加载对话历史失败'
    if (msg.includes('405')) {
      ElMessage.error('后端未更新，请重启后端服务后再试')
    } else {
      ElMessage.error(msg)
    }
  } finally {
    loadingMessages.value = false
  }
}

async function selectSession(sessionId: number) {
  if (activeSessionId.value === sessionId && messages.value.length) return
  if (activeSessionId.value && activeSessionId.value !== sessionId) {
    await cleanupEmptyDraftSession(activeSessionId.value)
  }
  activeSessionId.value = sessionId
  await loadSessionMessages(sessionId)
}

async function loadSessions() {
  if (!courseId.value) return
  sessions.value = await listSessions(courseId.value)
  if (sessions.value.length) {
    await selectSession(sessions.value[0].id)
  } else {
    activeSessionId.value = null
    messages.value = []
  }
}

async function startFreshSession() {
  if (!courseId.value) return
  await cleanupEmptyDraftSession(activeSessionId.value)
  const session = await createSession(courseId.value)
  markDraftSession(session.id)
  sessions.value = await listSessions(courseId.value)
  activeSessionId.value = session.id
  messages.value = []
}

async function onCourseChange() {
  await loadSuggestions()
  await startFreshSession()
}

async function newSession() {
  if (!courseId.value) return
  await cleanupEmptyDraftSession(activeSessionId.value)
  const session = await createSession(courseId.value)
  markDraftSession(session.id)
  sessions.value.unshift(session)
  activeSessionId.value = session.id
  messages.value = []
}

async function scrollBottom() {
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}

async function ensureSession(): Promise<number | null> {
  if (activeSessionId.value) return activeSessionId.value
  if (!courseId.value) {
    ElMessage.warning('暂无课程，请先在「我的课程」中选课')
    return null
  }
  const session = await createSession(courseId.value)
  markDraftSession(session.id)
  sessions.value.unshift(session)
  activeSessionId.value = session.id
  return session.id
}

function summarizeTitle(text: string, maxLen = 10): string {
  const normalized = text.trim().replace(/\s+/g, ' ')
  if (!normalized) return '新对话'
  return normalized.length <= maxLen ? normalized : normalized.slice(0, maxLen)
}

function sessionLabel(session: ChatSession): string {
  if (session.title && session.title !== '新对话') return session.title
  return '新对话'
}

function updateSessionTitle(sessionId: number, title: string) {
  const idx = sessions.value.findIndex((s) => s.id === sessionId)
  if (idx >= 0) {
    sessions.value[idx] = { ...sessions.value[idx], title }
  }
}

function patchAssistant(idx: number, patch: Partial<Bubble>) {
  const current = messages.value[idx]
  if (!current) return
  messages.value[idx] = { ...current, ...patch }
}

function toggleReasoning(idx: number) {
  const current = messages.value[idx]
  if (!current) return
  patchAssistant(idx, { reasoningExpanded: !current.reasoningExpanded })
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

async function sendWithQuestion(text: string) {
  if (sending.value) return
  input.value = text
  await send()
}

async function send() {
  if (!input.value.trim() || sending.value) return
  if (!courseId.value) {
    ElMessage.warning('暂无课程，请先在「我的课程」中选课')
    return
  }
  const sessionId = await ensureSession()
  if (!sessionId) return
  const text = input.value.trim()
  input.value = ''
  clearDraftSession(sessionId)
  const currentSession = sessions.value.find((s) => s.id === sessionId)
  if (currentSession?.title === '新对话') {
    updateSessionTitle(sessionId, summarizeTitle(text))
  }
  messages.value.push({ role: 'user', content: text })
  const assistantIdx = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    reasoning: '',
    streaming: true,
    showReasoningLive: true,
    reasoningExpanded: false,
  })
  await scrollBottom()

  sending.value = true
  try {
    await streamChatMessage(
      sessionId,
      text,
      (delta) => {
        const current = messages.value[assistantIdx]
        if (!current) return
        messages.value[assistantIdx] = {
          ...current,
          content: current.content + delta,
          showReasoningLive: false,
        }
        scrollBottom()
      },
      ({ citations, context_relevant, session_title }) => {
        const relevant = context_relevant !== false
        patchAssistant(assistantIdx, {
          citations: relevant ? citations : [],
          contextRelevant: context_relevant,
          streaming: false,
          showReasoningLive: false,
          reasoningExpanded: false,
        })
        if (session_title) {
          updateSessionTitle(sessionId, session_title)
        }
      },
      (msg) => {
        patchAssistant(assistantIdx, {
          content: msg || 'AI 回复失败，请稍后重试',
          streaming: false,
          showReasoningLive: false,
        })
        ElMessage.error(msg)
      },
      (delta) => {
        const current = messages.value[assistantIdx]
        if (!current) return
        messages.value[assistantIdx] = {
          ...current,
          reasoning: (current.reasoning || '') + delta,
          showReasoningLive: true,
        }
        scrollBottom()
      },
    )
  } finally {
    sending.value = false
    await scrollBottom()
  }
}

async function confirmDeleteSession(session: ChatSession) {
  const label = sessionLabel(session)
  try {
    await ElMessageBox.confirm(
      `确定删除会话「${label}」？删除后无法恢复。`,
      '删除会话',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }

  await deleteSession(session.id)
  clearDraftSession(session.id)
  const wasActive = activeSessionId.value === session.id
  sessions.value = sessions.value.filter((s) => s.id !== session.id)
  if (wasActive) {
    if (sessions.value.length) {
      await selectSession(sessions.value[0].id)
    } else {
      activeSessionId.value = null
      messages.value = []
    }
  }
  ElMessage.success('会话已删除')
}

async function cleanupOnLeave() {
  await cleanupEmptyDraftSession(activeSessionId.value)
}

onMounted(loadCourses)
onBeforeRouteLeave(async () => {
  await cleanupOnLeave()
})
onBeforeUnmount(async () => {
  await cleanupOnLeave()
})
</script>

<template>
  <div class="chat-page">
    <aside class="sidebar">
      <div class="sidebar-top">
        <el-select
          v-model="courseId"
          class="course-select"
          placeholder="选择课程"
          @change="onCourseChange"
        >
          <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <button type="button" class="new-chat-btn" @click="newSession">
          <el-icon><Plus /></el-icon>
          开启新对话
        </button>
      </div>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: activeSessionId === s.id }"
          @click="selectSession(s.id)"
        >
          <span class="session-title">{{ sessionLabel(s) }}</span>
          <button
            type="button"
            class="session-delete"
            title="删除会话"
            @click.stop="confirmDeleteSession(s)"
          >
            <el-icon><Delete /></el-icon>
          </button>
        </div>
      </div>
    </aside>

    <section class="chat-main">
      <div
        ref="chatBox"
        v-loading="loadingMessages"
        class="messages-wrap"
        element-loading-text="加载对话历史..."
      >
        <div class="messages-inner">
          <div v-if="!loadingMessages && !messages.length" class="welcome">
            <h2>慧编学伴 AI 助教</h2>
            <p>基于课程资料为你答疑解惑，支持多轮对话与代码讲解</p>
            <div class="welcome-hints">
              <button
                v-for="hint in suggestions"
                :key="hint"
                type="button"
                class="welcome-hint"
                :disabled="sending"
                @click="sendWithQuestion(hint)"
              >
                {{ hint }}
              </button>
            </div>
          </div>

          <div
            v-for="(m, i) in messages"
            :key="m.id ?? `local-${i}`"
            class="message-row"
            :class="m.role"
          >
            <div v-if="m.role === 'assistant'" class="avatar ai-avatar">AI</div>

            <div class="message-body">
              <template v-if="m.role === 'assistant'">
                <div
                  v-if="m.showReasoningLive && m.reasoning"
                  class="reasoning-live"
                >
                  <div class="reasoning-label">
                    <span class="dot-pulse" /> 深度思考中...
                  </div>
                  <div class="reasoning-text">{{ m.reasoning }}</div>
                </div>

                <div
                  v-else-if="m.streaming && !m.content && !m.reasoning"
                  class="loading-text"
                >
                  <span class="dot-pulse" /> 正在组织回答...
                </div>

                <div v-if="m.content" class="assistant-content">
                  <ChatMarkdown :content="m.content" />
                </div>

                <div
                  v-if="!m.streaming && m.reasoning"
                  class="reasoning-collapsed"
                >
                  <button type="button" class="reasoning-toggle" @click="toggleReasoning(i)">
                    {{ m.reasoningExpanded ? '收起思考过程' : '查看思考过程' }}
                  </button>
                  <div v-show="m.reasoningExpanded" class="reasoning-text muted">
                    {{ m.reasoning }}
                  </div>
                </div>
              </template>

              <div v-else class="user-content">{{ m.content }}</div>

              <div
                v-if="m.role === 'assistant' && !m.streaming && m.contextRelevant === false"
                class="ctx-hint"
              >
                注意：该回答不涉及本课程资料，以下为通用知识解答
              </div>

              <div
                v-if="m.contextRelevant !== false && displayCitations(m.citations).length"
                class="citations"
              >
                <span
                  v-for="c in displayCitations(m.citations)"
                  :key="c.chunk_id"
                  class="citation-tag"
                >
                  来自{{ c.material_name }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="composer-wrap">
        <div class="composer">
          <el-input
            v-model="input"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 6 }"
            resize="none"
            placeholder="向 AI 助教提问，Enter 发送，Shift+Enter 换行"
            @keydown="handleKeydown"
          />
          <button
            type="button"
            class="send-btn"
            :class="{ active: input.trim() && !sending }"
            :disabled="!input.trim() || sending"
            @click="send"
          >
            <el-icon v-if="!sending"><Promotion /></el-icon>
            <span v-else class="send-loading" />
          </button>
        </div>
        <p class="composer-tip">回答基于当前课程资料，引用将展示最相关的 3 份资料来源</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  gap: 0;
  height: calc(100vh - 120px);
  min-height: 560px;
  margin: -8px -12px 0;
  background: #f7f8fa;
  border-radius: 12px;
  overflow: hidden;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #f0f1f3;
  border-right: 1px solid #e5e7eb;
}

.sidebar-top {
  padding: 16px 12px 12px;
}

.course-select {
  width: 100%;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  margin-top: 10px;
  padding: 10px 12px;
  border: 1px solid #d8dce3;
  border-radius: 10px;
  background: #fff;
  color: #303133;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.new-chat-btn:hover {
  background: #fafbfc;
  border-color: #c5cad3;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px 12px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 12px;
  margin-bottom: 2px;
  border-radius: 8px;
  cursor: pointer;
  color: #4b5563;
  transition: background 0.15s;
}

.session-item:hover {
  background: rgba(0, 0, 0, 0.04);
}

.session-item.active {
  background: #fff;
  color: #1f2937;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.session-delete {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s, color 0.15s, background 0.15s;
}

.session-item:hover .session-delete,
.session-item.active .session-delete {
  opacity: 1;
}

.session-delete:hover {
  color: #ef4444;
  background: #fee2e2;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #f7f8fa;
}

.messages-wrap {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
}

.messages-inner {
  max-width: 820px;
  margin: 0 auto;
  padding: 0 24px;
}

.welcome {
  text-align: center;
  padding: 80px 20px 40px;
  color: #6b7280;
}

.welcome h2 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.welcome p {
  margin: 0 0 28px;
  font-size: 14px;
}

.welcome-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.welcome-hint {
  padding: 10px 16px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e5e7eb;
  font-size: 13px;
  color: #4b5563;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, color 0.15s;
}

.welcome-hint:hover:not(:disabled) {
  border-color: #4d6bfe;
  color: #4d6bfe;
  background: #f5f7ff;
}

.welcome-hint:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.message-row {
  display: flex;
  gap: 14px;
  margin-bottom: 28px;
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.ai-avatar {
  background: linear-gradient(135deg, #4d6bfe, #6b8afd);
  color: #fff;
}

.message-body {
  flex: 1;
  min-width: 0;
  max-width: calc(100% - 46px);
}

.message-row.user .message-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.user-content {
  display: inline-block;
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 16px 16px 4px 16px;
  background: #edf3fe;
  color: #1f2937;
  font-size: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
  text-align: left;
}

.assistant-content {
  color: #1f2937;
  font-size: 15px;
  line-height: 1.75;
}

.loading-text {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  font-size: 14px;
}

.reasoning-live {
  margin-bottom: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e8eaed;
}

.reasoning-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.dot-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4d6bfe;
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.35; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1); }
}

.reasoning-text {
  font-size: 13px;
  line-height: 1.65;
  color: #6b7280;
  white-space: pre-wrap;
  max-height: 220px;
  overflow-y: auto;
}

.reasoning-text.muted {
  margin-top: 8px;
  max-height: 180px;
  padding: 10px 12px;
  background: #f3f4f6;
  border-radius: 8px;
}

.reasoning-collapsed {
  margin-top: 10px;
}

.reasoning-toggle {
  border: none;
  background: none;
  color: #9ca3af;
  font-size: 13px;
  cursor: pointer;
  padding: 0;
}

.reasoning-toggle:hover {
  color: #4d6bfe;
}

.ctx-hint {
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
  font-size: 13px;
}

.citations {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.citation-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 6px;
  background: #fff;
  border: 1px solid #e5e7eb;
  color: #6b7280;
  font-size: 12px;
}

.composer-wrap {
  flex-shrink: 0;
  padding: 0 24px 20px;
}

.composer {
  max-width: 820px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 12px 10px 16px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.composer :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  padding: 4px 0;
  font-size: 15px;
  line-height: 1.6;
  background: transparent;
}

.composer :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.send-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 10px;
  background: #e5e7eb;
  color: #9ca3af;
  cursor: not-allowed;
  transition: background 0.15s, color 0.15s;
}

.send-btn.active {
  background: #4d6bfe;
  color: #fff;
  cursor: pointer;
}

.send-btn.active:hover {
  background: #3d5bdb;
}

.send-loading {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.composer-tip {
  max-width: 820px;
  margin: 8px auto 0;
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
}
</style>
