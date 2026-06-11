# 慧编学伴——智能编程学习助教系统

面向高校计算机类课程的智能编程学习助教系统。后端 FastAPI + MySQL + Redis + Chroma，前端 Vue3 + Element Plus。

**当前进度**：Phase 0～3（学生端）已闭环；Phase 4 **M07 教师学情**、**M09 账户/AI 管理**、**个人中心**、**前端 UI 美化** 已交付；**M08 部署** 待开工。

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
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **端口冲突**：若 8000 被旧 uvicorn 占用且 `/admin/overview` 返回 404，请先结束占用进程后重启；或临时改用 `--port 8001` 并同步修改 `frontend/.env.development` 中的 `VITE_API_BASE`。

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
python scripts/seed_dashboard_demo.py   # 三类课程 + 仪表盘/教师学情联调数据
```

登录 **access token 默认有效期 3 天**（见 `backend/.env.example`）。

## 演示账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | Admin123! |
| 教师 | teacher | Teacher123! |
| 学生 | student | Student123! |

`seed_demo.py` 另含 `adm` / `tea` / `stu` 等账号（密码 `123123`）。  
`seed_dashboard_demo.py` 写入 **C++ 数据结构**、**Python 数据分析**、**Java 面向对象** 三门演示课（含近 7 日错题与事件）。

## 端口约定

| 服务 | 端口 |
|------|------|
| FastAPI | 8000（开发默认） |
| Vue 前端 | 5173 |
| MySQL | 3306 |
| Redis | 6379 |

详见 [docs/deploy.md](docs/deploy.md)。

## 运行测试

```bash
cd backend
pytest -q          # 当前 154 passed
cd ../frontend
npm run build
```

## 文档索引

| 类型 | 路径 |
|------|------|
| 模块说明 | `docs/modules/M01～M07、M09_*.md` |
| 完成度 / 路线 | `out_data/20260611_功能模块开发完成度报告.md`、`out_data/20260611_项目功能模块汇总.md` |
| Bug / 联调 | `out_data/20260611_残留Bug汇总与解决.md`、`out_data/20260611_后续开发路线与Bug堵塞解决.md` |
| 文档索引 | `out_data/20260611_项目说明文档汇总.md` |
| API 规范 | `docs/api-convention.md` |
| 部署说明 | `docs/deploy.md` |
| 测试说明 | `docs/testing.md` |
| 开发路线 | `out_data/06_项目搭建优先级路线（详细路线）.md` |

## 答辩演示流程（Checklist）

### 学生端

1. `student` 登录 → **我的课程** → 选一门 dashboard 演示课（如 Python 数据分析）
2. **AI 辅导**：提问并查看 SSE 流式回答、引用来源、课程语言代码示例
3. **代码讲解** → 提交代码 → 查看分析结果
4. **学习仪表盘**：7 日趋势（末位为「今日」）、薄弱 KP、近期活动
5. **错题本**：筛选、图表、标记掌握

### 教师端

1. `teacher` 登录 → **班级学情**（`/teacher/dashboard`）
2. 选择课程 → 查看选课人数（可点开班级名单）、班级错题 TOP、薄弱 KP、事件趋势

### 管理员

1. `admin` 登录 → 默认进入 **管理概览**（`/admin/overview`）
2. **AI 模型管理**（`/admin/ai-models`）：切换百炼模型、自定义模型、API Key、日限额
3. **AI 用量监控**（`/admin/ai-usage`）：7 日趋势、学生 Token 用量
4. **学生账号** / **教师账号** 分模块 CRUD
5. **操作日志** 查看登录与配置变更记录

### 个人中心（三类用户）

1. 顶栏用户名下拉或侧栏 **账户 → 个人中心**（`/profile`）
2. 修改用户名 / 修改密码；学生可查看 AI 用量概览

### 教师资料（Phase 1+2）

1. `teacher` → 课程资料页上传 PDF/TXT/MD
2. 等待资料状态 `READY` 后，学生端 AI 辅导可引用
