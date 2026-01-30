# GitHub Deployment Guide

## 部署到 GitHub

### 方法 1: 使用部署脚本（推荐）

```bash
./deploy-to-github.sh
```

脚本会引导你完成整个过程。

### 方法 2: 手动部署

#### 步骤 1: 在 GitHub 上创建仓库

1. 访问 https://github.com/new
2. Repository name: `sentiment-radar` (或你喜欢的名称)
3. 选择 Public 或 Private
4. **不要**勾选 "Initialize this repository with a README"
5. 点击 "Create repository"

#### 步骤 2: 添加远程仓库

```bash
# 替换 YOUR_USERNAME 为你的 GitHub 用户名
git remote add origin https://github.com/YOUR_USERNAME/sentiment-radar.git
```

或者使用 SSH:
```bash
git remote add origin git@github.com:YOUR_USERNAME/sentiment-radar.git
```

#### 步骤 3: 推送代码

```bash
# 确保所有更改已提交
git add -A
git commit -m "Initial commit"

# 推送到 GitHub
git push -u origin main
```

### 验证部署

部署成功后，访问你的 GitHub 仓库：
```
https://github.com/YOUR_USERNAME/sentiment-radar
```

### 常见问题

#### 1. 认证问题

如果遇到认证问题，可以使用以下方法：

**使用 GitHub CLI:**
```bash
gh auth login
```

**使用 Personal Access Token:**
1. 访问 https://github.com/settings/tokens
2. 生成新的 token (classic)
3. 使用 token 作为密码

**使用 SSH 密钥:**
```bash
# 生成 SSH 密钥（如果还没有）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加到 GitHub
# 复制公钥内容
cat ~/.ssh/id_ed25519.pub

# 添加到 GitHub: Settings > SSH and GPG keys > New SSH key
```

#### 2. 仓库已存在

如果远程仓库已存在，可以更新：
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/sentiment-radar.git
```

#### 3. 分支名称不同

如果你的默认分支不是 `main`，使用：
```bash
git push -u origin YOUR_BRANCH_NAME
```

### 后续更新

推送更新到 GitHub：
```bash
git add -A
git commit -m "Your commit message"
git push
```

### 仓库信息

- **仓库名称**: Sentiment Alpha Radar
- **描述**: A full-stack application for analyzing user sentiment on X (Twitter)
- **主要技术**: FastAPI, Python, Docker
- **许可证**: MIT (可选)

### 注意事项

⚠️ **重要**: 确保 `.env` 文件在 `.gitignore` 中，不要将 API 密钥推送到 GitHub！

检查 `.gitignore` 包含：
```
.env
```
