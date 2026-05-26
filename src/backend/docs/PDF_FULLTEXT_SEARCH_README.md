# PDF 全文搜索功能文档

## 📖 功能概述

Scider 现已支持基于 **MySQL FULLTEXT + ngram** 的 PDF 全文搜索功能，提供以下特性：

- ✅ **中文分词搜索**：使用 ngram 二元分词实现中英文混合搜索
- ✅ **关键词高亮**：搜索结果自动高亮显示匹配内容
- ✅ **快速跳转**：点击搜索结果直接跳转到对应页面
- ✅ **零依赖部署**：无需额外搜索引擎，利用现有 MySQL 基础设施
- ✅ **异步索引**：PDF 上传后自动后台索引，不阻塞主流程

## 🏗️ 技术架构

### 核心技术栈
- **搜索引擎**: MySQL 8.0 FULLTEXT Index + ngram Parser
- **分词配置**: `ngram_token_size = 2`（二元分词）
- **后端框架**: FastAPI + SQLAlchemy (asyncmy)
- **前端框架**: Vue 3 + TypeScript + Element Plus

### 工作流程
```
用户上传 PDF
    ↓
PDF 解析完成 (parse_pdf_task)
    ↓
保存完整文本到 paper.full_text
    ↓
创建 FULLTEXT 索引（自动）
    ↓
前端搜索 API (/api/papers/{id}/search)
    ↓
返回高亮结果 → 点击跳转
```

## 🚀 部署与启动

### 1. 执行数据库迁移

```bash
cd src/backend/db
alembic upgrade head
```

这将执行迁移文件 `0007_add_fulltext_search.py`，添加：
- `paper.full_text` 字段（LONGTEXT）
- FULLTEXT 索引 `ft_idx_full_text`（使用 ngram 分词器）

### 2. 重启 Docker 服务

```bash
cd src/backend
docker compose down
docker compose up -d
```

MySQL 将自动加载 ngram 配置参数。

### 3. 验证配置

连接 MySQL 后执行：

```sql
SHOW VARIABLES LIKE 'ngram_token_size';
-- 应返回: ngram_token_size = 2

SHOW VARIABLES LIKE 'innodb_ft_min_token_size';
-- 应返回: innodb_ft_min_token_size = 2

SHOW INDEX FROM paper WHERE Key_name = 'ft_idx_full_text';
-- 应显示 FULLTEXT 索引信息
```

## 📝 使用说明

### 前端操作

1. **打开搜索面板**
   - 在 PDF 预览页面，点击右上角 🔍 图标
   - 或使用快捷键 `Ctrl+F` (Mac: `Cmd+F`)

2. **输入关键词**
   - 在搜索框中输入中文或英文关键词
   - 系统会自动防抖搜索（500ms 延迟）

3. **查看结果**
   - 结果列表显示匹配的页码和高亮片段
   - 黄色背景标记关键词位置

4. **跳转到页面**
   - 点击任意搜索结果，自动跳转到对应页面

### API 调用示例

```bash
# 在论文中搜索关键词
curl -X POST http://localhost:8000/api/papers/{paper_id}/search \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "深度学习",
    "page_number": null,
    "limit": 50
  }'
```

响应示例：
```json
{
  "code": 0,
  "msg": "搜索成功",
  "data": {
    "keyword": "深度学习",
    "total_results": 5,
    "results": [
      {
        "page_number": 3,
        "content": "原始文本内容...",
        "score": 1.0,
        "highlights": [
          "...这是关于<em class='search-highlight'>深度学习</em>的研究..."
        ]
      }
    ]
  }
}
```

## 🔧 高级配置

### MySQL 配置优化

如需调整 ngram 分词粒度，修改 `docker-compose.yml`：

```yaml
services:
  mysql:
    command: >
      --ngram_token_size=2        # 可选值: 1, 2, 3
      --innodb_ft_min_token_size=2
```

- `ngram_token_size=1`: 单字分词，精度高但索引大
- `ngram_token_size=2`: 二元分词，平衡方案（推荐）
- `ngram_token_size=3`: 三元分词，索引小但可能漏词

### 性能监控

```sql
-- 查看索引大小
SELECT 
    INDEX_NAME,
    ROUND(STAT_VALUE * @@innodb_page_size / 1024 / 1024, 2) AS size_mb
FROM mysql.innodb_index_stats
WHERE TABLE_NAME = 'paper'
  AND INDEX_NAME = 'ft_idx_full_text';

-- 定期优化索引（低峰期执行）
OPTIMIZE TABLE paper;
```

## ⚠️ 注意事项

### 1. 适用场景
- ✅ 论文数量 < 100 万篇
- ✅ 中小规模知识库
- ✅ 快速上线、降低运维成本

### 2. 技术限制
- ❌ 不支持模糊搜索和拼写容错
- ❌ 中文分词质量不如 ES 的 IK Analyzer
- ❌ 相关性排序仅基于 TF-IDF

### 3. 索引延迟
- 新上传的 PDF 需要等待解析完成才能搜索
- 通常在几秒到几十秒内完成（取决于 PDF 大小）
- 如搜索无结果，请稍等片刻再试

### 4. 故障排查

**问题**: 搜索返回空结果
```bash
# 检查论文是否已解析完成
SELECT id, status, LENGTH(full_text) FROM paper WHERE id = 'YOUR_PAPER_ID';

# 检查 FULLTEXT 索引是否存在
SHOW INDEX FROM paper WHERE Key_name = 'ft_idx_full_text';

# 手动测试搜索
SELECT MATCH(full_text) AGAINST ('深度学习' IN NATURAL LANGUAGE MODE) AS score
FROM paper
WHERE id = 'YOUR_PAPER_ID';
```

**问题**: ngram 配置未生效
```bash
# 重启 MySQL 容器
docker compose restart mysql

# 验证配置
docker compose exec mysql mysql -u root -p -e "SHOW VARIABLES LIKE 'ngram_token_size';"
```

## 📊 性能指标

| 指标 | 目标值 |
|------|--------|
| 查询延迟 (P95) | < 200ms |
| 单篇论文搜索时间 | < 50ms |
| 索引大小占比 | 原文的 30-50% |
| 防抖时间 | 500ms |
| 最大返回结果数 | 50（可配置至 200）|

## 🔄 维护操作

### 重建索引

如需重新构建全文索引：

```sql
-- 删除并重建索引
ALTER TABLE paper DROP INDEX ft_idx_full_text;
ALTER TABLE paper ADD FULLTEXT INDEX ft_idx_full_text (full_text) WITH PARSER ngram;
```

### 数据清理

```sql
-- 清理空文本记录
UPDATE paper SET full_text = NULL WHERE full_text = '';

-- 统计索引覆盖率
SELECT 
    COUNT(*) AS total_papers,
    SUM(CASE WHEN full_text IS NOT NULL THEN 1 ELSE 0 END) AS indexed_papers
FROM paper;
```

## 🎯 未来优化方向

### 短期优化（1-2周）
- [ ] 添加搜索历史记录（Redis）
- [ ] 支持多关键词组合搜索
- [ ] 优化高亮算法（上下文智能截取）

### 中期优化（1-2月）
- [ ] 引入拼音搜索（中文转拼音）
- [ ] 同义词扩展（如 "AI" → "人工智能"）
- [ ] 搜索结果排序优化（结合引用次数、年份）

### 长期规划（3-6月）
- [ ] 百万级数据后迁移到 Elasticsearch
- [ ] 引入 BM25 相关性算法
- [ ] 支持模糊搜索和拼写容错

## 📚 相关文档

- [数据库迁移指南](../db/README.md)
- [PDF 解析流水线](pdf_parse_pipeline.md)
- [API 接口文档](../../openapi.json)

---

**最后更新**: 2026-05-26  
**版本**: v1.0.0
