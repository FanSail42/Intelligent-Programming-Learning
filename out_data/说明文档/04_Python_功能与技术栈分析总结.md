# 04_Python_功能与技术栈分析总结

> **分析依据**：`root_data/01_慧编学伴——智能编程学习助教系统的设计与实现.pdf`（共 9 页）  
> **对照文档**：`02_Java_功能与技术栈分析总结.md`  
> **项目名称**：慧编学伴——智能编程学习助教系统的设计与实现  
> **分析日期**：2026-06-08  
> **技术主线**：FastAPI + LangChain（LLM/RAG）+ Vue3  
> **迁移说明**：原设计以 Java / Spring Boot 为主、Python 为辅助脚本；现按 `root_data/SKILL/01_skill.md` 要求，**后端主语言统一为 Python**，业务功能与模块划分保持不变。

---

## 一、项目概述

### 1.1 定位与目标

面向**高校计算机类课程**（C/C++、Java、Python 等）的**智能编程学习助教系统**，服务对象为**学生**与**教师**，兼顾**管理员**运维。系统以 **FastAPI** 为后端核心，通过 **LLM API + LangChain（或 LiteLLM 统一网关）** 实现代码讲解、IDE 式辅助、对话式学习路径推荐；支持教师构建**课程专属知识库**，使 AI 在教学场景中给出**可解释、分步骤、贴合课程大纲**的辅导，而非泛化闲聊。

### 1.2 与现有方案差异（文档归纳）

| 对比对象 | 主要不足 | 本项目应对 |
|---------|---------|-----------|
| PTA / 校内 OJ | 偏判题，缺个性化辅导与过程化讲解 | 多层级代码讲解 + 修改建议 |
| 慕课 / 录播 | 交互弱、难跟踪个体薄弱点 | 学习轨迹 + 个性化推荐 |
| 通用大模型 | 易偏离课程、难控教学口径 | RAG + 课程知识库 + 教师审核 |

### 1.3 设计原则

- **工程化可控**：不训练自有模型，通过 LangChain / 原生 HTTP 客户端对接商用/开源 API，成本与风险可控。  
- **课程精确化**：教师上传教材/PPT/示例，形成课程知识库。  
- **人机协同**：AI 关键答复可经管理员/教师审核，保证可追溯。  
- **模块化**：按 Python 包划分领域模块，便于分期实现 MVP 与后续扩展。  
- **Python 生态优先**：文档解析、向量化、Prompt 编排、异步任务均在 Python 内完成，**不再依赖 Java 调用 Python 脚本**。

### 1.4 相对原 Java 方案的技术迁移摘要

| 原设计（Java） | Python 替代方案 | 迁移理由 |
|---------------|----------------|---------|
| Spring Boot | **FastAPI** | 异步友好、自动 OpenAPI、SSE 流式响应成熟，与 AI 场景契合 |
| Spring Security + JWT | **FastAPI Security** + python-jose + passlib | 轻量 RBAC，JWT 签发/校验生态成熟 |
| MyBatis / JPA | **SQLAlchemy 2.0** + **Alembic** | Python 主流 ORM，迁移脚本可版本化管理 |
| Spring AI | **LangChain** / **LiteLLM** | Python AI 生态最完整，RAG/Embedding 开箱即用 |
| Apache POI / PDFBox | **pdfplumber** / **python-pptx** / **python-docx** | 纯 Python 解析，部署更简单 |
| `@Async` / MQ | **Celery** + Redis 或 **ARQ** | 资料解析、Embedding 等长任务异步化 |
| Spring Boot Actuator | 自定义 `/health` + **Prometheus** 指标（可选） | 健康探活 + 答辩演示足够 |
| Python 辅助脚本 | **并入主工程** `app/services/` | 消除跨语言调用与部署复杂度 |

---

## 二、角色与用例

> 业务角色与用例与原 PDF / 02 号报告一致，不因技术栈变更而改变。

### 2.1 学生端

| 痛点 | 系统能力 |
|-----|---------|
| 报错难懂、只会给结论 | 语法/语义/运行多级讲解 + 修改建议 |
| 不知下一步学什么 | 基于学习记录的个性化知识推荐 |
| 缺少持续辅导 | 一对一对话式 AI 助教、错题本 |
| 资料分散 | 统一查看课程资料、示例、讲题、作业 |

**核心用例**：智能解题、错误定位、修改建议、个性化推荐、代码个性化辅导、学习记录可视化。

### 2.2 教师端

| 痛点 | 系统能力 |
|-----|---------|
| 难掌握班级学情 | 学习数据可视化、班级分析 |
| 答疑重复、口径不一 | 上传资料 + AI 基于课程库回答 |
| 内容质量难控 | AI 回答审核、内容追溯 |
| 资源分散 | 统一课程资源与作业管理 |

**核心用例**：课程知识库构建、AI 回答可控化、班级学情分析、作业与资源管理。

### 2.3 管理员端

- 用户账号与角色权限分配  
- 系统参数配置（含 AI 模型、API Key 管理）  
- 操作日志与系统监控  
- 数据备份、课程资源审计  

---

## 三、功能模块体系

文档将系统划分为 **6 大功能模块** + **1 个系统管理模块**；以下在保留原业务描述基础上，补充 **Python 实现侧** 的技术落点。

### 3.1 智能代码讲解模块

| 维度 | 说明 |
|-----|------|
| **目标** | 超越 OJ「只显示对错」，提供可理解的调试与教学反馈 |
| **能力** | 语法级、语义级、运行级分析；修改建议；优化提示 |
| **语言** | C/C++、Java、Python（文档明确） |
| **AI 角色** | 结构化返回：调试建议、分步讲解、常见错误提示 |
| **Python 落点** | `app/services/code_analysis.py`；可选 **Judge0** / **subprocess 沙箱** 获取 stderr；Pydantic 定义响应 Schema |
| **典型流程** | 学生提交代码 → LLM +（可选）静态分析 → 结构化 JSON 返回 |

### 3.2 AI 一对一对话式学习辅导模块

| 维度 | 说明 |
|-----|------|
| **目标** | 模拟「编程家教」的持续对话 |
| **能力** | 多轮对话、知识点串联、例题与练习推荐 |
| **约束** | 需结合课程上下文（知识库/RAG），避免脱离教学大纲 |
| **Python 落点** | LangChain `ConversationalRetrievalChain` 或自研 RAG Pipeline；**SSE** 流式输出（`StreamingResponse`） |
| **典型流程** | 学生提问 → 向量检索课程切片 → 拼 Prompt → 分步讲解 + 引用来源 |

### 3.3 课程知识库管理模块

| 维度 | 说明 |
|-----|------|
| **目标** | 将教师资料转化为 AI 可检索的教学上下文 |
| **输入** | 教材、PPT、示例代码、作业等 PDF/Office 文件 |
| **处理** | **pdfplumber / python-pptx / python-docx** 解析 → 切片 → **Embedding** → 写入向量库 |
| **输出** | RAG 检索增强生成；AI 回答可标注来源 |
| **Python 落点** | Celery 任务：`parse_material → chunk → embed`；MVP 可用 **ChromaDB** 或 **FAISS** 本地持久化 |
| **典型流程** | 教师上传 → 异步解析入库 → 问答时 TopK 检索 |

### 3.4 学习分析与个性化推荐模块

| 维度 | 说明 |
|-----|------|
| **目标** | 低成本实现个性化（规则引擎，非核心依赖大模型） |
| **采集** | 做题历史、练习频率、错误类型、知识点掌握度 |
| **输出** | 薄弱点补强、专项练习、复习计划、学习路径建议 |
| **Python 落点** | SQLAlchemy 聚合查询 + 简单 Python 规则函数；文案润色可选单次 LLM 调用 |
| **典型流程** | 记录学习轨迹 → 更新错题本/画像 → 规则推荐 |

### 3.5 教师教学支持模块

| 维度 | 说明 |
|-----|------|
| **目标** | 减轻重复答疑，提升班级管理效率 |
| **能力** | 作业布置与批改辅助、班级学情、资源审核、AI 回答审核 |
| **可视化** | ECharts：错误分布、知识点薄弱图、班级对比等 |
| **Python 落点** | 统计 API 返回 JSON；前端 ECharts 渲染；审核流用状态机 + ORM |
| **典型流程** | 教师查看班级数据 → 调整教学重点 → 审核/订正 AI 答复 |

### 3.6 系统管理模块

| 维度 | 说明 |
|-----|------|
| **用户与权限** | 学生 / 教师 / 管理员；JWT + 依赖注入鉴权 |
| **配置** | AI 模型切换、API Key、Prompt 模板、敏感词过滤 |
| **运维** | structlog 结构化日志、健康检查、备份脚本（`scripts/backup_db.py`） |

### 3.7 关键业务场景串联（文档第 3 页）

```
学生提交代码 → AI 多级分析 → 返回原因与修改建议
学生向 AI 提问 → 基于课程知识库分步讲解
教师上传 PPT/示例 → 构建知识库 → AI 生成课程范围内回答
系统记录学习轨迹 → 更新错题本与画像
教师查看班级数据 → 调整教学策略
管理员维护用户与系统配置
```

---

## 四、技术栈总览

### 4.1 架构形态

**前后端分离**：Vue3 前端 + FastAPI REST API；AI 能力通过 **LangChain / LiteLLM** 统一封装；长任务通过 **Celery + Redis** 异步执行；向量检索与 Embedding **原生 Python 实现**，无跨语言边界。

```
┌─────────────┐     HTTPS/SSE      ┌──────────────────────────────────┐
│  Vue3 前端   │ ◄────────────────► │  FastAPI（API + 鉴权 + 路由）      │
└─────────────┘                    │  ├── services/（业务 + AI + RAG）   │
                                   │  ├── models/（SQLAlchemy）        │
                                   │  └── tasks/（Celery 异步）         │
                                   └──────────┬─────────────┬───────────┘
                                              │             │
                         ┌────────────────────┼─────────────┼────────────┐
                         ▼                    ▼             ▼            ▼
                     MySQL               Redis          Chroma/FAISS   LLM API
                   (业务数据)          (缓存/队列)        (向量/RAG)   (DeepSeek等)
```

### 4.2 后端技术栈（Python）

| 类别 | 技术选型 | 用途 |
|-----|---------|------|
| 核心框架 | **FastAPI** | 业务 API、依赖注入、自动 OpenAPI 文档 |
| ASGI 服务器 | **Uvicorn** + **Gunicorn**（生产） | 运行与多 worker 部署 |
| 安全 | **python-jose** + **passlib[bcrypt]** | JWT 签发/校验、密码哈希 |
| 数据访问 | **SQLAlchemy 2.0** + **Alembic** | ORM、迁移脚本 |
| 数据库驱动 | **PyMySQL** 或 **asyncmy**（异步可选） | 连接 MySQL |
| 参数校验 | **Pydantic v2** | 请求/响应模型、AI 结构化输出 |
| AI 集成 | **LangChain** 或 **LiteLLM** | 对话、RAG、多模型适配 |
| Embedding | **OpenAI 兼容 API** / **sentence-transformers**（本地） | 课程资料向量化 |
| 大模型 API | DeepSeek / 通义千问 / ChatGPT 等 | 讲解、问答、推荐文案 |
| 文档解析 | **pdfplumber**、**python-pptx**、**python-docx** | PDF/Office 课程资料 |
| Markdown | **markdown-it-py**（可选） | 教师上传 md 资料 |
| 异步任务 | **Celery** + Redis 或 **ARQ** | 解析、Embedding、批量统计 |
| HTTP 客户端 | **httpx** | 调用外部 LLM / Judge0 |
| 配置管理 | **pydantic-settings** + `.env` | 环境变量、API Key |
| 日志 | **structlog** / **loguru** | 结构化日志、审计 |
| 测试 | **pytest** + **httpx.AsyncClient** | 单元测试、API 集成测试 |

**备选方案（团队更熟悉全栈 Django 时）**：

| 组件 | Django 替代 |
|-----|------------|
| Web 框架 | Django 5 + **Django REST framework** |
| 异步任务 | Celery（相同） |
| Admin | Django Admin 可快速做管理后台 |
| 流式 SSE | DRF StreamingHttpResponse |

> **推荐默认**：FastAPI + SQLAlchemy，与 LangChain/RAG 生态耦合更紧，毕设答辩时可展示自动生成的 Swagger 文档。

### 4.3 前端技术栈（保持不变）

| 类别 | 技术选型 | 用途 |
|-----|---------|------|
| 框架 | **Vue 3** | SPA 主框架 |
| 路由/状态 | **Vue Router**、**Pinia** | 页面路由与全局状态 |
| UI 组件 | **Element Plus** | 表单、表格、布局 |
| 可视化 | **ECharts** | 教师端学情图表、知识薄弱图 |
| HTTP | **Axios** | 调用 FastAPI；SSE 用 `fetch` / `@microsoft/fetch-event-source` |

### 4.4 数据与中间件

| 存储 | 技术 | 主要数据 |
|-----|------|---------|
| 关系库 | **MySQL 8** | 用户、课程、资源元数据、提交记录、作业、AI 调用日志、审核记录等 |
| 缓存/队列 | **Redis** | JWT 刷新、限流、对话上下文、Celery Broker、热点缓存 |
| 向量库（MVP） | **ChromaDB**（持久化）或 **FAISS**（文件） | 课程 embedding、RAG 检索 |
| 向量库（扩展） | **Milvus** / **pgvector** | 大规模或多课程隔离场景 |
| 对象存储（可选） | 本地 `uploads/` 或 **MinIO** | 原始 PDF/PPT 文件 |

### 4.5 建议工程目录结构

```
Intelligent_programming/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── core/                # 配置、安全、依赖
│   │   ├── api/v1/              # 路由（auth/courses/chat/code/...）
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── schemas/             # Pydantic 模型
│   │   ├── services/            # 业务 + AI + RAG
│   │   └── tasks/               # Celery 任务
│   ├── alembic/                 # 数据库迁移
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml           # 可选：Poetry/uv 管理依赖
├── frontend/                    # Vue3 工程
├── scripts/                     # 备份、初始化数据
├── docker-compose.yml           # MySQL + Redis +（可选）Chroma
└── docs/                        # API 说明、部署文档
```

### 4.6 部署与环境

- Python **3.10+**（推荐 3.11）  
- 学校机房 / 云主机（阿里云、腾讯云等）  
- **Docker Compose** 一键拉起 MySQL、Redis、后端、前端静态资源  
- 生产：`gunicorn -k uvicorn.workers.UvicornWorker` + Nginx 反向代理  
- 成本与运维以「可演示、可内测」为优先  

### 4.7 团队分工（Python 版）

| 角色 | 技术侧重 |
|-----|---------|
| Python 后端 | FastAPI 业务、SQLAlchemy、JWT、Celery 任务 |
| AI/RAG | LangChain Pipeline、Prompt、Embedding、向量库 |
| 前端 | Vue3 + Element Plus + ECharts |
| 运维/测试 | Docker、pytest、部署与演示数据准备 |

---

## 五、实施阶段与 MVP 优先级

### 5.1 阶段划分（对应 PDF，技术活动已 Python 化）

1. **调研与规划**：竞品分析、功能清单与 MVP、确定 FastAPI + LangChain 技术路线。  
2. **准备与原型**：FastAPI 骨架、MySQL/Redis、JWT 权限、Vue 脚手架、资料上传原型、LLM API 联调与 Prompt/敏感词策略。  
3. **全面实施**：RAG 问答、代码讲解、学习记录、教师可视化、内测与调优。  
4. **优化与交付**：性能、AI 质量、Docker 部署、论文与答辩材料。

### 5.2 建议 MVP 功能（文档明确优先级）

| 优先级 | 模块 |
|-------|------|
| P0 | 用户认证与角色、课程资源上传与列表 |
| P0 | AI 问答（含基础 RAG：ChromaDB + 课程切片） |
| P0 | 智能代码讲解（至少 Python 一种语言打通） |
| P1 | 学习记录、错题本 |
| P1 | 教师班级统计（基础 ECharts） |
| P2 | AI 回答审核、Milvus/pgvector 升级、高级推荐规则 |
| P2 | Prometheus 监控、本地 7B 模型接口预留（Ollama） |

---

## 六、创新点与技术亮点（文档第八～九页）

1. **教学场景 AI 深度融合**：课程知识库 + RAG，减少「跑题」。  
2. **多语言代码分级讲解**：Pydantic 约束结构化输出，贴近调试习惯。  
3. **学习轨迹驱动的个性化**：Python 规则引擎 + SQL 聚合，控制成本。  
4. **工程化可扩展架构**：FastAPI 模块化 + 向量库/模型可插拔（LangChain VectorStore 抽象）。  
5. **教师审核与人机协同**：关键答复可追溯、可订正。  
6. **Python 一体化栈（相对原方案新增亮点）**：解析、Embedding、推理、任务队列同一语言，降低毕设开发与答辩演示复杂度。

---

## 七、Python 依赖清单（建议 `requirements.txt` 核心项）

```text
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
alembic>=1.13.0
pymysql>=1.1.0
redis>=5.0.0
celery>=5.3.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
pydantic-settings>=2.2.0
httpx>=0.27.0
langchain>=0.2.0
langchain-openai>=0.1.0
chromadb>=0.4.0
pdfplumber>=0.11.0
python-pptx>=0.6.23
python-docx>=1.1.0
structlog>=24.1.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

> 版本号可在立项时按 PyPI 最新稳定版微调；`langchain` 生态迭代较快，建议在 `docs/dependencies.md` 锁定测试通过的组合。

---

## 八、预期交付物（文档第九页）

1. 可运行的「慧编学伴」系统一套（**Python 后端 + Vue3 前端**）  
2. 设计与实现类技术文档（含 API 文档、数据库设计、部署说明）  
3. 开题/答辩报告  
4. 各功能模块 **pytest** 测试说明与用例（符合 `01_skill.md` / `02_skill.md` 测试与闭环要求）

---

## 九、小结

「慧编学伴」在 Python 技术路线下形成 **Vue3 前端 + FastAPI 业务层 + LangChain/RAG 模型层 + MySQL/Redis + ChromaDB/FAISS（向量扩展）** 的清晰分层；在业务上仍围绕 **讲解、对话、知识库、学情、教师端、系统管理** 六模块展开，并以 **课程私有化 RAG** 与 **教师审核** 作为与通用 ChatBot 的核心差异。

相对原 Java 方案，**功能需求不变、实现语言与中间件适配 Python 生态**；后续查缺补漏与编码实现请以 **`05_Python_项目查缺补漏与实现审计报告.md`**、**`20260609_工作流审计文档.md`** 为对照清单，并严格遵循 `root_data/SKILL/01_skill.md` 与 **`02_skill.md`**（Phase 3 起）中的开发规范。

---

*本报告基于项目设计 PDF 与 02 号 Java 版报告整理，完成 Java → Python 技术栈映射，不涉及具体源码实现。*
