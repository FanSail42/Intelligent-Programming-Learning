# Phase 3 起开发要求与规范说明（续）

> **适用阶段**：Phase 1～2 核心链路已打通之后（2026-06-09 工作流审计基线）  
> **前置规范**：`root_data/SKILL/01_skill.md`（S1～S10 仍然有效，本文为补充与纠偏）  
> **依据文档**：`out_data/20260609_工作流审计文档.md`、`out_data/06_项目搭建优先级路线（详细路线）.md`

---

## 一、当前进度基线

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 0 | ~90% | 工程与规范基本就绪 |
| Phase 1 | ~85% | M01/M02 核心完成；课程审核流已超前落地 |
| Phase 2 | ~75% | M03/M04 主链路已通；Celery/联调/文档待打磨 |
| Phase 3 | 0% | **P0 智能代码讲解未开始——答辩最大缺口** |
| Phase 4 | ~15% | 仅课程审核部分提前实现 |

**已打通主链路**：登录 → 课程/选课（含审核）→ 教师上传 PDF → 学生 RAG 对话（SSE + 引用）。

---

## 二、开发要求（Phase 3 起）

### 1. 未完成 P0 不启动 P1（继承 S4，严格执行）

- Phase 3 的 **M05 智能代码讲解** 为答辩 P0，必须优先于 M06 学情分析。
- 禁止再超前实现 Phase 4 功能（如完整管理员后台），除非 M05 验收已通过。

### 2. 新模块开工前必须编写模块说明文档

| 模块 | 文档路径 | 开工条件 |
|------|---------|---------|
| M05 | `docs/modules/M05_智能代码讲解.md` | Phase 3 编码前 **必写** |
| M06 | `docs/modules/M06_学习分析与推荐.md` | M05 验收后 |
| M07 | `docs/modules/M07_教师教学支持.md` | Phase 4 开工前 |
| M08 | `docs/modules/M08_系统运维与部署.md` | Phase 4 开工前 |

### 3. 模块完成时必须闭环三件事

1. **pytest 全绿**：对应 `backend/tests/test_*.py` 全部通过（LLM/Embedding 必须 Mock）。
2. **验收勾选**：模块文档 §验收标准 全部 `[x]`，并填写完成日期。
3. **自测记录**：在 `docs/testing.md` §7 追加 Phase/模块自测行，删除重复或过时的「待完成」行。

### 4. Phase 3 P0 最低交付（M05）

- 表：`code_submission`、`analysis_result`（逻辑外键，见 `docs/database.md`）
- API：`POST /api/v1/code/submit`、`GET /api/v1/code/submit/{id}/result`
- 前端：`/student/code` + Monaco 编辑器
- 测试：`test_code_analysis.py`（Mock LLM 返回结构化 JSON）
- 答辩演示：提交含错 Python 代码 → 展示分级讲解结果

### 5. 已有模块打磨（Phase 3 并行，不阻塞 M05 主开发）

| 模块 | 必做项 | 优先级 |
|------|--------|--------|
| M03 | 资料 FAILED 重试、软删除 API；Celery 启动说明写入 `deploy.md` | 高 |
| M04 | 统一前后端 API 端口；完善 citation / no_context 判定 | 高 |
| M02 | seed 含「已审核 + 已发布」演示课；迁移以 Alembic 为主 | 中 |
| M01 | 至少补管理员读/写 LLM Key 配置 API（答辩步骤 1） | 中 |
| Phase 0 | README 替换模板；`/health` 探活 MySQL/Redis/Chroma | 中 |

### 6. 演示数据与 seed 脚本

- 新增或更新 `scripts/seed_*.py`，保证 **15 分钟答辩脚本** 无需手工多步审核即可演示。
- 演示账号、已发布课程、READY 资料须在 `README.md` 与 `deploy.md` 中写明。

### 7. 数据库迁移规范（纠偏）

- **新表/新字段**：仅通过 Alembic 版本脚本变更；禁止新增 `db_migrate.py` 式运行时补列。
- 已有 `ensure_course_schema()` 保留兼容，但 Phase 3 起不得再扩展该模式。
- 每次迁移同步更新 `docs/database.md` 表结构与逻辑外键说明。

### 8. 环境与端口一致性

- 以 `backend/.env.example` + `docs/deploy.md` 为 **唯一权威** 端口说明。
- 修改默认端口时须同步：`frontend/.env.development`、`docs/deploy.md`、`README.md`。
- 当前开发约定：**后端 `8000`（或文档明确单一端口），禁止文档内 8000/8002/8004 并存。**

---

## 三、规范说明（文档与审计）

### 1. 文档存放约定（澄清 S3）

| 类型 | 路径 | 说明 |
|------|------|------|
| 模块说明（开发前） | `docs/modules/M0X_*.md` | 业务/API/表/验收；**主存放位置** |
| 全局规范 | `docs/*.md` | api-convention、database、testing、deploy |
| 分析与路线报告 | `out_data/*.md` | 04/05/06、工作流审计、查缺补漏 |
| Skill 规范 | `root_data/SKILL/` | 01 基础规范 + 02 阶段续规范 |

`out_data` 存放 **分析报告与审计结论**，不替代 `docs/modules` 模块说明文档。

### 2. 模块收尾检查清单（S10 落地）

每个模块标记完成前，逐项确认：

- [ ] 模块说明文档验收标准已全部勾选
- [ ] `docs/testing.md` 测试门禁表已更新状态
- [ ] `docs/database.md` 已含本模块表 DDL 与逻辑外键
- [ ] `docs/api-convention.md` 已含本模块新增接口（若有）
- [ ] seed/演示脚本可复现主流程
- [ ] 无未 Mock 的真实 LLM 调用进入 CI/pytest

### 3. 工作流审计节奏

- 每完成一个 Phase 或重大偏离时，更新 `out_data/` 下工作流审计文档（或追加 dated 版本）。
- 审计结论中的「立即 / Phase N 开工前 / 答辩前」项须回写到 06 路线或本 skill。

### 4. 测试与 Mock（强化 S5）

- Phase 3+ 外部依赖：**LLM、Embedding、Judge0（若接入）** 在测试中必须 Mock。
- `docs/testing.md` 不得出现同一 Phase 重复两行且状态矛盾；以 **最新一次 pytest 结果** 为准。

---

## 四、建议开发顺序（2026-06-09 起）

```
① 编写 docs/modules/M05_智能代码讲解.md
      ↓
② 实现 M05（Mock 测试先行）→ 验收 + testing.md 记录
      ↓
③ 并行打磨 M03 重试 / deploy 端口统一 / seed 演示数据
      ↓
④ 编写 M06 文档 → 实现学情/错题本/仪表盘（P1）
      ↓
⑤ Phase 4：M07、M08 + Docker 全栈 + 15 分钟演示脚本定稿
```

**答辩最低闭环仍缺**：步骤 4「智能代码讲解」——须作为本周 P0。

---

## 五、与 01_skill 的关系

| 文档 | 作用 |
|------|------|
| `01_skill.md` | 全项目通用：Python 主栈、逻辑外键、模块测试、接口一致性 |
| `02_skill.md`（本文） | Phase 3 起：进度基线、文档索引澄清、迁移/端口纠偏、模块闭环与打磨清单 |

两者冲突时：**安全与测试要求以 01 为准**；**阶段优先级与文档闭环以 02 + 06 路线为准**。

---

## 六、变更记录

| 日期 | 说明 |
|------|------|
| 2026-06-09 | 初版：基于工作流审计文档，定义 Phase 3 起开发规范与文档闭环要求 |
