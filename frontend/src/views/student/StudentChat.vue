<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import ChatMarkdown from '@/components/ChatMarkdown.vue'
import { getMyCourses, type Course } from '@/api/course'
import {
  createSession,
  deleteSession,
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
  noContext?: boolean
}

const courses = ref<Course[]>([])
const courseId = ref<number | null>(null)
const sessions = ref<ChatSession[]>([])
const activeSessionId = ref<number | null>(null)
const input = ref('')
const sending = ref(false)
const loadingMessages = ref(false)
const messages = ref<Bubble[]>([])
const chatBox = ref<HTMLElement | null>(null)

async function loadCourses() {
  const result = await getMyCourses({ page_num: 1, page_size: 100 })
  courses.value = result.list
  if (courses.value.length && !courseId.value) {
    courseId.value = courses.value[0].id
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
      noContext: m.no_context,
      reasoningExpanded: false,
    }))
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

async function onCourseChange() {
  activeSessionId.value = null
  messages.value = []
  await loadSessions()
}

async function newSession() {
  if (!courseId.value) return
  const session = await createSession(courseId.value)
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
      ({ citations, no_context, session_title }) => {
        patchAssistant(assistantIdx, {
          citations,
          noContext: no_context,
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

onMounted(loadCourses)
</script>

<template>
  <div class="chat-layout">
    <aside class="sidebar">
      <div class="side-head">
        <el-select v-model="courseId" style="width: 100%" @change="onCourseChange">
          <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-button type="primary" plain style="width: 100%; margin-top: 8px" @click="newSession">
          新对话
        </el-button>
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
          <el-button
            link
            type="danger"
            class="session-delete"
            title="删除会话"
            @click.stop="confirmDeleteSession(s)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </aside>

    <section class="chat-main">
      <div
        ref="chatBox"
        v-loading="loadingMessages"
        class="messages"
        element-loading-text="加载对话历史..."
      >
        <el-empty
          v-if="!loadingMessages && !messages.length && activeSessionId"
          description="暂无消息，在下方输入问题开始对话"
          :image-size="80"
        />
        <div
          v-for="(m, i) in messages"
          :key="m.id ?? `local-${i}`"
          class="bubble"
          :class="m.role"
        >
          <template v-if="m.role === 'assistant'">
            <!-- 流式思考过程（生成中展开） -->
            <div
              v-if="m.showReasoningLive && m.reasoning"
              class="reasoning-live"
            >
              <div class="reasoning-label">
                <span class="dot-pulse" /> AI 思考中...
              </div>
              <div class="reasoning-text">{{ m.reasoning }}</div>
            </div>

            <div
              v-else-if="m.streaming && !m.content && !m.reasoning"
              class="content loading"
            >
              思考中...
            </div>

            <!-- 最终答案 -->
            <div v-if="m.content" class="content assistant-md">
              <ChatMarkdown :content="m.content" />
            </div>

            <!-- 完成后折叠的思考过程 -->
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

          <div v-else-if="m.content" class="content">{{ m.content }}</div>

          <el-alert
            v-if="m.noContext"
            title="当前课程暂无相关资料，以下为通用建议"
            type="warning"
            :closable="false"
            show-icon
            class="ctx-alert"
          />
          <div v-if="m.citations?.length" class="citations">
            <el-tag v-for="c in m.citations" :key="c.chunk_id" size="small" type="info">
              来自第 {{ c.page ?? '?' }} 页
            </el-tag>
          </div>
        </div>
      </div>
      <div class="composer">
        <el-input
          v-model="input"
          type="textarea"
          :rows="3"
          placeholder="向 AI 助教提问..."
          @keydown.ctrl.enter="send"
        />
        <el-button type="primary" :loading="sending" @click="send">发送 (Ctrl+Enter)</el-button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.chat-layout {
  display: flex;
  gap: 12px;
  min-height: 70vh;
}

.sidebar {
  width: 240px;
  background: #fff;
  border-radius: 8px;
  padding: 12px;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  padding: 12px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  max-height: 60vh;
  padding: 8px;
  min-height: 200px;
}

.bubble {
  margin-bottom: 16px;
  max-width: 85%;
}

.bubble.assistant {
  max-width: 92%;
}

.bubble.user {
  margin-left: auto;
  text-align: right;
}

.bubble.user .content {
  background: #409eff;
  color: #fff;
}

.bubble.assistant .content {
  background: #f4f4f5;
  color: #303133;
}

.bubble.assistant .content.assistant-md {
  display: block;
  width: 100%;
  min-width: 280px;
}

.bubble.assistant .content.loading {
  color: #909399;
  font-style: italic;
}

.content {
  display: inline-block;
  padding: 10px 12px;
  border-radius: 8px;
  white-space: pre-wrap;
  text-align: left;
}

.reasoning-live {
  margin-bottom: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fafafa;
  border: 1px dashed #dcdfe6;
}

.reasoning-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}

.dot-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #409eff;
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.reasoning-text {
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}

.reasoning-text.muted {
  margin-top: 8px;
  max-height: 160px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 6px;
}

.reasoning-collapsed {
  margin-top: 8px;
}

.reasoning-toggle {
  border: none;
  background: none;
  color: #909399;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}

.reasoning-toggle:hover {
  color: #409eff;
}

.citations {
  margin-top: 6px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.ctx-alert {
  margin-top: 8px;
}

.composer {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  margin-top: 12px;
}

.session-list {
  margin-top: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 8px;
  height: 40px;
  border-radius: 4px;
  cursor: pointer;
  color: #303133;
}

.session-item:hover {
  background: #f5f7fa;
}

.session-item.active {
  color: #409eff;
  background: #ecf5ff;
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
  opacity: 0;
  padding: 4px;
}

.session-item:hover .session-delete,
.session-item.active .session-delete {
  opacity: 1;
}
</style>
