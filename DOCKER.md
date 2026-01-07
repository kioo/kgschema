# Docker 部署指南

本文档说明如何使用 Docker 和 Docker Compose 部署知识图谱 Schema 管理系统。

## 前置要求

- Docker 20.10+
- Docker Compose 2.0+

## 环境变量配置

创建 `.env` 文件（参考 `.env.example`）：

```bash
# 数据库配置
DB_USER=kgschema
DB_PASSWORD=your-secure-password
DB_NAME=kgschema

# JWT 配置
JWT_SECRET=your-jwt-secret-key-change-in-production

# 调试模式（开发环境）
DEBUG=true
```

## 开发环境

### 启动所有服务

```bash
docker-compose up -d
```

服务将在以下端口运行：
- **前端**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **数据库**: localhost:5433

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### 停止服务

```bash
docker-compose down
```

### 重新构建

```bash
docker-compose up -d --build
```

## 生产环境

### 启动生产环境

```bash
docker-compose -f docker-compose.prod.yml up -d
```

生产环境将在以下端口运行：
- **应用**: http://localhost (包含前端和 nginx)
- **后端 API**: 通过容器内部网络访问
- **数据库**: 通过容器内部网络访问

### 停止生产环境

```bash
docker-compose -f docker-compose.prod.yml down
```

## 数据库迁移

### 运行迁移

```bash
# 在开发环境中
docker-compose exec backend alembic upgrade head

# 在生产环境中
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 创建新迁移

```bash
# 在开发环境中
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### 回滚迁移

```bash
docker-compose exec backend alembic downgrade -1
```

## 创建管理员用户

```bash
docker-compose exec backend python -m app.scripts.create_admin
```

## 常用命令

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入数据库容器
docker-compose exec db psql -U kgschema

# 进入前端容器
docker-compose exec frontend sh
```

### 查看容器状态

```bash
docker-compose ps
```

### 清理所有数据（警告：会删除数据库数据）

```bash
docker-compose down -v
```

## 故障排查

### 后端无法连接数据库

确保数据库服务已启动：
```bash
docker-compose ps db
```

检查数据库健康状态：
```bash
docker-compose logs db
```

### 前端无法访问后端 API

检查网络配置：
```bash
docker network inspect kgschema_kgschema-network
```

确保所有服务在同一网络中。

### 重新构建镜像

如果修改了代码或依赖：

```bash
docker-compose build --no-cache backend frontend
docker-compose up -d
```

## 镜像优化

生产环境使用多阶段构建：

1. **前端**:
   - 第一阶段：Node.js 构建 React 应用
   - 第二阶段：Nginx 提供静态文件服务

2. **后端**:
   - 使用 Python slim 镜像
   - 仅包含生产依赖
   - 非 root 用户运行

## 备份与恢复

### 备份数据库

```bash
docker-compose exec db pg_dump -U kgschema kgschema > backup.sql
```

### 恢复数据库

```bash
docker-compose exec -T db psql -U kgschema kgschema < backup.sql
```

## 监控

### 查看资源使用

```bash
docker stats
```

### 健康检查

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost/
```
