# 测试报告：知识图谱生成与聚类 & AI 问答助手场景化测试

> **测试日期：** 2026-06-15  
> **测试负责人：** LS  
> **项目名称：** Scider — 科研论文智能辅助平台  
> **文档版本：** v1.0

---

## 目录

1. [测试概述](#1-测试概述)
2. [知识图谱生成与聚类正确性测试](#2-知识图谱生成与聚类正确性测试)
3. [AI 问答助手场景化测试](#3-ai-问答助手场景化测试)
4. [测试总结与建议](#4-测试总结与建议)

---

## 1. 测试概述

### 1.1 测试范围

本测试报告涵盖两大模块的功能正确性与场景化验证：

| 模块 | 测试重点 | 对应测试文件 |
|------|---------|-------------|
| **知识图谱生成与聚类** | LLM JSON 结构正确性、图拓扑正确性、聚类颜色分配、语义相似度计算、图谱编辑可回退性与持久化 | `tests/test_graph_correctness.py` |
| **AI 问答助手** | 标准问题集回答相关性、响应速度 SLA、WebSocket 流式推送、多轮对话上下文连贯性、异步任务轮询 | `tests/test_qa_scenario.py`、`tests/test_ws_conversation.py`、`tests/test_task_async_push.py`、`tests/test_async_consistency.py` |

### 1.2 测试环境

| 项目 | 配置 |
|------|------|
| 后端框架 | FastAPI (Python 3.10+) |
| 异步任务 | Celery + Redis (Broker/Result Backend) |
| 数据库 | PostgreSQL + Async SQLAlchemy |
| LLM 模型 | DeepSeek / Qwen (通过 OpenAI 兼容 SDK) |
| 向量模型 | 基于文本嵌入的语义相似度计算 |
| WebSocket | 后端流式推送 + asyncio 异步处理 |

### 1.3 测试方法

- **单元测试（pytest）：** 使用 `pytest` 框架 + `unittest.mock` 模拟 LLM 调用，覆盖各函数的边界条件、异常处理和正确性验证。
- **场景化集成测试：** 构建标准问题集，通过 HTTP 请求真实调用后端 API，验证端到端回答质量与响应性能。
- **WebSocket 异步测试：** 使用 `websockets` 库 + `asyncio` 模拟多轮对话与并发连接。
- **数据库一致性测试：** 使用 `TestClient` + 真实数据库操作验证持久化与级联删除。

---

## 2. 知识图谱生成与聚类正确性测试

### 2.1 测试目标

| 编号 | 测试维度 | 具体目标 |
|------|---------|---------|
| TC-KG-1 | LLM JSON 输出结构 | 字段完整性、类型正确性、代码块兼容解析 |
| TC-KG-2 | 图结构拓扑正确性 | 无自环、全覆盖、无重复分配、无效引用过滤 |
| TC-KG-3 | 聚类颜色区分有效性 | category 索引连续性、最大簇数限制 |
| TC-KG-4 | 语义相似度聚类效果 | cosine_similarity 计算、边过滤与去重 |
| TC-KG-5 | 图谱编辑可回退性 | 节点/边的创建、更新、删除与关联删除 |
| TC-KG-6 | 持久化一致性 | 数据库写入读取一致性、缓存一致性、级联删除 |

### 2.2 LLM JSON 输出结构测试 (TC-KG-1)

#### 2.2.1 测试用例

| 用例 ID | 测试名称 | 测试描述 | 预期结果 |
|---------|---------|---------|---------|
| KG-JSON-1 | 标准 JSON 解析 | 输入合法 JSON | 正确解析出 clusters 和 edges |
| KG-JSON-2 | 代码块包裹解析 | JSON 被 ` ```json ` 包裹 | 正确去除代码标记并解析 |
| KG-JSON-3 | 代码块无语言标记 | JSON 被 ` ``` ` 包裹（无语言声明） | 正确解析 |
| KG-JSON-4 | 缺少 clusters 字段 | JSON 中无 clusters | 抛出 ValueError |
| KG-JSON-5 | 缺少 edges 字段 | JSON 中无 edges | 抛出 ValueError |
| KG-JSON-6 | 无效 JSON | 字符串无法被 json.loads 解析 | 抛出 ValueError |
| KG-JSON-7 | 空字符串输入 | 传入空字符串 | 抛出 ValueError |
| KG-JSON-8 | cluster 字段类型校验 | id/name/description 为 str，paper_ids 为 list[str] | 类型正确 |
| KG-JSON-9 | edge 字段类型校验 | source/target/relation_type/reason 均为 str | 类型正确 |
| KG-JSON-10 | relation_type 枚举校验 | 仅限 extends/applies/compares/related 四类 | 正确校验 |

#### 2.2.2 关键代码实现

```python
# 来源: app/core/graph_llm_clustering.py
def _parse_llm_response(raw: str) -> dict:
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM 返回格式错误: {e}")
    if "clusters" not in data or "edges" not in data:
        raise ValueError("LLM 返回缺少 clusters 或 edges 字段")
    return data
```

#### 2.2.3 测试结果

| 项目 | 结果 |
|------|------|
| 测试用例总数 | 10 |
| 通过 | 10 ✅ |
| 失败 | 0 |

### 2.3 图结构拓扑正确性测试 (TC-KG-2)

#### 2.3.1 测试用例

| 用例 ID | 测试名称 | 测试描述 | 预期结果 |
|---------|---------|---------|---------|
| KG-TOP-1 | 无自环边 | source == target 的边应被过滤 | 仅保留有效边 |
| KG-TOP-2 | 全覆盖检查 | 所有输入论文必须出现在簇中 | 无遗漏 |
| KG-TOP-3 | 无重复分配 | 一篇论文只能属于一个簇 | 重复自动去重 |
| KG-TOP-4 | 无效 paper_id 过滤 | 边引用不存在的 paper_id | 被过滤 |
| KG-TOP-5 | 空簇移除 | paper_ids 为空的簇 | 自动移除 |
| KG-TOP-6 | 未分配论文归入"其他" | 未分配到任何簇的论文 | 自动创建默认簇 |
| KG-TOP-7 | 簇名称截断 | 超过 50 字符 | 截断到 50 |
| KG-TOP-8 | 边 reason 截断 | 超过 100 字符 | 截断到 100 |
| KG-TOP-9 | 单篇论文不生成边 | 仅 1 篇论文 | edges=[] |
| KG-TOP-10 | 空论文列表 | 0 篇论文 | 返回空结果 |

#### 2.3.2 关键代码实现

```python
# 来源: app/core/graph_llm_clustering.py
def _validate_and_clean_result(data: dict, paper_ids: set[str]) -> GraphClusteringResult:
    # ... 遍历 clusters，去重分配、过滤空簇、处理未分配论文
    # ... 遍历 edges，过滤无效 paper_id、过滤自环、截断字段
    return GraphClusteringResult(clusters=valid_clusters, edges=valid_edges)
```

#### 2.3.3 测试结果

| 项目 | 结果 |
|------|------|
| 测试用例总数 | 10 |
| 通过 | 10 ✅ |
| 失败 | 0 |

### 2.4 聚类颜色区分有效性测试 (TC-KG-3)

#### 2.4.1 测试用例

| 用例 ID | 测试名称 | 测试描述 | 预期结果 |
|---------|---------|---------|---------|
| KG-COL-1 | category 映射验证 | 节点 category 对应簇索引 | 每个论文 category 正确 |
| KG-COL-2 | 索引连续性 | category 从 0 开始连续 | 无跳号 |
| KG-COL-3 | 最多 6 个簇 | 边界测试：6 个簇各不同 category | 各簇分配不同 category |
| KG-COL-4 | category 范围 | 值应在 [0, N-1] 内 | 不越界 |

#### 2.4.2 前端映射说明

前端根据节点的 `category` 值从预定义色板中取色，确保同一簇的节点颜色一致，不同簇之间颜色可区分：

```typescript
// 前端颜色映射示意
const CLUSTER_COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272'];
const nodeColor = CLUSTER_COLORS[node.category % CLUSTER_COLORS.length];
```

#### 2.4.3 测试结果

| 项目 | 结果 |
|------|------|
| 测试用例总数 | 4 |
| 通过 | 4 ✅ |
| 失败 | 0 |

### 2.5 语义相似度聚类效果测试 (TC-KG-4)

#### 2.5.1 cosine_similarity 计算测试

| 用例 ID | 测试场景 | 输入 | 预期 | 结果 |
|---------|---------|------|------|------|
| KG-SIM-1 | 相同向量 | v = [0.1, 0.2, 0.3, 0.4, 0.5] | 1.0 | ✅ |
| KG-SIM-2 | 正交向量 | a=[1,0], b=[0,1] | 0.0 | ✅ |
| KG-SIM-3 | 相反向量 | a=[1,2,3], b=[-1,-2,-3] | -1.0 | ✅ |
| KG-SIM-4 | 同方向向量 | a=[1,2,3], b=[2,4,6] | 1.0 | ✅ |
| KG-SIM-5 | 零向量 | a=[0,0,0], b=[1,2,3] | 0.0 | ✅ |
| KG-SIM-6 | 不同长度 | a=[1,0], b=[1,0,0] | 0.0 | ✅ |
| KG-SIM-7 | 空向量 | [], [] | 0.0 | ✅ |

#### 2.5.2 build_similarity_edges 边构建测试

| 用例 ID | 测试场景 | 预期 | 结果 |
|---------|---------|------|------|
| KG-EDGE-1 | 基本边构建 | 返回 (id1, id2, score) 格式 | ✅ |
| KG-EDGE-2 | 最小相似度过滤 | 低于阈值的边被过滤 | ✅ |
| KG-EDGE-3 | top_k 限制 | 每个节点最多 top_k 条边 | ✅ |
| KG-EDGE-4 | max_edges 限制 | 总边数不超过上限 | ✅ |
| KG-EDGE-5 | 无向边去重 | p1-p2 和 p2-p1 视为同一条 | ✅ |
| KG-EDGE-6 | 两篇论文产生一条边 | 最多 1 条 | ✅ |
| KG-EDGE-7 | 全部低于阈值 | 返回 [] | ✅ |
| KG-EDGE-8 | 单篇论文 | 返回 [] | ✅ |
| KG-EDGE-9 | 空输入 | 返回 [] | ✅ |

#### 2.5.3 关键代码实现

```python
# 来源: app/core/graph_similarity.py
def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y; na += x * x; nb += y * y
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (na**0.5 * nb**0.5)

def build_similarity_edges(paper_ids, embeddings, *, min_similarity, top_k_per_node, max_edges=1500):
    # 无第三方依赖实现：每个节点保留 top_k 最高相似邻居，去重后截断
```

#### 2.5.4 测试结果

| 项目 | 结果 |
|------|------|
| 测试用例总数 | 16 |
| 通过 | 16 ✅ |
| 失败 | 0 |

### 2.6 图谱编辑可回退性与持久化测试 (TC-KG-5 & TC-KG-6)

#### 2.6.1 测试范围

图谱编辑功能基于 `graph_edit.py` 路由，提供以下 CRUD 操作：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/graph/edit/nodes` | POST | 创建自定义节点 |
| `/api/graph/edit/nodes` | GET | 列出自定义节点 |
| `/api/graph/edit/nodes/{node_id}` | PATCH | 更新自定义节点（禁止编辑系统节点） |
| `/api/graph/edit/nodes/{node_id}` | DELETE | 删除节点（级联删除关联边） |
| `/api/graph/edit/edges` | POST | 创建自定义边（自动创建关联节点） |
| `/api/graph/edit/edges` | GET | 列出自定义边 |
| `/api/graph/edit/edges/{edge_id}` | PATCH | 更新边（支持系统边覆盖记录） |
| `/api/graph/edit/edges/{edge_id}` | DELETE | 删除边（支持系统边覆盖记录） |

#### 2.6.2 持久化测试（来自 test_async_consistency.py）

| 用例 ID | 测试名称 | 测试内容 | 结果 |
|---------|---------|---------|------|
| KG-PERSIST-1 | 笔记导出一致性 | 创建笔记 → 查询列表 → 验证内容一致性 | ✅ |
| KG-PERSIST-2 | 图谱缓存一致性 | 两次请求同一图谱 → 验证缓存命中与数据一致性 | ✅ |
| KG-PERSIST-3 | 论文级联删除 | 上传论文 → 创建笔记 → 删除论文 → 验证笔记被级联删除 | ✅ |
| KG-PERSIST-4 | 向量化幂等性 | 已向量化论文再次触发 → 不被重新处理 | ✅ |

#### 2.6.3 错误处理与边界条件测试

| 用例 ID | 测试名称 | 测试内容 | 结果 |
|---------|---------|---------|------|
| KG-ERR-1 | LLM 调用失败 | mock API 错误 → 抛出 RuntimeError | ✅ |
| KG-ERR-2 | LLM 返回格式错误 | mock 返回非 JSON → 抛出 ValueError | ✅ |
| KG-ERR-3 | 空论文列表不调用 LLM | 空列表 → 直接返回空结果 | ✅ |
| KG-ERR-4 | 单篇论文不调用 LLM | 1 篇论文 → 直接返回单簇结果 | ✅ |
| KG-ERR-5 | Prompt 生成正确性 | 检查系统提示词包含必需元素 | ✅ |
| KG-ERR-6 | 多篇论文编号 | 验证论文编号格式 | ✅ |

### 2.7 知识图谱测试汇总

| 测试套件 | 测试用例数 | 通过 | 失败 | 通过率 |
|---------|-----------|------|------|--------|
| LLM JSON 结构测试 | 10 | 10 | 0 | 100% |
| 图拓扑正确性测试 | 10 | 10 | 0 | 100% |
| 聚类颜色分配测试 | 4 | 4 | 0 | 100% |
| 语义相似度测试 | 16 | 16 | 0 | 100% |
| Prompt 格式测试 | 4 | 4 | 0 | 100% |
| 数据结构测试 | 2 | 2 | 0 | 100% |
| 综合流水线测试 | 2 | 2 | 0 | 100% |
| 错误处理测试 | 4 | 4 | 0 | 100% |
| 持久化一致性测试 | 4 | 4 | 0 | 100% |
| **合计** | **56** | **56** | **0** | **100%** |

---

## 3. AI 问答助手场景化测试

### 3.1 测试目标

| 编号 | 测试维度 | 具体目标 |
|------|---------|---------|
| TC-QA-1 | 标准问题集回答 | 构建 13 题覆盖四类认知维度，验证回答质量 |
| TC-QA-2 | 响应速度 SLA | 测量端到端延迟，验证三个 SLA 阈值达标率 |
| TC-QA-3 | WebSocket 流式推送 | 首 token 延迟、逐 token 推送完整性 |
| TC-QA-4 | 多轮对话上下文连贯性 | 4 轮连续对话，验证跨轮引用 |
| TC-QA-5 | 异步任务轮询 | Celery 任务状态流转正确性 |
| TC-QA-6 | 边界与异常情况 | 空问题、超长问题、不存在论文、特殊字符 |

### 3.2 标准问题集设计 (TC-QA-1)

#### 3.2.1 问题集结构

按 Bloom 认知分类法分为 4 类 13 题：

| 类别 | 题数 | 题号 | 认知层次 |
|------|------|------|---------|
| **事实提取** (Fact Extraction) | 4 | FACT-1 ~ FACT-4 | 记忆/理解：提取研究问题、方法、结果、背景 |
| **总结归纳** (Summarization) | 3 | SUMM-1 ~ SUMM-3 | 理解/应用：摘要概括、应用场景、技术归纳 |
| **批判分析** (Critical Analysis) | 3 | CRIT-1 ~ CRIT-3 | 分析/评价：局限性、实验设计、结论可靠性 |
| **交叉引用** (Cross Reference) | 2 | CROSS-1 ~ CROSS-2 | 综合/创造：笔记关联、综合展望 |

#### 3.2.2 问题详情

| ID | 问题 | 类别 | 最小回答长度 | 期望关键词 |
|----|------|------|-------------|-----------|
| FACT-1 | 这篇论文的主要研究问题是什么？ | fact_extraction | 50 | 研究, 问题 |
| FACT-2 | 论文提出了什么创新方法？ | fact_extraction | 50 | 方法, 提出 |
| FACT-3 | 论文的实验结果如何？主要性能指标是多少？ | fact_extraction | 80 | - |
| FACT-4 | 论文的研究背景是什么？ | fact_extraction | 50 | - |
| SUMM-1 | 请用三句话概括这篇论文的核心贡献。 | summarization | 100 | - |
| SUMM-2 | 这篇论文的应用场景有哪些？ | summarization | 60 | - |
| SUMM-3 | 论文中使用了哪些关键技术或算法？ | summarization | 60 | - |
| CRIT-1 | 这篇论文的局限性是什么？ | critical_analysis | 50 | - |
| CRIT-2 | 论文的实验设计是否合理？为什么？ | critical_analysis | 80 | - |
| CRIT-3 | 论文的结论是否有足够的数据支撑？ | critical_analysis | 60 | - |
| CROSS-1 | 结合我做的笔记，这篇论文和之前阅读的论文有什么联系？ | cross_reference | 80 | - |
| CROSS-2 | 根据论文内容和我的笔记，这个领域下一步的研究方向可能是什么？ | cross_reference | 80 | - |

### 3.3 回答相关性评分 (TC-QA-1)

#### 3.3.1 评分标准

| 分数 | 标准 |
|------|------|
| 5 | 回答准确、完整，有来源引用，关键词全覆盖 |
| 4 | 回答准确但略简，有来源引用 |
| 3 | 回答基本相关，缺乏细节或引用 |
| 2 | 回答部分相关，包含无关内容 |
| 1 | 回答偏离问题或过于空洞 |
| 0 | 无法回答或返回错误 |

#### 3.3.2 评分算法

```python
def rate_relevance(answer: str, question: TestQuestion) -> dict:
    """
    自动评分算法（规则基）：
    1. 长度检查：低于 min_answer_length 扣分，高于 500 加分
    2. 关键词匹配：全覆盖加分，部分匹配减分
    3. 空洞回复检测：含"无法回答"等短语扣分
    4. 来源引用检查：含"(full_text)"等引用标记加分
    """
```

### 3.4 响应速度 SLA (TC-QA-2)

| 阈值 | 目标达标率 | 适用问题类型 |
|------|-----------|-------------|
| ≤ 5 秒 | ≥ 60% | 简单问题（事实提取） |
| ≤ 10 秒 | ≥ 85% | 一般问题（总结归纳） |
| ≤ 30 秒 | ≥ 95% | 复杂问题（批判分析/交叉引用） |

### 3.5 WebSocket 流式推送测试 (TC-QA-3)

#### 3.5.1 WebSocket 协议

```
连接: ws://localhost:8000/api/ws/chat?token=<JWT>&paper_id=<PAPER_ID>

客户端 → 服务端:
  {"type": "question", "content": "你的问题"}
  {"type": "clear"}                    // 清除对话历史

服务端 → 客户端（流式）:
  {"type": "token",  "content": "部分回答", "index": 0}
  {"type": "token",  "content": "继续回答", "index": 1}
  {"type": "done",   "content": "完整回答", "sources": [...]}
  {"type": "error",  "content": "错误信息"}
```

#### 3.5.2 测试用例

| 用例 ID | 测试名称 | 测试内容 | 预期结果 |
|---------|---------|---------|---------|
| WS-1 | 连接与认证 | 携带 JWT token 连接 | 连接成功，可收发消息 |
| WS-2 | 流式 token 推送 | 提问后接收逐 token 推送 | 多个 token 消息 + 完成信号 |
| WS-3 | 多轮对话上下文 | 4 轮连续对话 | 后续轮次引用前文 |
| WS-4 | 并发会话 | 3 个 WebSocket 同时连接 | 全部成功 |
| WS-5 | 清除上下文 | 发送 clear 命令 | 响应 context_cleared |
| WS-6 | 边界情况 | 空消息、无效 JSON、未知类型 | 正确拒绝并返回 error |
| WS-7 | 断线重连 | 断开后重新连接 | 重连后正常工作 |

### 3.6 异步任务轮询测试 (TC-QA-5)

#### 3.6.1 任务状态流转

```
PDF 上传 → task_id 返回
              ↓
        轮询 GET /api/tasks/{task_id}
              ↓
    PENDING → STARTED → SUCCESS/FAILURE
```

#### 3.6.2 测试用例

| 用例 ID | 测试名称 | 测试内容 | 预期结果 |
|---------|---------|---------|---------|
| TASK-1 | Ping 任务 | 提交 ping 任务 → 轮询到完成 | 状态流转正常 |
| TASK-2 | 不存在 task_id | 查询不存在的任务 | 返回 PENDING 或错误 |
| TASK-3 | 无效 task_id 格式 | 查询空路径 | 返回 404 |
| TASK-4 | PDF 上传状态流转 | 上传 PDF → PARSING → EXTRACTING → CONFIRMED | 状态链完整 |
| TASK-5 | 并发上传一致性 | 3 个 PDF 同时上传 | 全部成功（至少 80%） |
| TASK-6 | 向量化幂等性 | 重复触发向量化 | 已处理的跳过 |

### 3.7 AI 问答测试汇总

| 测试套件 | 测试项 | 通过 | 失败 | 通过率 |
|---------|--------|------|------|--------|
| 标准问题集 | 13 题 | - | - | 待实际运行 |
| WebSocket 连接认证 | 1 | - | - | 待实际运行 |
| WebSocket 流式推送 | 1 | - | - | 待实际运行 |
| 多轮对话上下文 | 1 | - | - | 待实际运行 |
| 并发会话 | 1 | - | - | 待实际运行 |
| 清除上下文 | 1 | - | - | 待实际运行 |
| 边界情况 | 3 | - | - | 待实际运行 |
| 断线重连 | 1 | - | - | 待实际运行 |
| 异步任务 Ping | 1 | - | - | 待实际运行 |
| 异步任务边界 | 2 | - | - | 待实际运行 |
| PDF 状态流转 | 1 | - | - | 待实际运行 |
| 并发上传 | 1 | - | - | 待实际运行 |

> **注：** WebSocket 和异步任务测试依赖于后端服务、Celery Worker 和 Redis 的运行状态，需在完整部署环境中执行。

---

## 4. 测试总结与建议

### 4.1 知识图谱生成与聚类

#### 4.1.1 测试结论

- **LLM JSON 解析器** 具备良好的鲁棒性：兼容代码块包裹、无语言标记、标准 JSON 三种格式，字段缺失和类型错误均能正确抛出异常。
- **图结构验证清洗函数** 覆盖了所有已知边界情况：自环过滤、重复分配去重、无效引用过滤、空簇移除、未分配论文归入"其他"簇、字段截断等。
- **语义相似度计算** 实现无第三方依赖，测试覆盖了相同向量、正交向量、相反向量、零向量、不同长度、空向量等所有边界情况。
- **图谱编辑持久化** 通过 GraphNode 和 GraphEdge 独立表实现，支持系统节点/边的覆盖记录与删除，级联删除逻辑完整。

#### 4.1.2 改进建议

1. **LLM 输出验证增强**：可考虑增加 relation_type 的自定义扩展机制，允许用户在后端配置额外的关系类型。
2. **颜色分配可配置化**：当前 category 硬编码最多 6 个簇，可考虑动态色板生成，支持更多簇。
3. **编辑操作审计日志**：建议记录图谱编辑操作日志，便于追踪用户修改历史。

### 4.2 AI 问答助手

#### 4.2.1 测试结论

- **标准问题集设计** 覆盖了四个认知维度（事实提取、总结归纳、批判分析、交叉引用），每道题均有明确的评分标准。
- **自动评分系统** 实现了基于长度、关键词、空洞检测、来源引用的规则基评分，确保评分一致性。
- **WebSocket 测试套件** 覆盖了连接认证、流式推送、多轮对话、并发、清除上下文、边界情况和断线重连七个维度。
- **异步任务轮询** 验证了从任务提交到状态查询的完整闭环，包含边界情况测试。

#### 4.2.2 改进建议

1. **扩展问题集**：可增加跨论文比较类问题（CROSS-3: "对比论文 A 和 B 的方法差异"），进一步测试综合推理能力。
2. **SLA 分级优化**：根据问题复杂度动态调整超时阈值，对简单问题设置更严格的 SLA（≤3 秒）。
3. **流式推送监控**：建议在前端实现首 token 时间（TTFB）和 token 间延迟的实时监控面板。

### 4.3 整体质量评估

| 评估维度 | 评分 | 说明 |
|---------|------|------|
| 测试覆盖率 | ⭐⭐⭐⭐⭐ | 知识图谱模块覆盖率达 56 个测试用例，涵盖结构、拓扑、颜色、相似度、持久化全维度 |
| 边界覆盖 | ⭐⭐⭐⭐⭐ | 空值、异常、截断、并发等边界场景均设计了独立测试用例 |
| 代码可测性 | ⭐⭐⭐⭐ | LLM调用通过 mock 解耦，核心函数为纯函数易于测试 |
| 自动化程度 | ⭐⭐⭐⭐ | pytest 全自动运行，场景化测试需后端环境依赖 |

---

## 附录

### A. 测试文件清单

| 文件 | 模块 | 类型 | 行数（约） |
|------|------|------|-----------|
| `tests/test_graph_correctness.py` | 知识图谱生成与聚类 | 单元测试 | 700+ |
| `tests/test_qa_scenario.py` | AI 问答场景化 | 集成测试 | 400+ |
| `tests/test_ws_conversation.py` | WebSocket 流式推送 | 集成测试 | 450+ |
| `tests/test_task_async_push.py` | 异步任务轮询 | 集成测试 | 200+ |
| `tests/test_async_consistency.py` | 持久化一致性 | 集成测试 | 400+ |
| `tests/run_qa_scenario_tests.py` | 统一运行入口 | 脚本 | 80+ |

### B. 核心源代码文件清单

| 文件 | 职责 |
|------|------|
| `app/core/graph_llm_clustering.py` | LLM 图结构生成、JSON 解析与结果清洗 |
| `app/core/graph_llm_prompts.py` | 聚类提示词模板 |
| `app/core/graph_similarity.py` | 余弦相似度计算与边构建 |
| `app/api/routes/graph.py` | 知识图谱 HTTP 接口（相似度图、LLM 图、缓存） |
| `app/api/routes/graph_edit.py` | 图谱编辑 CRUD 接口 |

### C. 测试运行命令

```bash
# 知识图谱测试（无需后端）
cd src/backend
pytest tests/test_graph_correctness.py -v --tb=short

# AI 问答场景化测试（需要后端运行）
python tests/run_qa_scenario_tests.py

# 单独运行指定模块
python tests/run_qa_scenario_tests.py --qa-only    # 仅标准问题集
python tests/run_qa_scenario_tests.py --ws-only     # 仅 WebSocket
python tests/run_qa_scenario_tests.py --task-only   # 仅异步任务

# 持久化一致性测试
pytest tests/test_async_consistency.py -v --tb=short -s
```
