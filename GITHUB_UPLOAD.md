# GitHub 上传指南

按照以下步骤将此项目上传到GitHub：

## 1. 创建GitHub仓库

1. 登录您的GitHub账户
2. 点击右上角的 "+" 按钮，选择 "New repository"
3. 填写仓库名称，例如 "MasterDataMCP"
4. 添加描述（可选）："SAP Material Master Data MCP service"
5. 选择仓库可见性（公开或私有）
6. 不要勾选"Initialize this repository with a README"
7. 点击 "Create repository"

## 2. 初始化本地Git仓库并上传

打开终端，在项目目录中运行以下命令：

```bash
# 初始化Git仓库
git init

# 添加所有文件到暂存区
git add .

# 查看将要提交的文件
git status

# 移除不需要上传的文件（如果有）
# git rm --cached 文件名

# 提交更改
git commit -m "Initial commit"

# 添加远程仓库URL（替换为您的GitHub仓库URL）
git remote add origin https://github.com/yourusername/MasterDataMCP.git

# 推送到GitHub
git push -u origin main
```

如果您的默认分支是master而不是main，则使用：

```bash
git push -u origin master
```

## 3. 后续更新

之后，每次更新代码时，可以使用以下命令：

```bash
# 添加修改的文件
git add .

# 提交更改
git commit -m "描述您的更改"

# 推送到GitHub
git push
```

## 4. 其他注意事项

- 确保 `.env` 文件已被 `.gitignore` 忽略，不要上传敏感信息
- 上传后检查是否有任何敏感信息意外暴露
- 通过GitHub界面可以进一步完善仓库，如添加议题标签、设置分支保护等 