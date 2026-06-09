# M04_AI对话辅导

> **Phase**：2 | **优先级**：P0 | **更新**：2026-06-08

## 1. 业务目标

学生基于已选课程的 RAG 上下文，与 AI 助教进行 SSE 流式多轮对话，回答附带资料引用。

## 2. 用例与角色

| 用例 | 角色 | 说明 |
|------|------|------|
| 创建/列出会话 | student（已选课） | 按 course_id |
| SSE 问答 | student | TopK 检索 + 流式输出 |
| 教师旁听 | teacher | Phase 2 仅学生发起 |

## 3. 业务规则

1. `course_id` 必填；学生须已选课
2. 向量无命中 → 弱提示「当前课程暂无相关资料」
3. 禁止 eval/exec；system prompt 外置不可被用户覆盖
4. LLM 日调用限流（Redis `rate:llm:{userId}`）
5. 每次 LLM 调用 structlog 记录（Phase 4 落库 ai_invoke_log）

## 4. 数据库表

| 表 | 核心字段 | 逻辑外键 |
|----|---------|---------|
| `chat_session` | user_id, course_id, title | user.id, course.id |
| `chat_message` | session_id, role, content, token_count | chat_session.id |
| `message_citation` | message_id, chunk_id | chat_message.id, material_chunk.id |

## 5. API 列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat/sessions` | 新建会话 |
| GET | `/api/v1/chat/sessions` | 列表 ?course_id= |
| POST | `/api/v1/chat/sessions/{id}/messages` | SSE 流式 |

## 6. SSE 格式

见 `docs/api-convention.md` §6。

## 7. 前端

| 路由 | 说明 |
|------|------|
| `/student/chat` | 会话 + 气泡 + Markdown + 引用卡片 |

## 8. 测试用例

- 有/无检索命中；Mock LLM
- 未选课学生 → 403
- SSE 事件格式校验

## 9. 验收标准

- [x] 学生提问含引用来源（2026-06-09）
- [x] `test_chat_rag.py`、`test_chat_sse.py` 通过（2026-06-09）

## 10. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-06-08 | Phase 2 初版 |
