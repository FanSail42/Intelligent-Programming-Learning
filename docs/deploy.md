# 部署与本地开发说明

> **项目**：慧编学伴——智能编程学习助教系统
> **版本**：Phase 0 骨架（Phase 4 定稿）

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
4. `python scripts/seed_demo.py` + `python scripts/seed_warehouses.py` — 演示数据
5. `cd frontend` → `npm run dev`
6. 浏览器打开 http://localhost:5173

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

## 10. 生产部署（Phase 4 完善）

- Docker Compose 增加 `backend`、`celery-worker`、`frontend`（build）服务
- Nginx 反向代理 + 静态资源
- Gunicorn：`gunicorn -k uvicorn.workers.UvicornWorker app.main:app`

---

## 11. 变更记录

| 日期       | 说明                 |
| ---------- | -------------------- |
| 2026-06-08 | Phase 0 本地启动骨架 |
| 2026-06-09 | 统一端口 8000/3306；补充 Celery worker 说明 |
