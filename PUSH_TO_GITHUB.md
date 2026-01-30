# 推送到 GitHub 的几种方法

## 方法 1: 使用 GitHub CLI (推荐)

如果你已经安装了 GitHub CLI 并登录：

```bash
gh auth login
git push -u origin main
```

## 方法 2: 使用 Personal Access Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" > "Generate new token (classic)"
3. 选择权限：至少需要 `repo` 权限
4. 生成并复制 token

然后使用 token 作为密码推送：

```bash
git push -u origin main
# Username: archland48
# Password: <粘贴你的 token>
```

或者配置 credential helper：

```bash
git config --global credential.helper osxkeychain  # macOS
git push -u origin main
```

## 方法 3: 使用 SSH (推荐用于长期使用)

### 步骤 1: 生成 SSH 密钥（如果还没有）

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

### 步骤 2: 添加 SSH 密钥到 GitHub

```bash
# 复制公钥
cat ~/.ssh/id_ed25519.pub
```

然后：
1. 访问 https://github.com/settings/ssh/new
2. 粘贴公钥内容
3. 点击 "Add SSH key"

### 步骤 3: 更改远程 URL 为 SSH

```bash
git remote set-url origin git@github.com:archland48/Sentiment-Radar.git
git push -u origin main
```

## 方法 4: 使用 GitHub Desktop

1. 打开 GitHub Desktop
2. File > Add Local Repository
3. 选择项目文件夹
4. 点击 "Publish repository"

## 当前状态

- ✅ 远程仓库已配置: https://github.com/archland48/Sentiment-Radar.git
- ⏳ 等待认证后推送

## 快速推送命令

选择一种方法后，运行：

```bash
cd "/Users/apple/Downloads/sentiment alpha"
git push -u origin main
```
