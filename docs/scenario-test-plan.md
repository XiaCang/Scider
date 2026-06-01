# AI 问答助手场景化测试方案

## 1. 测试目标

对 Scider 系统的 AI 问答功能进行多维度的场景化测试，验证：

| 维度 | 目标 | 衡量指标 |
|------|------|----------|
| **回答相关性** | LLM 基于 PDF 正文和笔记的回答是否准确 | 相关性评分 (0-5) + 关键词覆盖 |
| **响应速度** | 端到端问答延迟 | SLA: ≤5s / ≤10s / ≤30s 达标率 |
| **流式推送** | WebSocket 逐 token 推送的实时性 | 首 token 延迟 + 推送完整性 |
| **上下文连贯** | 多轮对话能否引用前文 | 跨轮次引用检测 |
| **异步可靠性** | Celery 任务状态轮询正确性 | 状态流转完整性 |

## 2. 测试套件架构

```
tests/
├── run_qa_scenario_tests.py        # 统一运行入口
├── test_qa_scenario.py             # 标准问题集 × PDF 场景测试
├── test_ws_conversation.py         # WebSocket 流式 + 多轮对话测试
└── test_task_async_push.py         # Celery 异步任务推送测试
```

## 3. 标准问题集 (13 题)

按认知维度分为 4 类：

### 3.1 事实提取 (FACT-1 ~ FACT-4)

| ID | 问题 | 预期能力 |
|----|------|----------|
| FACT-1 | 这篇论文的主要研究问题是什么？ | 提取研究问题 |
| FACT-2 | 论文提出了什么创新方法？ | 提取方法创新点 |
| FACT-3 | 论文的实验结果如何？主要性能指标是多少？ | 提取实验数据 |
| FACT-4 | 论文的研究背景是什么？ | 提取研究背景 |

### 3.2 总结归纳 (SUMM-1 ~ SUMM-3)

| ID | 问题 | 预期能力 |
|----|------|----------|
| SUMM-1 | 请用三句话概括这篇论文的核心贡献。 | 摘要总结 |
| SUMM-2 | 这篇论文的应用场景有哪些？ | 应用归纳 |
| SUMM-3 | 论文中使用了哪些关键技术或算法？ | 技术归纳 |

### 3.3 批判分析 (CRIT-1 ~ CRIT-3)

| ID | 问题 | 预期能力 |
|----|------|----------|
| CRIT-1 | 这篇论文的局限性是什么？ | 局限识别 |
| CRIT-2 | 论文的实验设计是否合理？为什么？ | 实验评估 |
| CRIT-3 | 论文的结论是否有足够的数据支撑？ | 结论判断 |

### 3.4 交叉引用 (CROSS-1 ~ CROSS-2)

| ID | 问题 | 预期能力 |
|----|------|----------|
| CROSS-1 | 结合我做的笔记，这篇论文和之前阅读的论文有什么联系？ | 笔记关联 |
| CROSS-2 | 根据论文内容和我的笔记，这个领域下一步的研究方向可能是什么？ | 综合展望 |

## 4. 测试流程

### 4.1 前置条件

```bash
# 1. 启动后端
cd src/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. 启动 Celery Worker（新终端）
cd src/backend
celery -A app.worker:celery_app worker --loglevel=info --pool=solo --concurrency=1

# 3. 确保有 CONFIRMED 状态的论文
#    可通过 Swagger UI 上传 PDF：http://localhost:8000/docs
```

### 4.2 运行测试

```bash
# 方式一：统一运行入口（推荐）
cd src/backend
python tests/run_qa_scenario_tests.py

# 方式二：选择性运行
python tests/run_qa_scenario_tests.py --qa-only
python tests/run_qa_scenario_tests.py --ws-only
python tests/run_qa_scenario_tests.py --task-only

# 方式三：pytest 单个文件
pytest tests/test_qa_scenario.py -v --tb=short
python tests/test_qa_scenario.py          # 直接运行

# WebSocket 测试
python tests/test_ws_conversation.py

# 异步任务测试
python tests/test_task_async_push.py
```

## 5. WebSocket 异步推送

### 5.1 协议设计

**连接**: `ws://localhost:8000/api/ws/chat?token=<JWT>&paper_id=<PAPER_ID>`

**客户端 → 服务端**:
```json
{"type": "question", "content": "你的问题"}
{"type": "clear"}                    // 清除对话历史
```

**服务端 → 客户端**（流式）:
```json
{"type": "token",  "content": "部分回答", "index": 0}
{"type": "token",  "content": "继续回答", "index": 1}
{"type": "done",   "content": "完整回答", "sources": [...]}
{"type": "error",  "content": "错误信息"}
```

### 5.2 测试覆盖

| 测试项 | 说明 |
|--------|------|
| 连接认证 | JWT token 认证、缺少 token 拒绝 |
| 流式推送 | 逐 token 推送、首 token 延迟、完成信号 |
| 多轮对话 | 4 轮连续对话、上下文引用检测 |
| 并发会话 | 3 个 WebSocket 同时连接 |
| 清除上下文 | clear 命令正确重置历史 |
| 边界情况 | 空消息、无效 JSON、未知消息类型 |
| 断线重连 | 断开后重新连接正常工作 |

## 6. 回答相关性评分标准

| 分数 | 标准 |
|------|------|
| 5 | 回答准确、完整，有来源引用，关键词全覆盖 |
| 4 | 回答准确但略简，有来源引用 |
| 3 | 回答基本相关，缺乏细节或引用 |
| 2 | 回答部分相关，包含无关内容 |
| 1 | 回答偏离问题或过于空洞 |
| 0 | 无法回答或返回错误 |

## 7. 响应时间 SLA

| 阈值 | 目标达标率 | 说明 |
|------|-----------|------|
| ≤ 5 秒 | ≥ 60% | 简单问题（事实提取） |
| ≤ 10 秒 | ≥ 85% | 一般问题（总结归纳） |
| ≤ 30 秒 | ≥ 95% | 复杂问题（批判分析） |

## 8. 测试报告示例

运行后自动生成结构化的测试报告，包含：

```
📊 AI 问答场景化测试报告
=========================================
📈 总体统计:
   问题总数: 13
   成功: 12 / 失败: 1
   平均响应时间: 4.23s
   平均相关性评分: 3.8 / 5.0

⏱ 响应时间 SLA:
   ≤ 5秒: ████████████████░░░░ 80% (10/13)
   ≤ 10秒: ████████████████████ 100% (13/13)

📂 按类别统计:
   事实提取: 4/4 通过 | 平均评分 4.2 | 平均响应 2.1s
   总结归纳: 3/3 通过 | 平均评分 3.8 | 平均响应 3.5s
   ...

🏆 综合评分: 85.5/100 (等级 B)
```

## 9. 新增测试编写指南

如需新增测试问题，编辑 `test_qa_scenario.py` 中的 `STANDARD_QUESTIONS` 列表：

```python
TestQuestion(
    id="FACT-5",                          # 唯一 ID
    question="论文的数据集是什么？",       # 问题内容
    category="fact_extraction",           # 问题类别
    description="验证能否提取数据集信息",  # 测试意图
    min_answer_length=30,                 # 最小回答长度
    expected_keywords=["数据", "训练"],    # 期望关键词
)
```
