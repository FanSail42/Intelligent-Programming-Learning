# 测试说明

> **项目**：慧编学伴——智能编程学习助教系统  
> **框架**：pytest + pytest-asyncio + httpx.AsyncClient  
> **版本**：Phase 0 骨架

---

## 1. 目录约定

```
backend/
├── tests/
│   ├── conftest.py          # 公共 fixture（AsyncClient 等）
│   ├── test_health.py       # Phase 0 健康检查
│   ├── test_auth.py         # Phase 1 认证
│   ├── test_courses.py      # Phase 1 课程
│   └── ...                  # 各 Phase 按模块追加
└── pytest.ini
```

---

## 2. 运行方式

```bash
cd backend

# 安装依赖（首次）
pip install -r requirements.txt

# 运行全部测试
pytest

# 详细输出
pytest -v

# 指定模块
pytest tests/test_health.py -v
```

---

## 3. 测试分层

| 层级 | 说明 | 示例 |
|------|------|------|
| 单元测试 | 纯函数、Schema 校验 | `test_mastery.py` 公式 |
| API 集成测试 | httpx 调 FastAPI 路由 | `test_auth.py` 登录流程 |
| Mock 策略 | 外部 LLM/Embedding 必须 Mock | `unittest.mock.patch` |

---

## 4. Mock 策略

### 4.1 必须 Mock 的外部依赖

| 依赖 | Mock 方式 | 阶段 |
|------|----------|------|
| LLM API | patch `services/llm_service.py` | Phase 2+ |
| Embedding API | patch `services/embedding.py` | Phase 2+ |
| Redis | fakeredis 或 patch | Phase 1+ |
| Celery 任务 | `task.apply()` 同步执行或 patch delay | Phase 2+ |

### 4.2 测试数据库

- Phase 1 起：使用独立测试库 `huibian_test` 或 SQLite 内存库（迁移脚本需兼容）
- 每个测试用例事务回滚或 truncate 表

---

## 5. Fixture 约定

`conftest.py` 提供：

| Fixture | 说明 |
|---------|------|
| `client` | httpx AsyncClient，挂载 FastAPI app |
| `db_session` | Phase 1 起：SQLAlchemy Session |
| `auth_headers` | Phase 1 起：各角色 Token Header |

---

## 6. 测试门禁（skill S5）

每个 Phase 完成前，对应测试文件 **全部通过** 方可进入下一阶段。

| Phase | 测试文件 | 状态 |
|-------|---------|------|
| 0 | `test_health.py` | ✅ Phase 0 |
| 1 | `test_auth.py`、`test_courses.py`、`test_deps.py` | 待 Phase 1 |
| 2 | `test_material_pipeline.py`、`test_chat_rag.py` 等 | 待 Phase 2 |
| 3 | `test_code_analysis.py`、`test_mastery.py` 等 | 待 Phase 3 |
| 4 | `test_teacher_stats.py`、`test_health.py`（全组件） | 待 Phase 4 |

---

## 7. 自测记录

### Phase 0（2026-06-08）

| 用例 | 结果 | 备注 |
|------|------|------|
| `test_health_returns_200` | ✅ 通过 | GET /health 返回 code=0（2026-06-08） |

> 每完成一个 Phase，在本节追加测试执行记录（日期、命令、通过数/失败数）。

---

## 8. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-06-08 | Phase 0 骨架创建 |
