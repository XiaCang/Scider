# 前端测试报告

**生成日期**: 2026-06-15  
**项目**: Scider — 学术论文管理平台  
**测试框架**: Vitest v4.1.7 + happy-dom  
**执行方式**: `vitest run`

---

## 汇总

| 指标 | 数值 |
|---|---|
| 测试文件 | 20 个 |
| 全部通过 | 20 个 |
| 总用例数 | 207 |
| 通过 | 207 (100%) |
| 失败 | 0 |
| 执行时长 | ~3.5s |

---

## 分模块详情

### 1. API 层

| 文件 | 用例数 | 结果 | 测试内容 |
|---|---|---|---|
| `auth.test.ts` | 10 | ✅ 全部通过 | login/register/sendCode/getProfile/changePassword/changePasswordByOld/updateProfile/avatar CRUD |
| `discover.test.ts` | 8 | ✅ 全部通过 | 论文搜索（含筛选参数）、推荐、引用上游/下游（含超时）、引用图谱、单篇/批量导入、PDF 代理下载 |
| `graph.test.ts` | 10 | ✅ 全部通过 | 相似度/LLM 图谱（含筛选）、节点/边 CRUD、自定义图谱、图谱 AI 问答 |
| `library.test.ts` | 22 | ✅ 全部通过 | 论文 CRUD、文件夹 CRUD（含子文件夹、移动、复制）、论文-文件夹关联（含批量）、PDF 信息/文件获取、笔记 CRUD（含图片上传）、PDF 上传（含批量）、PDF 全文搜索 |
| `settings.test.ts` | 4 | ✅ 全部通过 | LLM 提供商 CRUD |
| `tasks.test.ts` | 2 | ✅ 全部通过 | 任务结果查询、Worker Ping |
| `chat.test.ts` | 12 | ✅ 全部通过 | WebSocket 连接 URL 参数、token/done/error/status 消息分发、send/clear/close 控制、non-JSON 静默容错、未登录返回空控制器 |

### 2. 工具函数 (Utils)

| 文件 | 用例数 | 结果 | 测试内容 |
|---|---|---|---|
| `crypto.test.ts` | 5 | ✅ 全部通过 | SHA-256 哈希：一致性、差异性、空字符串、中文、长度验证 |
| `auth_storage.test.ts` | 11 | ✅ 全部通过 | Token 存取/清除、Profile 存取/清除/JSON 容错、clearAll |
| `url.test.ts` | 7 | ✅ 全部通过 | `resolveBackendUrl`：null/undefined/空字符串→空、绝对 URL 原样返回、相对路径拼接 origin、无 BASE_URL 回退 |

### 3. 组合式函数 (Hooks / Composables)

| 文件 | 用例数 | 结果 | 测试内容 |
|---|---|---|---|
| `useFolderTreeFilter.test.ts` | 11 | ✅ 全部通过 | 搜索过滤（大小写、空词）、四种排序（名称/时间 升降序） |
| `useFolderOperations.test.ts` | 7 | ✅ 全部通过 | 树扁平化、后代判定（含嵌套、非后代、自身、不存在 parentId） |
| `useGuide.test.ts` | 12 | ✅ 全部通过 | 初始状态、start/next/prev/skip/finish 导航、已完成时不再激活、currentStepData 正确性、storageKey 拼接、resetAllTours |

### 4. 论文发现 (Discover)

| 文件 | 用例数 | 结果 | 测试内容 |
|---|---|---|---|
| `useSearch.test.ts` | 8 | ✅ 全部通过 | 搜索结果标准化、空关键词回退到推荐、年份/来源过滤、排序、客户端关键词过滤、清空筛选 |
| `useCitationGraph.test.ts` | 8 | ✅ 全部通过 | 引用图谱加载、上游/下游论文过滤、清除选择、已加载时不重复请求、selectedPaper 三种场景 |

### 5. 状态管理 (Pinia Store)

| 文件 | 用例数 | 结果 | 测试内容 |
|---|---|---|---|
| `folder.test.ts` | 15 | ✅ 全部通过 | 初始状态、加载/失败、currentFolder、创建根/子文件夹、重命名、删除（含当前文件夹复位）、移动（含移到根）、添加论文（含去重）、移除、全局移除、批量添加 |
| `paper.test.ts` | 7 | ✅ 全部通过 | 初始状态、加载论文列表/失败容错、paperMap 映射、保存 KeyPoints（含状态变更）、不存在 paperId 容错、getPapersByIds |
| `auth.test.ts` | 10 | ✅ 全部通过 | 初始未登录、登录成功/失败、注册后自动登录、hydrate（无 token/有效 token/过期 token/去重）、applySession、logout、displayName |
| `pdf.test.ts` | 8 | ✅ 全部通过 | 初始状态、加载 PDF 信息/loading 状态、加载笔记、创建笔记（含未选论文报错）、更新笔记、resetPdf |

### 6. 网络层 (Network)

| 文件 | 用例数 | 结果 | 测试内容 |
|---|---|---|---|
| `request.test.ts` | 10 | ✅ 全部通过 | 请求拦截器（有/无 token）、响应拦截器成功分支（正常响应/业务错误码）、响应拦截器错误分支（401 重定向/登录页豁免/提取 msg/提取 message/网络错误友好提示/超时友好提示）|

---

## 代码覆盖率分析

未配置 `vitest --coverage`，暂无覆盖率数据。建议结合 `@vitest/coverage-v8` 补充覆盖率统计。

覆盖率盲区预估（基于代码结构）：

| 模块 | 风险级别 | 说明 |
|---|---|---|
| Components (16 个) | 🔴 高 | 无任何组件测试（AiChatPanel、MarkdownEditor、PdfUploadDialog 等） |
| Views (6 个) | 🔴 高 | 无任何页面级测试 |
| Router (`router/`) | 🟡 中 | 路由守卫、权限判断未测试 |
| Utils | 🟢 低 | crypto、auth_storage、url 均有覆盖 |
| API 层 (`api/*.ts`) | 🟢 低 | 全部 7 个 API 模块均已覆盖 |
| Hooks | 🟢 低 | useGuide 已补充，核心 composable 全覆盖 |
| Store | 🟢 低 | Pinia store 覆盖率较好（folder、paper、auth、pdf） |

---

## 改进历程

| 日期 | 变更 | 文件数 | 用例数 | 通过率 |
|---|---|---|---|---|
| 2026-06-12 | 初次报告 | 11 | 105 | 98.1% (2 失败) |
| 2026-06-15 | - 修复 2 个失败用例（`request.test.ts`）<br>- 新增 API 层测试 7 个<br>- 新增 URL 工具测试<br>- 新增 useGuide 钩子测试 | 20 | 207 | 100% |

---

## 进一步建议

1. **补充组件测试**：优先覆盖 PdfUploadDialog（文件上传边界逻辑）、AiChatPanel（WebSocket 消息流）、MarkdownEditor（富文本操作）
2. **添加覆盖率报告**：在 `vitest.config.ts` 中启用 `@vitest/coverage-v8`，CI 中设定覆盖率阈值
3. **测试路由守卫**：`router/index.ts` 中的鉴权守卫逻辑缺乏测试，建议补充
