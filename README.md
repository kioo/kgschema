# Knowledge Graph Schema Management System

基于 FastAPI + PostgreSQL + SQLAlchemy 的知识图谱 Schema 管理系统。

## 快速开始

```bash
# 启动开发环境
docker-compose up -d

# 访问 API 文档
open http://localhost:8000/docs
```

## 技术栈

- **后端**: FastAPI + SQLAlchemy 2.0 (async) + Alembic
- **数据库**: PostgreSQL 15+
- **认证**: JWT (python-jose)

## 目录结构

```
app/
├── main.py          # FastAPI 入口
├── api/             # 路由模块
├── core/            # 配置、安全、依赖
├── models/          # SQLAlchemy 模型
├── schemas/         # Pydantic 模型
├── services/        # 业务逻辑
└── db/              # 数据库会话与迁移
```
