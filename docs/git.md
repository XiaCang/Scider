# Git Commit 提交规范指南

## 1. 提交格式
每次提交应包含：Header（必需）、Body（可选）、Footer（可选）。

格式：
<type>(<scope>): <subject>
<空行>
<body>
<空行>
<footer>

---

## 2. Type（必需）
用于说明 commit 的类别，只允许使用下面 7 个标识：

- feat:      新功能 (feature)
- fix:       修补 bug
- docs:      文档修改 (documentation)
- style:     格式修改（不影响代码运行的变动，如空格、分号等）
- refactor:  重构（即不是新增功能，也不是修改 bug 的代码变动）
- test:      增加测试或更新现有测试
- chore:     构建过程或辅助工具的变动（如依赖更新、配置修改）
- perf:      提高性能的代码更改
- ci:        CI 配置、脚本文件等变动

## 3. Scope（可选）
说明 commit 影响的范围，比如：数据层、控制层、某个特定模块等。

## 4. Subject（必需）
提交说明的简短描述：
- 建议使用中文，以动词开头（如：“增加”、“修复”、“修改”）
- 结尾不加句号
- 尽量控制在 50 个字符以内

## 5. Body（可选）
对本次提交的详细描述。可以说明修改的原因、背景、解决问题的逻辑等。

## 6. Footer（可选）
用于不兼容变动（Breaking Change）或关闭 Issue：
- BREAKING CHANGE: 后面跟变动的详细说明
- Closes #123, #245