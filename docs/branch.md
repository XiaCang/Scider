# Git 分支管理规范

## 1. 常驻分支 (Long-lived Branches)
- main: 主分支，仅用于发布生产环境的代码。必须保持极度稳定，禁止直接提交代码。
- dev: 开发分支，所有功能分支的汇聚点。代表最新的开发进度。

## 2. 临时分支 (Short-lived Branches)

### feature/* (功能分支)
- 命名：feature/功能名称
- 来源：dev
- 合回：dev
- 说明：用于开发新功能。开发完成后需发起 Pull Request (PR) 经过 Code Review 后合并。

### hotfix/* (热修复分支)
- 命名：hotfix/问题描述 (如: hotfix/ios-crash)
- 来源：main
- 合回：main & develop
- 说明：用于紧急修复生产环境的 Bug。修复后需同时合并回主分支和开发分支。

### release/* (发布预览分支)
- 命名：release/版本号 (如: release/v1.0.0)
- 来源：dev
- 合回：main & dev
- 说明：发布前的最后测试阶段。只允许修复 Bug，不允许加入新功能。

---

## 3. 分支操作核心原则
1. 【禁止直推】：禁止在 main 和 dev 分支上直接进行 git push。
2. 【合并规范】：合并代码前必须先同步目标分支的代码（git pull --rebase），解决冲突后再发起合并。
3. 【删除策略】：功能上线或 hotfix 合并后，应及时删除对应的临时分支，保持仓库整洁。
4. 【标签管理】：每次 main 分支合并 release 或 hotfix 后，必须打上版本 Tag (如 v1.1.2)。

---

## 4. 典型工作流示例
1. 从 dev 拉取 feature/pay-order 开展工作。
2. 开发并自测完成后，提交 PR 请求合并入 develop。
3. 待版本功能集齐，从 develop 拉取 release/v2.0 并在测试环境验证。
4. 验证无误，将 release/v2.0 同时合并入 master 和 develop。
5. 在 master 上打 Tag v2.0，删除 release 分支。