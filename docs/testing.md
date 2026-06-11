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

## 6. 测试门禁（skill S5；Phase 3 闭环见 `root_data/SKILL/02_skill.md` §二.3）

每个 Phase 完成前，对应测试文件 **全部通过** 方可进入下一阶段。

| Phase | 测试文件 | 状态 |
|-------|---------|------|
| 0 | `test_health.py` | ✅ Phase 0（含组件探活, 2026-06-09） |
| 1 | `test_auth.py`、`test_courses.py`、`test_deps.py` | ✅ Phase 1（14 passed, 2026-06-08） |
| 2 | `test_material_pipeline.py`、`test_vector_store.py`、`test_chat_rag.py`、`test_chat_sse.py`、`test_warehouses.py` | ✅ Phase 2+仓库（含 PPTX 格式仓） |
| 3 | `test_code_analysis.py`、`test_code_helpers.py` | ✅ M05（66 passed, 2026-06-10） |
| 3 | `test_mastery.py`、`test_learning_api.py`、`test_wrong_book_analysis.py` | ✅ M06（含错题本统计与类别分析） |
| 4 | `test_teacher_stats.py`、`test_admin_users.py`、`test_admin_ai.py`、`test_health.py`（全组件） | ✅ M07/M09 MVP（2026-06-11） |

---

## 7. 自测记录

### Phase 0（2026-06-08）

| 用例 | 结果 | 备注 |
|------|------|------|
| `test_health_returns_200` | ✅ 通过 | GET /health 返回 code=0（2026-06-08） |

### Phase 1（2026-06-08）

| 用例 | 结果 | 备注 |
|------|------|------|
| `pytest -v` | ✅ 14 passed | 含 auth/courses/deps/health |

### Phase 2（2026-06-08）

| 用例 | 结果 | 备注 |
|------|------|------|
| `pytest -v` | ✅ 23 passed | 含 material_pipeline/vector_store/chat_rag/chat_sse |

### Phase 0-2 打磨回归（2026-06-09）

| 用例 | 结果 | 备注 |
|------|------|------|
| `pytest -v` | ✅ 37 passed | 新增 health 组件探活、资料删除/重试测试 |
| `test_health_returns_200` | ✅ 通过 | 返回 mysql/redis/chroma 组件状态 |
| `test_retry_failed_material` | ✅ 通过 | FAILED → UPLOADED 并重派任务 |
| `test_delete_material` | ✅ 通过 | 软删除 + 向量清理 |

### Phase 3 M05（2026-06-10）

| 用例 | 结果 | 备注 |
|------|------|------|
| `pytest -v` | ✅ 66 passed | 含 `test_code_analysis` 15 + `test_code_helpers` 4 |
| `test_submit_with_mock_llm` | ✅ 通过 | Mock LLM JSON 落库与 GET 结果 |
| `test_submit_without_enrollment` | ✅ 通过 | 无需选课即可提交 |
| `test_list_submissions_empty` | ✅ 通过 | 历史列表无 course_id |
| 四语言 + 语言校验 + 分栏 UI | ✅ 自测 | 见 `M05_智能代码讲解.md` §9 |

### Phase 3 M06（2026-06-10）

| 用例 | 结果 | 备注 |
|------|------|------|
| `pytest -v` | ✅ 75 passed | 含 `test_mastery` 4 + `test_learning_api` 5 |
| `test_code_submit_creates_wrong_book` | ✅ 通过 | M05 语义 error → 错题本 |
| `test_dashboard` | ✅ 通过 | 汇总统计 + 薄弱 KP |
| `test_wrong_book_list_and_mastered` | ✅ 通过 | 列表筛选 + 标记掌握 |
| `test_recommendations_requires_enrollment` | ✅ 通过 | 未选课 40301 |
| 前端仪表盘 / 错题本 | ✅ 自测 | `/student/dashboard`、`/student/wrong-book` |

### Phase 3 M06 错题本可视化（2026-06-10）

| 用例 | 结果 | 备注 |
|------|------|------|
| `test_learning_api.py` + `test_wrong_book_analysis.py` | ✅ 9 passed | 含 `test_wrong_book_stats` |
| `test_wrong_book_analysis.py` | ✅ 2 passed | 类别推断、对话详情 |
| `npm run build` | ✅ 通过 | `WrongBookCharts.vue` 编译无报错 |
| 前端错题本图表 | ✅ 修复 | `v-if="stats"` + `nextTick` + `ResizeObserver` |

### Phase 3 M06 学习仪表盘三类课程联调（2026-06-10）

| 用例 | 结果 | 备注 |
|------|------|------|
| `test_dashboard_integration.py` | ✅ 7 passed | C++/Python/Java 三类课程 |
| 来源构成 | ✅ | `code_submission` + `chat_message` 均有计数 |
| 类别分布 | ✅ | 含语法/语义/问答无上下文等多类别 |
| 演示数据 | ✅ 保留 | `scripts/seed_dashboard_demo.py` → 47 条错题 + 18 份资料 |
| 资料路径 | ✅ | `root_data/课程资料/` 分类目录 + `_联调演示/` |

### 全量回归（2026-06-11）

| 用例 | 结果 | 备注 |
|------|------|------|
| `pytest -q` | ✅ **154 passed** | 全后端测试 |
| `test_health_returns_200` | ✅ 修复 | 断言组件含 `pptx_parser` |
| `test_rag_relevance.py` | ✅ 4 passed | AI 引用相关性过滤 |
| `test_chat_suggestions.py` | ✅ 3 passed | 课程导向问题 |
| `test_wrong_book_trend.py` | ✅ 1 passed | 趋势含今日、近 7 日 |
| `npm run build` | ✅ 通过 | 前端生产构建 |

### M07 教师学情 MVP（2026-06-11）

| 用例 | 结果 | 备注 |
|------|------|------|
| `test_teacher_stats.py` | ✅ 6 passed | 教师/管理员可读、学生/他人教师 403、空班/聚合 |
| `GET /teacher/courses/{id}/overview` | ✅ | 班级错题、KP、事件趋势 |
| `TeacherDashboard.vue` | ✅ | `/teacher/dashboard` 班级学情页 |

### M09 账户管理 MVP（2026-06-11）

| 用例 | 结果 | 备注 |
|------|------|------|
| `test_admin_users.py` | ✅ 15 passed | 分模块 CRUD、概览、日志、角色校验 |
| `AccountManage.vue` | — | 已拆分为独立子页面 |
| `AdminOverview.vue` / `StudentAccountManage.vue` / `TeacherAccountManage.vue` / `OperationLogs.vue` | ✅ | 系统管理子模块 |

### 个人中心（2026-06-11）

| 用例 | 结果 | 备注 |
|------|------|------|
| `test_profile.py` | ✅ 5 passed | 概览、改用户名、改密、错误密码 |
| `PersonalCenter.vue` | ✅ | `/profile` 三类用户通用 |

---

### M09 AI 模型管理（2026-06-11）

| 用例 | 结果 | 备注 |
|------|------|------|
| `test_admin_ai.py` | ✅ 9 passed | 百炼模型目录、配置更新、用量统计、密钥加密 |
| `AiModelManage.vue` / `AiUsageStats.vue` | ✅ | `/admin/ai-models`、`/admin/ai-usage` |

---

## 8. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-06-08 | Phase 0 骨架创建 |
| 2026-06-09 | 删除重复 Phase 2 门禁行；补 Phase 2 自测记录；引用 `02_skill.md` |
| 2026-06-09 | Phase 0-2 问题修复后全量回归 37 passed |
| 2026-06-09 | 二次复检：含 `test_warehouses.py` 共 45 passed |
| 2026-06-10 | M05 验收：66 passed；M06 模块文档就绪待编码 |
| 2026-06-10 | M06 验收：75 passed（含 mastery + learning API） |
| 2026-06-10 | M06 错题本：stats API + ECharts；`test_wrong_book_analysis` 9 passed 联调 |
| 2026-06-11 | M07 MVP：`test_teacher_stats` + 教师班级学情 API/前端 |
| 2026-06-11 | 全量回归 119 passed；health 含 pptx_parser；M04/M06 联调增强 |
| 2026-06-11 | M09 子模块：`test_admin_users` 15 passed；全量 **140 passed** |
| 2026-06-11 | 个人中心：`test_profile` 5 passed；全量 **154 passed**；UI 美化 |

### Phase 0-2 二次复检（2026-06-09）

| 用例 | 结果 | 备注 |
|------|------|------|
| `pytest -v` | ✅ 45 passed | 含仓库 CRUD、分派、资料名称模糊搜索 |
| `test_warehouses.py` | ✅ 8 passed | 课程仓手动分派/移出 |
