# 05_Python_项目查缺补漏与实现审计报告

> **项目名称**：慧编学伴——智能编程学习助教系统  
> **审计日期**：2026-06-08  
> **对照文档**：`root_data/01_慧编学伴——智能编程学习助教系统的设计与实现.pdf`  
> **检查重点**：Python 后端业务逻辑 · 前端 UI · 数据库（MySQL / Redis / 向量数据库）  
> **关联报告**：`04_Python_功能与技术栈分析总结.md`  
> **开发规范**：`root_data/SKILL/01_skill.md`（Python 主语言、模块测试、逻辑外键、接口一致性）；Phase 3 起另见 **`root_data/SKILL/02_skill.md`**

---

## 〇、审计范围与重要说明

### 0.1 代码库现状

在当前工作目录 `Intelligent_programming` 下检索结果如下：

| 检查项 | 结果 |
|--------|------|
| `requirements.txt` / `pyproject.toml` / FastAPI 工程 | **未发现** |
| `backend/app/main.py` 等 Python 业务代码 | **未发现** |
| `package.json` / Vue 前端工程 | **未发现** |
| `.env.example` / Alembic 迁移 / `schema.sql` | **未发现** |
| 工作区现有内容 | `root_data` 设计 PDF + `out_data` 报告目录 + `test/path_test.py` |

**结论**：本次审计为 **「设计文档 + Python 技术路线 → 可实现性 / 完整性」** 的查缺补漏，并给出 **Python 落地实现时的对照清单**。若源码位于其他路径，请将 `backend/` 与 `frontend/` 放入本仓库后做 **第二轮代码级审计**（对照本报告第三节～第五节逐项勾选）。

### 0.2 审计方法

- 在 03 号 Java 版审计结论基础上，**保留全部业务 Gap**，并将实现建议 **映射为 Python/FastAPI 技术栈**。
- 标注原 PDF 中 **Spring Boot / Spring AI** 相关表述在 Python 版中的 **等价实现**。
- 按六大功能模块拆解应有业务规则、接口、页面与表结构。
- 评估文档描述的合理性与可实现风险。
- 标出 **缺失（Gap）**、**模糊（Ambiguous）**、**过度（Over-scope）** 三类问题。
- 对 MySQL / Redis / 向量库分别给出建议 schema 与使用规范（**逻辑外键，不在 DB 层建物理外键**，符合 skill 规范）。

### 0.3 Java → Python 审计对照说明

| 03 号（Java）检查项 | 05 号（Python）等价检查 |
|--------------------|------------------------|
| Spring Boot 工程 / `pom.xml` | `backend/` + FastAPI + `requirements.txt` |
| Spring Security + JWT | `app/core/security.py` + Depends 鉴权 |
| Spring AI `Flux` + SSE | FastAPI `StreamingResponse` + async generator |
| `@Async` / MQ | Celery task / ARQ job |
| MyBatis / JPA | SQLAlchemy Model + Repository 模式 |
| Actuator `/health` | `GET /health` + DB/Redis/向量库 ping |
| Swagger | FastAPI 自动生成 `/docs` |
| POI / PDFBox | pdfplumber / python-pptx / python-docx |

---

## 一、总体评估

| 维度 | 评分（设计完整度） | 摘要 |
|------|-------------------|------|
| 需求与模块划分 | ★★★★☆ | 角色清晰、模块边界合理，场景链路完整 |
| 技术选型一致性（Python 版） | ★★★★☆ | FastAPI + LangChain + Vue3 主线明确，与 AI 场景匹配 |
| 后端业务可落地性 | ★★★☆☆ | 状态机、边界条件、API 契约、Pydantic Schema 未写清 |
| 前端信息架构 | ★★★☆☆ | 页面类型有暗示，缺路由/权限/交互细则 |
| 数据模型 | ★★☆☆☆ | 未给出 ER 图与表清单；Redis/向量库 Key 规范缺失 |
| 非功能（安全/性能/成本） | ★★★☆☆ | JWT、审核、限流概念有，缺量化指标 |
| Python 工程规范 | ★★☆☆☆ | 缺目录结构、测试策略、Celery 任务约定、`.env` 模板 |

**整体判断**：作为毕设开题/方案质量较好；作为 **可直接编码的 Python 规格说明** 仍缺约 30%～40% 的细节。实现前需补齐：**Pydantic 契约 + 数据字典 + Alembic 初版迁移 + 核心流程状态机 + 模块级 pytest 计划**。

**相对 Java 版的额外优势**：RAG、文档解析、Embedding 可在单进程/单语言内闭环，**消除「Java 调 Python 脚本」部署 Gap**（原 03 号报告第六节已标注为低风险项，Python 版可彻底移除）。

---

## 二、分模块查缺补漏（业务细节与 Python 实现建议）

### 2.1 智能代码讲解模块

#### 文档已有

- 语法 / 语义 / 运行三级分析；多语言；结构化输出（建议、分步、常见错误）。

#### 合理性

- ✅ 与 OJ 差异化明确，符合教学场景。
- ⚠️ 「运行级分析」若不在沙箱执行用户代码，只能依赖静态分析 + LLM 推测，**准确性需降级表述**或接入 **Judge0 API** / Docker 沙箱（`app/services/sandbox.py`）。

#### 后端应实现但文档未细化（Gap）

| 编号 | 缺失项 | Python 实现建议 |
|------|--------|----------------|
| B1-01 | 代码提交实体：语言、源码、课程 ID、作业 ID、版本号 | SQLAlchemy 模型 `CodeSubmission`；Alembic 迁移 |
| B1-02 | 讲解结果结构化 JSON Schema | **Pydantic** 模型：`AnalysisResult(level, issues[], suggestions[], examples[])` |
| B1-03 | 与真实编译/运行结果联动 | `httpx` 调 Judge0；或将 `stderr` 注入 LangChain Prompt |
| B1-04 | Token 与费用控制 | Redis `rate:llm:{userId}`；超长代码截断 + tiktoken 计数 |
| B1-05 | 异步任务 | **Celery** `analyze_code_task`；前端轮询 `GET /api/code/{id}/status` 或 WebSocket |

#### 前端应实现但文档未细化（Gap）

| 编号 | 缺失项 | 建议 |
|------|--------|------|
| F1-01 | 类 IDE 编辑器 | Monaco / CodeMirror，语法高亮、语言切换 |
| F1-02 | 分级结果 Tab | 语法 / 语义 / 运行 分页展示，可复制修改建议 |
| F1-03 | 历史提交对比 | 时间线 + diff 视图 |

#### 数据库（Gap）

- MySQL：`code_submission`、`analysis_result`（JSON 字段用 SQLAlchemy `JSON` 类型）。
- Redis：提交频控 `rate:submit:{userId}`；缓存 `analysis:{submissionId}` TTL 1h。
- 向量库：**非必需**；可选 embedding 错误摘要做相似案例检索。

#### Python 模块测试（skill 要求）

- [ ] `tests/test_code_analysis.py`：Mock LLM 返回，断言 Pydantic 解析与落库。
- [ ] 超长代码截断、语言枚举校验、未授权课程访问 403。

---

### 2.2 AI 一对一对话辅导模块

#### 文档已有

- 多轮对话、知识点串联、例题推荐；结合课程知识库。

#### 合理性

- ✅ 教学场景核心功能。
- ⚠️ 未区分「课程内问答」与「通用编程问答」的**策略开关**。

#### 后端 Gap

| 编号 | 缺失项 | Python 实现建议 |
|------|--------|----------------|
| B2-01 | 会话与消息模型 | `ChatSession`、`ChatMessage` ORM；role/content/token/refs |
| B2-02 | 上下文窗口管理 | Redis `ctx:chat:{sessionId}`；LangChain `ConversationBufferWindowMemory` 或自研摘要 |
| B2-03 | RAG 检索流程 | `app/services/rag.py`：查询改写 → Chroma similarity_search → Prompt → 返回 citation IDs |
| B2-04 | 敏感词 / 提示注入防护 | 固定 system prompt；用户输入 regex 过滤；禁止 user 覆盖 system |
| B2-05 | 流式响应 | FastAPI `StreamingResponse` + async generator；`text/event-stream` |

#### 前端 Gap

| 编号 | 缺失项 | 建议 |
|------|--------|------|
| F2-01 | 聊天 UI | 气泡、Markdown、代码块高亮、引用资料卡片 |
| F2-02 | 会话列表 | 按课程/时间分组；新建/删除会话 |
| F2-03 | 「是否在课程范围内」提示 | 无检索命中时 UI 明示 |

#### 数据库 Gap

- MySQL：会话、消息、可选 `message_citation`（chunk_id，逻辑外键）。
- Redis：会话活跃上下文、流式临时缓冲。
- 向量库：**RAG MVP 必需**；Chroma collection 按 `course_id` metadata 隔离。

#### Python 模块测试

- [ ] `tests/test_chat_rag.py`：Mock 向量检索为空/有命中两种路径。
- [ ] SSE 流式接口集成测试（httpx AsyncClient stream）。

---

### 2.3 课程知识库管理模块

#### 文档已有

- 教师上传 PPT/示例；解析、结构化 + 向量检索。

#### 合理性

- ✅ 系统差异化关键。
- ⚠️ PPT 自动结构化工作量被低估；MVP 限定 **PDF / txt / md + 手动分段**。

#### 后端 Gap

| 编号 | 缺失项 | Python 实现建议 |
|------|--------|----------------|
| B3-01 | 上传流水线状态机 | Enum：`UPLOADED → PARSING → CHUNKING → EMBEDDING → READY / FAILED` |
| B3-02 | 文件存储 | 本地 `uploads/{course_id}/` 或 MinIO；MySQL 仅存元数据 |
| B3-03 | 切片策略 | `app/services/chunking.py`：按标题/页/token 长度；保留 `source_page` |
| B3-04 | 重索引与版本 | 资料更新 → Celery 删旧 Chroma vectors + 重建 |
| B3-05 | 权限 | FastAPI Depends：教师 role + `course_teacher` 归属校验 |

#### 前端 Gap

| 编号 | 缺失项 | 建议 |
|------|--------|------|
| F3-01 | 资料管理页 | 列表、上传进度、解析失败重试 |
| F3-02 | 切片预览（教师） | 查看分块效果，手动合并/拆分（P2） |
| F3-03 | 引用溯源展示 | 学生端显示「来自第 X 页 / 文件名」 |

#### 数据库 Gap

| 存储 | 建议表/结构 |
|------|------------|
| MySQL | `course`、`course_material`（type, status, file_path, version）、`material_chunk` |
| Redis | Celery broker、解析任务状态 `material:status:{id}` |
| 向量库 | Chroma metadata：`course_id`, `material_id`, `chunk_id`, `page` |

#### Python 模块测试

- [ ] `tests/test_material_pipeline.py`：上传 PDF → Mock 解析 → 切片数量断言。
- [ ] 失败重试与状态机非法跳转拒绝。

---

### 2.4 学习分析与个性化推荐模块

#### 文档已有

- 行为采集；规则引擎；错题本、复习计划。

#### 合理性

- ✅ 用规则降低成本，毕设友好。
- ⚠️ 统计用 SQL/Python 规则完成，LLM 仅润色文案。

#### 后端 Gap

| 编号 | 缺失项 | Python 实现建议 |
|------|--------|----------------|
| B4-01 | 行为事件埋点 | `LearningEvent` 模型；API `POST /api/learning/events` |
| B4-02 | 知识点体系 | `KnowledgePoint` 树形表；题目/错误映射 |
| B4-03 | 掌握度算法 | `app/services/mastery.py`：错题权重 + 时间衰减 |
| B4-04 | 推荐 API | `GET /api/learning/recommendations?courseId=` |
| B4-05 | 定时任务 | Celery beat：每日 `aggregate_class_stats` |

#### 前端 Gap

| 编号 | 缺失项 | 建议 |
|------|--------|------|
| F4-01 | 学生仪表盘 | 学习时长、正确率趋势、薄弱知识点 |
| F4-02 | 错题本页 | 筛选语言/知识点/是否已掌握 |
| F4-03 | 推荐卡片 | 一键跳转练习或资料 |

#### 数据库 Gap

- MySQL：`learning_event`、`wrong_question_book`、`user_kp_mastery`、`daily_stat_agg`。
- Redis：`cache:dashboard:{userId}` TTL 5～15min。

#### Python 模块测试

- [ ] 掌握度公式单元测试（固定输入 → 期望分数）。
- [ ] 推荐 API 仅返回当前用户有权限的课程数据。

---

### 2.5 教师教学支持模块

#### 文档已有

- 作业、班级学情、资源审核、AI 回答审核；ECharts 可视化。

#### 合理性

- ✅ 体现 B 端价值。
- ⚠️ 「AI 回答审核」流程未定义：全量还是抽样？未审核是否对学生可见？

#### 后端 Gap

| 编号 | 缺失项 | Python 实现建议 |
|------|--------|----------------|
| B5-01 | 班级-课程-学生关系 | `Class`、`ClassStudent`、`TeacherCourse` 模型 |
| B5-02 | 作业生命周期 | 状态 Enum + 迟交策略 |
| B5-03 | 审核工作流 | `AiAnswerAudit`：pending/approved/rejected |
| B5-04 | 统计 API | SQLAlchemy 聚合 + Pydantic 响应；注意隐私脱敏 |
| B5-05 | 导出 | `StreamingResponse` CSV |

#### 前端 Gap

| 编号 | 缺失项 | 建议 |
|------|--------|------|
| F5-01 | 教师工作台 | 课程卡片、待审核红点 |
| F5-02 | 班级学情大屏 | ECharts 折线/柱状/雷达 |
| F5-03 | 审核队列页 | 学生问题 / AI 草稿 / 引用 / 教师修订对比 |

#### 数据库 Gap

- MySQL：`assignment`、`assignment_submit`、`ai_answer_audit`、`class_statistics`。
- Redis：审核待办计数 `audit:pending:{teacherId}`。

---

### 2.6 系统管理模块

#### 文档已有

- 用户角色、AI 配置、日志、备份。

#### 后端 Gap

| 编号 | 缺失项 | Python 实现建议 |
|------|--------|----------------|
| B6-01 | RBAC 模型 | `User.role` Enum + FastAPI `require_roles(["admin"])` 依赖 |
| B6-02 | API Key 加密存储 | `cryptography.fernet` 或环境变量；禁止明文日志 |
| B6-03 | 操作审计 | `OperationLog` 模型；中间件记录 who/what/ip |
| B6-04 | 多模型路由 | `app/core/llm_router.py`：场景 → model 映射（讲解/聊天） |
| B6-05 | 健康检查 | `GET /health`：MySQL `SELECT 1`、Redis ping、Chroma heartbeat、LLM 探活 |

#### 前端 Gap

- 管理员：用户 CRUD、角色分配、系统参数、日志查询。
- 登录/注册/忘记密码、403/404 统一页。

#### 数据库 Gap

- MySQL：`sys_config`、`operation_log`、`api_key_config`（加密字段）。
- Redis：JWT 黑名单 `jwt:blacklist:{jti}`、登录失败锁定。

---

## 三、Python 后端业务逻辑专项检查清单

> 实现后请逐项打勾；当前均为 **未实现 / 待验证**。

### 3.1 横切能力

| 检查项 | 状态 | Python 实现说明 |
|--------|------|----------------|
| 统一响应体 `ApiResponse[T]` | ⬜ | Pydantic 泛型 + 全局 exception_handler |
| 参数校验 | ⬜ | Pydantic Field 约束 + HTTP 422 中文 message |
| JWT 签发/刷新/登出 | ⬜ | python-jose；Redis 存 refresh / blacklist |
| 接口幂等 | ⬜ | Header `Idempotency-Key` + Redis SETNX |
| 分页规范 | ⬜ | `page_num` / `page_size` Query 参数统一 |
| OpenAPI 文档 | ⬜ | FastAPI 自带 `/docs`、`/redoc` |
| LLM 抽象层 | ⬜ | `LLMService` 接口；LiteLLM 切换 DeepSeek/通义 |
| Prompt 模板外置 | ⬜ | DB `sys_config` 或 `prompts/*.yaml` |
| LLM 调用日志 | ⬜ | `ai_invoke_log` 表 + structlog |
| 限流 | ⬜ | `slowapi` 或 Redis 滑动窗口 |
| CORS | ⬜ | 前端 dev/prod 域名白名单 |
| 类型检查（可选） | ⬜ | mypy strict 核心模块 |

### 3.2 核心业务链路（必须打通）

```
[登录] → [选课程] → [上传资料→Celery 解析→向量化] → [学生提问→RAG→SSE 回答]
                → [学生交代码→（可选 Judge0）→讲解结果落库]
                → [记录事件→更新掌握度→推荐列表]
                → [教师查看统计→审核 AI 回答]
```

| 链路节点 | 关键校验 | 状态 |
|----------|----------|------|
| 登录 | 角色路由、passlib bcrypt | ⬜ |
| 资料上传 | 文件类型白名单、大小限制 | ⬜ |
| RAG 问答 | courseId 强制、无资料降级提示 | ⬜ |
| 代码讲解 | 语言 Enum、源码长度上限 | ⬜ |
| 教师审核 | 未审核内容可见策略 | ⬜ |

### 3.3 文档未写但易遗漏的业务规则

1. **学生只能访问已选课程**（垂直越权）— `Depends` 内校验 `course_student`。  
2. **教师只能管理自己授课课程**。  
3. **删除课程**软删除 + Celery 清理向量与文件。  
4. **AI 免责声明**与调用日志留存。  
5. **LLM 熔断**：单用户短时间超额 → 429。  
6. **逻辑外键**：ORM 层维护关联，MySQL **不建物理 FOREIGN KEY**（skill 规范）。  
7. **表字段命名统一**：建议全 snake_case，每张表含 `id, created_at, updated_at, deleted`。

---

## 四、前端 UI 专项检查清单

> 与 03 号报告一致；接口基址改为 FastAPI 服务地址。

### 4.1 信息架构（建议路由）

| 角色 | 路由示例 | 文档覆盖 | 建议优先级 |
|------|----------|----------|------------|
| 公共 | `/login`, `/register` | 隐含 | P0 |
| 学生 | `/student/courses`, `/student/chat`, `/student/code`, `/student/wrong-book`, `/student/dashboard` | 部分 | P0～P1 |
| 教师 | `/teacher/courses`, `/teacher/materials`, `/teacher/class/:id/stats`, `/teacher/audit`, `/teacher/assignments` | 部分 | P0～P1 |
| 管理 | `/admin/users`, `/admin/config`, `/admin/logs` | 有 | P1 |

### 4.2 UI/UX Gap

| 编号 | 问题 | 建议 |
|------|------|------|
| UI-01 | 无设计稿 | Element Plus 主题色、8px 栅格 |
| UI-02 | 长等待无反馈 | AI 请求 Loading / SSE 打字效果 |
| UI-03 | 移动端 | 声明 PC 优先，基本响应式 |
| UI-04 | 错误提示 | 表单校验中文；网络重试 |
| UI-05 | 权限路由守卫 | Pinia 存 role；`beforeEach` 跳转 |
| UI-06 | API 基址 | `.env.development` 指向 `http://localhost:8000` |

### 4.3 与 Python 后端契约

- 列表分页字段与 3.1 节一致。  
- 聊天/讲解：**SSE** `Content-Type: text/event-stream`。  
- 文件上传：`UploadFile` + 前端 `multipart/form-data` + 轮询 `materialId` 解析状态。  
- 统一错误码：业务异常 HTTP 200 + `code != 0` 或 HTTP 4xx（团队择一并写进 `docs/api-convention.md`）。

---

## 五、数据库专项检查（MySQL / Redis / 向量库）

### 5.1 MySQL — 建议核心表（逻辑外键）

| 域 | 表名 | 核心字段（摘要） |
|----|------|-----------------|
| 用户 | `user` | id, username, password_hash, role, status |
| 课程 | `course`, `course_student`, `course_teacher` | 课程元数据、选课关系 |
| 资料 | `course_material`, `material_chunk` | 文件、解析状态、文本块 |
| 代码 | `code_submission`, `analysis_result` | 源码、语言、AI 分析 JSON |
| 对话 | `chat_session`, `chat_message` | 多轮记录 |
| 学习 | `learning_event`, `wrong_question_book`, `user_kp_mastery` | 行为与掌握度 |
| 作业 | `assignment`, `assignment_submit` | 作业与提交 |
| 审核 | `ai_answer_audit` | 审核状态与修订内容 |
| 系统 | `sys_config`, `operation_log`, `ai_invoke_log` | 配置与审计 |

**Gap（文档级）**：

- ❌ 无 ER 图、无 Alembic 初版迁移。
- ❌ 未统一 `deleted`、`created_at`、`updated_at`。
- ❌ skill 要求：**逻辑外键**需在 `docs/database.md` 中画出关系说明。

**建议索引**（与 03 号一致）：

- `learning_event(user_id, course_id, created_at)`
- `chat_message(session_id, created_at)`
- `code_submission(user_id, course_id, created_at)`
- `material_chunk(material_id, seq)`

**Python 落地动作**：

- [ ] `alembic revision --autogenerate -m "init"` 生成初版迁移  
- [ ] `scripts/seed_demo.py` 插入演示用户/课程/资料  

### 5.2 Redis — 建议使用场景

| Key 模式 | 类型 | TTL | 用途 |
|----------|------|-----|------|
| `refresh:token:{uuid}` | String | 7d | 刷新令牌 |
| `jwt:blacklist:{jti}` | String | 至 token 过期 | 登出失效 |
| `rate:llm:{userId}` | String 计数 | 1d | LLM 日调用上限 |
| `cache:dashboard:{userId}` | JSON | 10min | 学生仪表盘 |
| `cache:class_stats:{classId}` | JSON | 15min | 教师统计 |
| `ctx:chat:{sessionId}` | JSON | 2h | 对话上下文 |
| `lock:material:parse:{id}` | 分布式锁 | 短 | 防重复解析 |
| Celery broker | List/Stream | — | 异步任务队列 |

**Gap**：写后删缓存策略需在 Service 层统一（如 `invalidate_dashboard(user_id)`）。

### 5.3 向量数据库 — ChromaDB / FAISS / Milvus

| 检查项 | 文档 | Python 版建议 |
|--------|------|--------------|
| MVP 选型 | 扩展项 | **ChromaDB 持久化目录** `./data/chroma`；单机答辩足够 |
| 集合划分 | 未写 | metadata 过滤 `course_id`；或每课程一个 collection |
| 向量维度 | 未写 | 与 embedding 模型一致（如 1536 / 1024） |
| 元数据 | 未写 | `chunk_id, material_id, page, title` |
| 一致性 | 未写 | 删 chunk → `vector_store.delete(ids=[...])` |
| 抽象层 | 未写 | `app/services/vector_store.py` 统一接口，便于换 Milvus/pgvector |

**合理性**：Python 版 **MVP 直接上 Chroma** 比 Java 版 SimpleVectorStore 更自然；答辩稳定后再迁 Milvus。

---

## 六、跨模块一致性与风险

| 风险 | 等级 | 说明 | Python 版缓解 |
|------|------|------|--------------|
| LLM 幻觉 / 偏离课程 | 高 | 无 RAG 体验差 | 强制 courseId + 无命中拒答/弱答 |
| API 费用超支 | 高 | 无限额 | Redis 限流 + 管理员配额 |
| 代码执行安全 | 高 | 本地 exec 危险 | **禁止** `eval`/`exec` 用户代码；Judge0 或仅静态+LLM |
| 资料解析失败 | 中 | PPT 复杂 | MVP：PDF/txt/md |
| 学情隐私 | 中 | 班级排名 | 学生只见自己 |
| LangChain 版本漂移 | 中 | API 频繁变更 | 锁定 requirements；核心 RAG 可薄封装 |
| Celery 运维 | 低 | 多进程 | Docker Compose 同栈启动 worker |
| GIL / CPU 密集 | 低 | Embedding 阻塞 | Celery worker 独立进程 |

---

## 七、优先级整改路线图（建议 4 周 MVP — Python 版）

### 第 1 周：地基

- [ ] 初始化 `backend/`：FastAPI + SQLAlchemy + Alembic + Redis + JWT  
- [ ] 初始化 `frontend/`：Vue3 + Router + Pinia + Element Plus  
- [ ] 用户/角色/课程 CRUD + 登录联调  
- [ ] 输出 ER 图 + 初版 Alembic 迁移 + `docs/database.md`（逻辑外键说明）  
- [ ] `pytest` 基础设施：`conftest.py` + 测试数据库  

### 第 2 周：内容与 AI 主链

- [ ] 资料上传 + pdfplumber 解析 + 切片入 MySQL  
- [ ] ChromaDB Embedding + RAG 问答 API  
- [ ] 学生聊天页（SSE）+ 引用展示  
- [ ] **模块测试**：资料流水线 + RAG 单测通过  

### 第 3 周：编程辅导与学情

- [ ] 代码提交 + LangChain 结构化讲解 + 落库  
- [ ] 学习事件埋点 + 错题本 + 规则推荐  
- [ ] 教师班级 ECharts 统计  
- [ ] **模块测试**：代码讲解 Schema + 推荐 API  

### 第 4 周：闭环与答辩

- [ ] 教师审核流（列表 + 通过/驳回）  
- [ ] 管理员 AI Key、限流配置  
- [ ] `/health` + Docker Compose 部署文档 + 演示数据集  
- [ ] 全模块测试报告 + API 文档导出（`/docs` 截图）  

---

## 八、审计结论

1. **设计层面**：业务模块与原 PDF 一致；迁移至 Python 后，**AI/RAG/文档解析路径更短**，有利于毕设周期内完成 MVP。  
2. **实现层面**：当前仓库 **尚无 Python 后端与 Vue 前端源码**；上述 Gap 均为「按设计应收尾」项。  
3. **数据库层面**：需尽快 Alembic 落库；Redis Key 规范成文；向量库建议 Chroma MVP。  
4. **规范层面**：须遵守 `01_skill.md`——**每完成一模块运行 pytest**、**逻辑外键**、**接口字段一致**。  
5. **下一步**：按 04 号报告目录结构创建工程，依据本报告 **第三节～第五节** 做实现与第二轮代码审计。

---

## 附录 A：建议 REST API 分组（FastAPI 路由）

| 前缀 | 模块 | 路由文件建议 |
|------|------|-------------|
| `/api/v1/auth` | 登录、刷新、登出 | `api/v1/auth.py` |
| `/api/v1/courses` | 课程、选课 | `api/v1/courses.py` |
| `/api/v1/materials` | 上传、解析状态、切片 | `api/v1/materials.py` |
| `/api/v1/chat` | 会话、消息、SSE | `api/v1/chat.py` |
| `/api/v1/code` | 提交、讲解结果 | `api/v1/code.py` |
| `/api/v1/learning` | 事件、错题本、推荐 | `api/v1/learning.py` |
| `/api/v1/assignments` | 作业 | `api/v1/assignments.py` |
| `/api/v1/teacher` | 班级统计、审核 | `api/v1/teacher.py` |
| `/api/v1/admin` | 用户、配置、日志 | `api/v1/admin.py` |
| `/health` | 健康检查 | `main.py` |

## 附录 B：与 02 / 03 / 04 号报告的关系

| 报告 | 定位 |
|------|------|
| **02** | Java 版：从 PDF 归纳模块与技术 |
| **03** | Java 版：查缺补漏与落地清单 |
| **04** | **Python 版：功能与技术栈（本文档姊妹篇）** |
| **05** | **Python 版：查缺补漏（保留 03 业务 Gap，替换为 FastAPI 实现建议）** |

## 附录 C：建议首批交付文档（skill 要求）

| 文档 | 路径建议 |
|------|----------|
| 数据库设计（逻辑外键） | `docs/database.md` |
| API 约定 | `docs/api-convention.md` |
| 部署说明 | `docs/deploy.md` |
| 环境变量模板 | `backend/.env.example` |
| 模块测试说明 | `docs/testing.md` |

---

*报告结束。请将 `backend/` 与 `frontend/` 置于本仓库后，依据本清单进行代码级审计与 pytest 覆盖率补充。*
