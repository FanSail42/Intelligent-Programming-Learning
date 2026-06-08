# 部署与本地开发说明

> **项目**：慧编学伴——智能编程学习助教系统  
> **版本**：Phase 0 骨架（Phase 4 定稿）

---

## 1. 环境要求

| 组件 | 版本 |
|------|------|
| Python | 3.10+（推荐 3.11） |
| Node.js | 18+ |
| Docker | 20+ |
| Docker Compose | v2+ |

---

## 2. 端口一览

| 服务 | 端口 | 说明 |
|------|------|------|
| FastAPI | 8000 | 后端 API + Swagger `/docs` |
| Vue 前端 | 5173 | Vite 开发服务器 |
| MySQL | 3306 | 业务数据库 |
| Redis | 6379 | 缓存 / Celery Broker |

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

| 项 | 值 |
|----|-----|
| Host | localhost:3306 |
| Database | huibian |
| User | huibian |
| Password | huibian123 |
| Root Password | root123456 |

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

# 启动开发服务器
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

## 6. 完整启动顺序（Phase 0）

1. `docker compose up -d` — 启动 MySQL、Redis  
2. 后端：`uvicorn app.main:app --reload`  
3. 前端：`npm run dev`  
4. 浏览器打开 http://localhost:5173  

---

## 7. 测试

```bash
cd backend
pytest -v
```

---

## 8. 演示账号（Phase 1 seed 后启用）

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | Admin123! |
| 教师 | teacher | Teacher123! |
| 学生 | student | Student123! |

> Phase 1 完成后由 `scripts/seed_demo.py` 写入。

---

## 9. 生产部署（Phase 4 完善）

- Docker Compose 增加 `backend`、`celery-worker`、`frontend`（build）服务  
- Nginx 反向代理 + 静态资源  
- Gunicorn：`gunicorn -k uvicorn.workers.UvicornWorker app.main:app`

---

## 10. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-06-08 | Phase 0 本地启动骨架 |
