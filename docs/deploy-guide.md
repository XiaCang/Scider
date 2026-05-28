# Scider 后端自动化部署指南

本项目使用 **GitHub Actions** 实现 CI/CD 自动化部署，通过 Docker 容器化方式将后端服务部署到远程服务器。

---

## 目录

1. [整体架构](#1-整体架构)
2. [CI/CD 工作流说明](#2-cicd-工作流说明)
3. [前置准备](#3-前置准备)
4. [GitHub Secrets 配置](#4-github-secrets-配置)
5. [服务器初始化](#5-服务器初始化)
6. [触发部署](#6-触发部署)
7. [本地一键部署](#7-本地一键部署)
8. [常见问题](#8-常见问题)

---

## 1. 整体架构

```
                    GitHub Actions                        远程服务器
                ┌──────────────────────┐             ┌──────────────────────┐
                │  1. test (pytest)     │             │                      │
                │  2. build-and-push    │──docker──▶  │  /opt/scider/        │
                │     (Docker 镜像 → GHCR) │  pull      │  ├── src/backend/   │
                │  3. deploy (SSH)      │────ssh────▶ │  │   ├── docker-compose.yml│
                └──────────────────────┘             │  │   ├── .env         │
                                                      │  │   └── app/ ...    │
                                                      │  ├── src/frontend/   │
                                                      │  └── .github/        │
                                                      └──────────────────────┘
```

- **GitHub Container Registry (GHCR)**：存储 Docker 镜像
- **`src/backend/docker-compose.yml`**：在服务器上编排所有后端服务
- **GitHub Actions**：自动构建镜像 → 推送 GHCR → SSH 登录服务器部署

> 💡 服务器克隆的是**完整仓库**（含前端代码），但 Docker 容器完全隔离，前端文件不会对后端运行产生任何影响，请放心。

---

## 2. CI/CD 工作流说明

文件：`.github/workflows/backend-cicd.yml`

### 触发条件

| 事件 | 分支 | 执行阶段 |
|---|---|---|
| `push` | `dev` | test → build-and-push → deploy (dev) |
| `push` | `main` | test → build-and-push → deploy (production) |
| `pull_request` | `dev` | test（不构建/部署） |

> ✅ Merge PR 到 `dev` 会产生 `push` 事件，**同样会触发完整部署流程**。

### 三个阶段

| Job | 功能 |
|---|---|
| **test** | 启动 MySQL + Redis 服务容器，运行 `pytest` |
| **build-and-push** | 构建 `backend` 和 `worker` 两个 Docker 镜像，推送到 GHCR |
| **deploy** | SSH 登录服务器 → 拉取新镜像 → 执行数据库迁移 → 重启服务 |

### 镜像 Tag 规则

| 分支 | 后端 Tag | Worker Tag | 额外 Tag |
|---|---|---|---|
| `main` | `main` | `worker-main` | `sha-<commit>` |
| `dev` | `dev` | `worker-dev` | `sha-<commit>` |

---

## 3. 前置准备

### 3.1 服务器要求

- **操作系统**：Ubuntu 20.04+ / CentOS 7+
- **已安装**：
  - Docker（≥ 24.0）
  - Docker Compose Plugin（`docker compose` 命令可用）
  - Git
- **开放端口**：8000（后端 API）

### 3.2 本地要求

- GitHub 仓库已推送至 `github.com`
- 你有仓库的 **Admin** 或 **Maintain** 权限

---

## 4. GitHub Secrets 配置

前往 GitHub 仓库 → **Settings → Secrets and variables → Actions**，添加以下 Repository secrets：

| Secret 名称 | 说明 | 示例值 |
|---|---|---|
| `SERVER_IP` | **dev** 服务器公网 IP | `39.107.252.200` |
| `SERVER_USER` | **dev** 服务器 SSH 用户名 | `root` |
| `SSH_PRIVATE_KEY` | 服务器的 SSH 私钥（**不要泄露！**） | `-----BEGIN OPENSSH PRIVATE KEY-----\n...` |
| `GHCR_PAT` | GitHub Personal Access Token（用于服务器拉取镜像） | `ghp_xxxxxxxxxxxx` |
| `PROD_SERVER_IP` | **生产**服务器公网 IP（可选） | `1.2.3.4` |
| `PROD_SERVER_USER` | **生产**服务器 SSH 用户名（可选） | `root` |

### SSH 密钥对生成方法

```bash
# 在本地电脑生成（不要在你的服务器上生成）
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github-actions

# 将公钥添加到服务器
ssh-copy-id -i ~/.ssh/github-actions.pub root@39.107.252.200

# 测试连接
ssh -i ~/.ssh/github-actions root@39.107.252.200 "echo ok"

# 查看私钥内容（完整复制，填入 SSH_PRIVATE_KEY）
cat ~/.ssh/github-actions
```

> ⚠️ `SSH_PRIVATE_KEY` 是**私钥文件**（没有 `.pub` 后缀），内容以 `-----BEGIN` 开头、`-----END` 结尾，复制时不要漏掉任何字符。

### GHCR PAT 获取方法

1. GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. 点击 **Generate new token**
3. 设置：
   - **Token name**: `ghcr-deploy`
   - **Expiration**: 根据需要选择
   - **Repository access**: 选择你的仓库
   - **Permissions** → **Container repositories**: `Read`
4. 生成后将 token 值填入 `GHCR_PAT`

---

## 5. 服务器初始化

首次部署前，需要在服务器上完成以下初始化：

### 5.1 安装 Docker

```bash
# Ubuntu
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker

# 验证
docker --version
docker compose version
```

### 5.2 克隆完整仓库

> 如果 `/opt/scider/` 已经存在老文件，先用 `` 备份再清空。

```bash
# 若已存在后端文件，先备份关键配置
cp /opt/scider/.env ~/env.backup 2>/dev/null || echo "没有 .env 需备份"

# 清空目录（如有必要）
rm -rf /opt/scider/* /opt/scider/.* 2>/dev/null

# 创建目录并克隆完整仓库
mkdir -p /opt/scider
cd /opt/scider
git clone <你的仓库URL> .

# 切换到 dev 分支
git checkout dev
```

### 5.3 配置 .env

`.env` 放在 compose 文件同目录（`src/backend/.env`）下，Docker Compose 会自动加载它：

```bash
# 从模板创建 .env
cp src/backend/.env.example src/backend/.env
vim src/backend/.env
```

`.env` 中关键配置项：

```bash
# 数据库（用户名密码与 docker-compose.yml 中的 MySQL 一致）
DATABASE_URL=mysql+asyncmy://root:你的密码@mysql:3306/db?charset=utf8mb4

# Redis（docker compose 中服务名为 redis，所以用主机名 redis）
REDIS_BROKER_URL=redis://redis:6379/0
REDIS_RESULT_BACKEND=redis://redis:6379/1
REDIS_VERIFY_URL=redis://redis:6379/2

# LLM API Key（至少填一个）
DEEPSEEK_API_KEY=你的key
# 或
QWEN_API_KEY=你的key

# SMTP 配置（用于发送注册验证码）
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USER=你的邮箱
SMTP_PASS=你的授权码
```

### 5.4 验证结构

```bash
# 确认关键文件存在
ls -la /opt/scider/src/backend/docker-compose.yml
ls -la /opt/scider/src/backend/.env

# 删除旧 venv（非 Docker 部署已用不到）
rm -rf /opt/scider/venv 2>/dev/null || true
```

---

## 6. 触发部署

### 自动触发

只需推送代码到指定分支，GitHub Actions 会自动执行完整流水线：

```bash
# 部署到 dev 环境
git checkout dev
git add .
git commit -m "feat: xxx"
git push origin dev

# 部署到生产环境
git checkout main
git merge dev
git push origin main
```

### 手动触发

可以在 GitHub 仓库的 **Actions** 标签页中：
1. 选择 **Backend CI/CD** workflow
2. 点击 **Run workflow**
3. 选择分支后运行

---

## 7. 本地一键部署

如果你不想用 GitHub Actions，也可以在本地运行 `deploy.sh` 脚本：

```bash
# 设置 GHCR 访问令牌
export GHCR_PAT="ghp_xxxxxxxxxxxx"

# 运行部署脚本
cd src/backend
bash deploy.sh
```

此脚本会：
1. SSH 登录服务器
2. 拉取最新代码
3. 登录 GHCR
4. 拉取最新 Docker 镜像
5. 执行数据库迁移
6. 重启 backend + worker 服务
7. 清理旧镜像

---

## 8. 常见问题

### Q1：部署后服务启动失败

```bash
# SSH 到服务器查看日志
ssh root@<服务器IP>
docker compose -f /opt/scider/src/backend/docker-compose.yml logs backend
```

### Q2：数据库迁移失败

```bash
# 手动执行迁移
docker compose -f /opt/scider/src/backend/docker-compose.yml run --rm --entrypoint "" backend \
  sh -c "cd /app/db && alembic upgrade head"
```

### Q3：镜像拉取失败（权限问题）

确认 `GHCR_PAT` 有效且有 `read:packages` 权限，以及服务器上执行了 `docker login ghcr.io`。

### Q4：如何回滚到旧版本

```bash
# 手动指定旧镜像 tag 启动
docker compose -f /opt/scider/src/backend/docker-compose.yml stop backend worker
docker compose -f /opt/scider/src/backend/docker-compose.yml rm -f backend worker

# 修改 src/backend/docker-compose.yml 中的 image tag 为旧的 sha 值
# 然后重新 up
docker compose -f /opt/scider/src/backend/docker-compose.yml up -d backend worker
```

或者通过 GitHub Actions 重新运行上一次成功的 workflow。

### Q5：端口冲突

如果服务器的 8000 端口已被占用，修改 `src/backend/docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8001:8000"  # 宿主机 8001 → 容器 8000
```

---

## 参考文件

| 文件 | 说明 |
|---|---|
| `.github/workflows/backend-cicd.yml` | CI/CD 工作流定义 |
| `src/backend/deploy.sh` | 本地一键部署脚本 |
| `src/backend/docker-compose.yml` | Dev 环境容器编排 |
| `src/backend/docker-compose.prod.yml` | 生产环境容器编排 |
| `src/backend/Dockerfile` | Backend API 镜像构建 |
| `src/backend/Dockerfile.worker` | Celery Worker 镜像构建 |
| `src/backend/docker-entrypoint.sh` | 容器入口（自动执行迁移） |
