# 12 Week Year - Collaboration Guide

## 开发模式：TDD + Code Review + Small Batch

### 迭代路线图

| 版本 | 功能 | 提交粒度 |
|------|------|----------|
| v0.1 | 项目初始化 + Hello API | 1-2 个 |
| v0.2 | SQLite 数据库 + CRUD | 3-4 个 |
| v0.3 | 任务管理 API | 2-3 个 |
| v0.4 | 执行分数计算 | 2 个 |
| v0.5 | 基础前端 | 3-4 个 |

### 每个提交的检验标准

- ✅ 单元测试通过
- ✅ 集成测试通过 (API 测试)
- ✅ 代码能跑通
- ✅ 另一个 agent review 过

### 协作流程

1. **人类** → 提需求/拆分任务
2. **AI Agent** → 写代码 + 测试
3. **另一个 Agent** → Code Review
4. **人类** → 确认合并

---

## v0.1 目标：搭建项目骨架，有一个可运行的 Hello API

### 目录结构

```
12-week-year/
├── backend/
│   ├── main.py          # FastAPI 入口
│   ├── tests/           # 测试
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── docker-compose.yml
└── README.md
```
