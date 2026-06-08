# 依赖锁定说明

> **项目**：慧编学伴——智能编程学习助教系统  
> **更新日期**：2026-06-08（Phase 0）

---

## 1. Python 后端

来源：`backend/requirements.txt`

| 包 | 最低版本 | 用途 | 启用阶段 |
|----|---------|------|---------|
| fastapi | 0.110.0 | Web 框架 | Phase 0 |
| uvicorn[standard] | 0.27.0 | ASGI 服务器 | Phase 0 |
| sqlalchemy | 2.0.0 | ORM | Phase 1 |
| alembic | 1.13.0 | 数据库迁移 | Phase 1 |
| pymysql | 1.1.0 | MySQL 驱动 | Phase 1 |
| redis | 5.0.0 | Redis 客户端 | Phase 1 |
| celery | 5.3.0 | 异步任务 | Phase 2 |
| python-jose[cryptography] | 3.3.0 | JWT | Phase 1 |
| passlib[bcrypt] | 1.7.4 | 密码哈希 | Phase 1 |
| pydantic-settings | 2.2.0 | 配置管理 | Phase 0 |
| httpx | 0.27.0 | HTTP 客户端 / 测试 | Phase 0 |
| langchain | 0.2.0 | LLM/RAG 编排 | Phase 2 |
| langchain-openai | 0.1.0 | OpenAI 兼容接口 | Phase 2 |
| chromadb | 0.4.0 | 向量库 | Phase 2 |
| pdfplumber | 0.11.0 | PDF 解析 | Phase 2 |
| python-pptx | 0.6.23 | PPT 解析 | Phase 5（P2） |
| python-docx | 1.1.0 | Word 解析 | Phase 5（P2） |
| structlog | 24.1.0 | 结构化日志 | Phase 1+ |
| pytest | 8.0.0 | 测试框架 | Phase 0 |
| pytest-asyncio | 0.23.0 | 异步测试 | Phase 0 |

---

## 2. 前端

| 包 | 用途 |
|----|------|
| vue | 3.x SPA 框架 |
| vue-router | 路由 |
| pinia | 状态管理 |
| element-plus | UI 组件库 |
| axios | HTTP 请求 |
| echarts | 图表（Phase 4 教师端） |
| typescript | 类型支持 |

---

## 3. 基础设施

| 组件 | 镜像/版本 |
|------|----------|
| MySQL | mysql:8.0 |
| Redis | redis:7-alpine |

---

## 4. 版本锁定建议

Phase 0 使用 `>=` 最低版本约束；在首次全量测试通过后，建议执行：

```bash
pip freeze > backend/requirements-lock.txt
```

并在 CI / 答辩环境使用 lock 文件安装。

---

## 5. 已知兼容性注意

- `langchain` 生态迭代较快，Phase 2 开工前需验证与 `chromadb` 的组合  
- `chromadb` 在 Windows 上可能需要 Visual C++ 构建工具  
- `passlib[bcrypt]` 与 `bcrypt` 4.x 存在已知兼容问题，若报错可 pin `bcrypt<4.1`

---

## 6. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-06-08 | Phase 0 初版，对齐 04 §七 依赖清单 |
