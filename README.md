# 慧编学伴——智能编程学习助教系统

面向高校计算机类课程的智能编程学习助教系统。后端 FastAPI + MySQL + Redis + Chroma，前端 Vue3 + Element Plus。当前已完成 **Phase 0～2**：登录鉴权、课程选课、知识库 RAG、AI 对话辅导（SSE 流式 + 引用）。

## 快速启动

### 1. 启动中间件

```bash
docker compose up -d
```

### 2. 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173

### 4. 数据库迁移与演示数据

```bash
cd backend
alembic upgrade head
cd ..
python scripts/seed_demo.py
python scripts/seed_warehouses.py
```

登录 **access token 默认有效期 3 天**（见 `backend/.env.example`）。

## 演示账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | Admin123! |
| 教师 | teacher | Teacher123! |
| 学生 | student | Student123! |

`seed_demo.py` 会创建已审核、已发布的演示课程 **Python Programming Demo**，学生可直接选课体验 RAG 对话。

## 端口约定

| 服务 | 端口 |
|------|------|
| FastAPI | 8000 |
| Vue 前端 | 5173 |
| MySQL | 3306 |
| Redis | 6379 |

详见 [docs/deploy.md](docs/deploy.md)。

## 运行测试

```bash
cd backend
pytest -v
```

## 文档索引

| 类型 | 路径 |
|------|------|
| 模块说明 | `docs/modules/M01～M04_*.md` |
| API 规范 | `docs/api-convention.md` |
| 部署说明 | `docs/deploy.md` |
| 测试说明 | `docs/testing.md` |
| 开发路线 | `out_data/06_项目搭建优先级路线（详细路线）.md` |
| 工作流审计 | `out_data/20260609_工作流审计文档.md` |

## 演示流程（Phase 1+2）

1. 教师 `teacher` 登录 → 课程资料页上传 PDF/TXT/MD
2. 等待资料状态变为 `READY`
3. 学生 `student` 登录 → 我的课程 → AI 辅导提问
4. 查看 SSE 流式回答与引用来源
