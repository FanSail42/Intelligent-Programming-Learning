# 部署与本地开发说明

> **项目**：慧编学伴——智能编程学习助教系统
> **版本**：Phase 4 开发中（M07/M09 已交付；M08 生产部署待完善）

---

## 1. 环境要求

| 组件           | 版本               |
| -------------- | ------------------ |
| Python         | 3.10+（推荐 3.11） |
| Node.js        | 18+                |
| Docker         | 20+                |
| Docker Compose | v2+                |

---

## 2. 端口一览

| 服务     | 端口 | 说明                         |
| -------- | ---- | ---------------------------- |
| FastAPI  | 8000 | 后端 API + Swagger `/docs`（开发环境） |
| Vue 前端 | 5173 | Vite 开发服务器              |
| MySQL    | 3306 | 业务数据库（docker-compose 映射） |
| Redis    | 6379 | 缓存 / Celery Broker         |

---

## 3. 一键启动中间件（Docker）

在项目根目录执行：

```bash
docker compose up -d
```

验证：

```bash
# MySQL
docker exec huibian-mysql mysqladmin ping -h localhost -u root -proot123456

# Redis
docker exec huibian-redis redis-cli ping
```

停止：

```bash
docker compose down
```

### 3.1 默认数据库账号

| 项            | 值             |
| ------------- | -------------- |
| Host          | localhost:3306 |
| Database      | huibian        |
| User          | huibian        |
| Password      | huibian123     |
| Root Password | root123456     |

---

## 4. 后端本地启动

```bash
cd backend

# 创建虚拟环境（首次）
python -m venv .venv

# Windows 激活
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量
copy .env.example .env

# 数据库迁移（首次或 schema 变更后）
alembic upgrade head

# 启动开发服务器（首次启动会补齐仓库等运行时 schema）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：

- 健康检查：http://localhost:8000/health
- API 文档：http://localhost:8000/docs

---

## 5. 前端本地启动

```bash
cd frontend

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev
```

访问：http://localhost:5173

环境变量（`.env.development`）：

```
VITE_API_BASE=http://localhost:8000
```

---

## 6. 完整启动顺序（推荐）

1. `docker compose up -d` — 启动 MySQL、Redis
2. `cd backend` → `alembic upgrade head` — 数据库迁移
3. `uvicorn app.main:app --reload` — 启动后端（补齐仓库 schema）
4. `python scripts/seed_demo.py` + `python scripts/seed_warehouses.py` — 基础账号与仓库
5. `python scripts/seed_dashboard_demo.py` — **仪表盘/教师学情联调**（C++/Python/Java 三门课 + 近 7 日错题）
6. `cd frontend` → `npm run dev`
7. 浏览器打开 http://localhost:5173

### 6.2 仪表盘演示数据说明

| 脚本 | 作用 |
|------|------|
| `seed_demo.py` | admin/teacher/student + 单门 Python Demo 课 |
| `seed_dashboard_demo.py` | 3 门代表课、18+ 份 PDF 资料、55+ 错题、90 学习事件 |
| `seed_warehouses.py` | 格式仓/课程仓初始数据 |

演示课 keys：`cpp`（C++ 数据结构）、`python`（Python 数据分析）、`java`（Java 面向对象）。可重复执行，脚本幂等。

### 6.3 开发端口冲突（Windows 常见）

若前端访问 `/admin/overview` 或 `/admin/logs` 返回 **404**，而 pytest 已通过，通常是 **8000 上仍有旧 uvicorn 进程**（OpenAPI 不含新路由）。

1. 查占用：`netstat -ano | findstr :8000`
2. 结束对应 PID 后，在 `backend` 目录仅启动 **一个** 实例：`uvicorn app.main:app --reload --port 8000`
3. 验证：http://localhost:8000/openapi.json 应含 `/api/v1/admin/overview`
4. 临时方案：在新端口启动最新后端，例如：
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
   ```
   并设置 `frontend/.env.development`：
   ```
   VITE_API_BASE=http://127.0.0.1:8002
   ```
5. **修改 `.env.development` 后必须重启** `npm run dev`（Vite 不会热加载 env）
6. 快速自检：浏览器打开 `{VITE_API_BASE}/openapi.json`，搜索 `admin/overview` 与 `admin/ai/models` 均应存在

### 6.1 JWT 有效期

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 4320（3 天） | 登录 access token |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 7 | refresh token |

修改后需重启后端；本地 `.env` 覆盖 `.env.example` 默认值。

---

## 7. Celery Worker（可选，推荐生产/大文件）

资料解析默认先尝试 Celery 异步任务；若 worker 未启动，自动降级为 FastAPI `BackgroundTasks`（小文件可用，大 PDF 可能阻塞请求线程）。

```bash
cd backend

# Windows（开发）
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo

# Linux/macOS
celery -A app.tasks.celery_app worker --loglevel=info
```

Broker 默认使用 `REDIS_URL`（见 `backend/.env.example`）。

---

## 8. 测试

```bash
cd backend
pytest -v
```

---

## 9. 演示账号（Phase 1 seed 后启用）

| 角色   | 用户名  | 密码        |
| ------ | ------- | ----------- |
| 管理员 | admin   | Admin123!   |
| 教师   | teacher | Teacher123! |
| 学生   | student | Student123! |
| 管理员 | adm     | 123123      |
| 教师   | tea     | 123123      |
| 教师   | tea1    | 123123      |
| 教师   | tea2    | 123123      |
| 教师   | tea3    | 123123      |
| 学生   | stu     | 123123      |

> Phase 1 完成后由 `scripts/seed_demo.py` 写入。

---

## 10. 生产部署（M08，待完善）

当前 `docker-compose.yml` 仅含 MySQL + Redis。Phase 4 M08 目标：

| 任务 | 说明 |
|------|------|
| `docker-compose.prod.yml` | 增加 `backend`、`celery-worker`、`frontend`（build）服务 |
| Nginx | 反向代理 + 静态资源 |
| Gunicorn | `gunicorn -k uvicorn.workers.UvicornWorker app.main:app` |
| 配置 | `sys_config` / LLM Key 管理或 `.env` 文档化 |
| 备份 | `scripts/backup_db.py`（可选） |

答辩最低标准：本地 `docker compose up -d` + 手动启后端/前端即可；生产一键部署为 M08 交付物。

---

## 11. 变更记录

| 日期       | 说明                 |
| ---------- | -------------------- |
| 2026-06-08 | Phase 0 本地启动骨架 |
| 2026-06-09 | 统一端口 8000/3306；补充 Celery worker 说明 |
| 2026-06-11 | 补充 dashboard 演示种子、8000 端口冲突排查、M08 待办 |
| 2026-06-11 | 全量联调 154 passed；个人中心；文档四件套 |
