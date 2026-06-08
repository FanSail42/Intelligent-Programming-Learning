# API 约定规范

> **项目**：慧编学伴——智能编程学习助教系统  
> **版本**：Phase 0 初版  
> **Base URL**：`http://localhost:8000`  
> **API 前缀**：`/api/v1`（业务接口）；健康检查 `/health` 无前缀

---

## 1. 统一响应体

所有 JSON 接口（SSE 除外）采用统一包装：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | `0` 表示成功；非 0 为业务错误码 |
| `message` | string | 人类可读提示 |
| `data` | T \| null | 业务数据；无数据时为 `null` |

### 1.1 错误策略（全文统一）

**采用：HTTP 200 + `code != 0` 表示业务错误。**

- 成功：`HTTP 200` + `code: 0`
- 业务错误（参数校验、权限不足、资源不存在等）：`HTTP 200` + `code != 0`
- 系统级错误（未捕获异常）：`HTTP 500`

常见业务错误码（Phase 1 起在 `app/core/exceptions.py` 实现）：

| code | 含义 |
|------|------|
| 0 | 成功 |
| 40001 | 参数校验失败 |
| 40101 | 未登录或 Token 无效 |
| 40301 | 无权限 |
| 40401 | 资源不存在 |
| 42901 | 请求过于频繁（限流） |
| 50001 | 内部服务错误 |

---

## 2. 分页约定

### 2.1 请求参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page_num` | int | 1 | 页码，从 **1** 开始 |
| `page_size` | int | 10 | 每页条数，最大 **100** |

示例：`GET /api/v1/courses?page_num=1&page_size=10`

### 2.2 分页响应

`data` 字段结构：

```json
{
  "list": [],
  "total": 0,
  "page_num": 1,
  "page_size": 10
}
```

---

## 3. 认证

### 3.1 Header

```
Authorization: Bearer <access_token>
```

### 3.2 Token 类型

| Token | 用途 | 存储（前端） |
|-------|------|-------------|
| access_token | API 鉴权 | Pinia + sessionStorage |
| refresh_token | 刷新 access_token | Pinia + sessionStorage |

---

## 4. 时间与 ID

| 项 | 约定 |
|----|------|
| 时间格式 | ISO 8601 字符串 `YYYY-MM-DDTHH:mm:ss`（无时区，服务器本地/UTC 需在 deploy 文档说明） |
| ID 类型 | **int64**（数据库自增主键），JSON 中以 number 传输 |

---

## 5. REST 路径规范

- 资源名使用复数：`/api/v1/courses`、`/api/v1/materials`
- 路径参数：`/api/v1/courses/{id}`
- 子资源：`/api/v1/courses/{id}/join`
- 动词型操作（非 CRUD）：`POST /api/v1/auth/login`

---

## 6. SSE 流式约定（Phase 2 聊天）

### 6.1 请求

```
POST /api/v1/chat/sessions/{id}/messages
Content-Type: application/json
Accept: text/event-stream
Authorization: Bearer <token>
```

### 6.2 事件格式

```
event: message
data: {"delta": "部分内容", "done": false}

event: message
data: {"delta": "", "done": true, "citations": [{"chunk_id": 1, "page": 3}]}

event: error
data: {"code": 50001, "message": "LLM 调用失败"}
```

| 字段 | 说明 |
|------|------|
| `delta` | 增量文本 |
| `done` | 是否结束 |
| `citations` | 引用来源（仅最后一包） |

SSE 响应 **不** 使用统一 `{code, message, data}` 包装；错误通过 `event: error` 传递。

---

## 7. 文件上传（Phase 2）

- `Content-Type: multipart/form-data`
- 字段名：`file`
- 附加字段：`course_id`（int）
- 白名单：`pdf`、`txt`、`md`
- 单文件上限：20MB

---

## 8. 前端 Axios 拦截器约定

1. 请求拦截：自动附加 `Authorization` Header  
2. 响应拦截：`code === 0` 时返回 `data`；`code !== 0` 时 ElMessage 提示并 reject  
3. 401：清除 Token，跳转 `/login`

---

## 9. 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-06-08 | 0.1 | Phase 0 初版创建 |
