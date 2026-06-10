import request from './request'

export interface ChatSession {
  id: number
  course_id: number
  title: string
  created_at: string
}

export interface Citation {
  chunk_id: number
  page: number | null
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
  citations: Citation[]
  no_context?: boolean
}

function getAccessToken(): string {
  return sessionStorage.getItem('access_token') || ''
}

export function listSessions(courseId: number): Promise<ChatSession[]> {
  return request.get('/api/v1/chat/sessions', { params: { course_id: courseId } })
}

export function createSession(courseId: number, title = '新对话'): Promise<ChatSession> {
  return request.post('/api/v1/chat/sessions', { course_id: courseId, title })
}

export function listSessionMessages(sessionId: number): Promise<ChatMessage[]> {
  return request.get(`/api/v1/chat/sessions/${sessionId}/messages`)
}

export function deleteSession(sessionId: number): Promise<null> {
  return request.delete(`/api/v1/chat/sessions/${sessionId}`)
}

export async function streamChatMessage(
  sessionId: number,
  content: string,
  onContentDelta: (delta: string) => void,
  onDone: (payload: {
    citations: Citation[]
    no_context?: boolean
    session_title?: string
  }) => void,
  onError: (message: string) => void,
  onReasoningDelta?: (delta: string) => void,
): Promise<void> {
  const token = getAccessToken()
  if (!token) {
    onError('未登录，请重新登录')
    return
  }

  const resp = await fetch(
    `${import.meta.env.VITE_API_BASE}/api/v1/chat/sessions/${sessionId}/messages`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({ content }),
    },
  )

  const contentType = resp.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    const payload = await resp.json()
    if (payload.code !== 0) {
      onError(payload.message || '请求失败')
      return
    }
  }

  if (!resp.ok || !resp.body) {
    onError(resp.status === 500 ? 'AI 服务异常，请重启后端后重试' : '请求失败')
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let receivedContent = false

  const processPart = (part: string) => {
    const lines = part.split('\n')
    let event = 'message'
    let data = ''
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed.startsWith('event:')) event = trimmed.slice(6).trim()
      if (trimmed.startsWith('data:')) data = trimmed.slice(5).trim()
    }
    if (!data) return
    const parsed = JSON.parse(data)
    if (event === 'error') {
      onError(parsed.message || 'AI 调用失败')
      throw new Error('stream_error')
    }
    if (parsed.done) {
      onDone({
        citations: parsed.citations || [],
        no_context: parsed.no_context,
        session_title: parsed.session_title,
      })
    } else if (parsed.reasoning_delta && onReasoningDelta) {
      receivedContent = true
      onReasoningDelta(parsed.reasoning_delta)
    } else if (parsed.delta) {
      receivedContent = true
      onContentDelta(parsed.delta)
    }
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        processPart(part)
      }
    }
    if (buffer.trim()) {
      processPart(buffer)
    }
    if (!receivedContent) {
      onError('未收到 AI 回复内容')
    }
  } catch (err) {
    if (err instanceof Error && err.message !== 'stream_error') {
      onError(err.message || '流式响应解析失败')
    }
  }
}
