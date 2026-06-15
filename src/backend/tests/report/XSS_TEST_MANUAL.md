# XSS安全测试执行手册

## 快速开始

### 1. 环境准备

```bash
cd src/backend

# 安装测试依赖
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio

# 确保bleach库已安装
pip install bleach
```

### 2. 运行所有XSS测试

```bash
# 运行完整测试套件
pytest tests/test_security_xss_injection.py -v

# 生成详细报告
pytest tests/test_security_xss_injection.py -v --tb=short

# 生成覆盖率报告
pytest tests/test_security_xss_injection.py --cov=app --cov-report=html
```

### 3. 运行特定测试类

```bash
# 测试笔记内容XSS防护
pytest tests/test_security_xss_injection.py::TestXSSInjectionInNotesContent -v

# 测试笔记标题XSS防护
pytest tests/test_security_xss_injection.py::TestXSSInjectionInNotesTitle -v

# 测试PDF元数据XSS防护
pytest tests/test_security_xss_injection.py::TestXSSInjectionInPDFMetadata -v

# 测试图谱节点名称XSS防护
pytest tests/test_security_xss_injection.py::TestXSSInjectionInGraphNodeNames -v

# 测试图片文件名安全性
pytest tests/test_security_xss_injection.py::TestXSSInjectionInImageFilenames -v
```

---

## 手动API测试

### 方式1: 使用Swagger UI

1. 启动后端服务
```bash
uvicorn app.main:app --reload
```

2. 打开浏览器访问: http://127.0.0.1:8000/docs

3. 按照以下流程测试:

#### Step 1: 登录
```
POST /api/auth/login
Body: {
  "email": "test@example.com",
  "password": "password123"
}
```
复制返回的 `token` 值

#### Step 2: 创建包含XSS的笔记
```
POST /api/notes/
Authorization: Bearer {token}
Body: {
  "paperId": "paper_123",
  "title": "<img src=x onerror=\"alert('XSS')\">",
  "contentHtml": "<p>Test</p><script>alert('XSS')</script>",
  "contentFormat": "html"
}
```

**预期结果:**
- `data.title`: 应该是转义的纯文本或空字符串
- `data.contentHtml`: 不应该包含 `<script>` 标签

#### Step 3: 验证获取的笔记
```
GET /api/notes/{note_id}
Authorization: Bearer {token}
```

**预期结果:** 返回的 HTML 应该是清洁的，无恶意脚本

---

### 方式2: 使用cURL

```bash
# 1. 登录
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' | jq '.data.token')

echo "Token: $TOKEN"

# 2. 创建包含XSS的笔记
curl -X POST http://127.0.0.1:8000/api/notes/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "paperId": "paper_123",
    "title": "Test<script>alert('"'"'XSS'"'"')</script>",
    "contentHtml": "<p>Content</p><img src=x onerror=\"alert('"'"'XSS'"'"')\">",
    "contentFormat": "html"
  }'

# 3. 查询笔记
NOTEID="note_id_from_response"
curl -X GET http://127.0.0.1:8000/api/notes/$NOTEID \
  -H "Authorization: Bearer $TOKEN"
```

---

### 方式3: 使用REST Client VS Code扩展

1. 安装VS Code插件: REST Client

2. 在项目中创建 `test_xss.http` 文件:

```http
### 登录获取token
POST http://127.0.0.1:8000/api/auth/login
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "password123"
}

### 创建包含XSS脚本的笔记
@token = {{login.response.body.data.token}}

POST http://127.0.0.1:8000/api/notes/
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "paperId": "paper_123",
  "title": "<script>alert('XSS')</script>My Note",
  "contentHtml": "<p>Content</p><img src=x onerror=\"alert('Stored XSS')\">",
  "contentFormat": "html"
}

### 获取笔记验证清洗
@noteId = {{create_note.response.body.data.id}}

GET http://127.0.0.1:8000/api/notes/{{noteId}}
Authorization: Bearer {{token}}

### 测试图片上传 - 危险文件名
POST http://127.0.0.1:8000/api/notes/uploads
Authorization: Bearer {{token}}

< @file="../../../etc/passwd.png"

### 测试搜索 - XSS关键词
GET http://127.0.0.1:8000/api/notes/search?q=<script>alert('XSS')</script>&paperId=paper_123
Authorization: Bearer {{token}}
```

3. 点击每条请求的 "Send Request" 按钮

---

## 测试用例详解

### 测试1: 基本Script标签

**输入:**
```html
<script>alert('XSS')</script>
```

**期望输出:**
```html
(空字符串或纯文本内容)
```

**验证方式:**
```python
from app.utils.sanitize import sanitize_html

result = sanitize_html("<script>alert('XSS')</script>")
assert "<script>" not in result
assert "alert" not in result
```

---

### 测试2: IMG onerror事件

**输入:**
```html
<img src=x onerror="alert('XSS')">
```

**期望输出:**
```html
<img src="x" alt="">
(onerror属性应被移除)
```

**验证方式:**
```python
result = sanitize_html('<img src=x onerror="alert(\'XSS\')">')
assert "onerror" not in result
assert "alert" not in result
```

---

### 测试3: SVG Onload事件

**输入:**
```html
<svg onload="alert('XSS')"></svg>
```

**期望输出:**
```html
(SVG标签应被完全移除)
```

**验证方式:**
```python
result = sanitize_html('<svg onload="alert(\'XSS\')"></svg>')
assert "<svg" not in result
assert "onload" not in result
```

---

### 测试4: IFrame JavaScript协议

**输入:**
```html
<iframe src="javascript:alert('XSS')"></iframe>
```

**期望输出:**
```html
(完全移除)
```

**验证方式:**
```python
result = sanitize_html('<iframe src="javascript:alert(\'XSS\')"></iframe>')
assert "<iframe" not in result
```

---

### 测试5: 文件名路径遍历

**输入:**
```
../../../etc/passwd.png
```

**期望输出:**
```
etc-passwd.png (或类似的清洁名称)
```

**验证逻辑:**
```python
from app.utils.file_handler import sanitize_filename

result = sanitize_filename("../../../etc/passwd.png")
assert ".." not in result
assert "/" not in result
```

---

## 关键检查点

在每个测试后，确认以下几点:

### 笔记创建测试

- [ ] Response 状态码为 200/201
- [ ] `data.contentHtml` 不包含 `<script>`
- [ ] `data.contentHtml` 不包含事件属性 (onclick, onerror等)
- [ ] `data.title` 是纯文本或HTML转义
- [ ] `data.contentText` 是提取的纯文本

### 笔记获取测试

- [ ] 返回的 HTML 与创建后返回的一致
- [ ] 数据库中存储的是清洁的HTML

### 搜索测试

- [ ] 搜索结果中不执行任何脚本
- [ ] 特殊字符被正确处理

### 文件上传测试

- [ ] 返回的文件名安全
- [ ] 文件不在预期目录外
- [ ] 返回的URL正确

---

## 常见问题解答

### Q1: 为什么我的测试失败了?

**A:** 检查以下几点:

1. 确保 `bleach` 库已安装:
```bash
pip install bleach
```

2. 确保 `sanitize_html` 函数已实现:
```python
# 应该存在于 app/utils/sanitize.py
from app.utils.sanitize import sanitize_html
```

3. 检查 `ALLOWED_TAGS` 配置:
```python
ALLOWED_TAGS = ['p','br','strong','em','ul','ol','li','a','code','pre','h1','h2','h3','img']
```

### Q2: 测试中某个XSS向量没有被过滤怎么办?

**A:** 这表示发现了一个安全漏洞! 

1. **记录漏洞**:
```bash
# 在issue中记录
Issue Title: "[Security] XSS vulnerability in {component}"
Description: 以下输入未被正确过滤: {payload}
```

2. **立即修复**:
   - 更新 `sanitize_html` 函数
   - 添加测试用例以确保修复有效
   - 验证该修复不会破坏其他功能

3. **验证修复**:
```bash
pytest tests/test_security_xss_injection.py -v
```

### Q3: 如何测试文件上传的安全性?

**A:** 使用以下Python脚本:

```python
import requests

TOKEN = "your_token_here"
headers = {"Authorization": f"Bearer {TOKEN}"}

# 测试1: 正常文件上传
with open("test_image.png", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://127.0.0.1:8000/api/notes/uploads",
        files=files,
        headers=headers
    )
    print("正常上传:", response.json())

# 测试2: 危险文件名
dangerous_names = [
    "../../../etc/passwd.png",
    "file\x00.png",
    "file<script>.png",
]

for name in dangerous_names:
    # 创建临时文件
    with open(name.replace("\x00", "").replace("<", "").replace(">", ""), "w") as tmp:
        tmp.write("test")
    # 上传并检查返回的文件名是否安全
```

### Q4: 如何验证JSON响应的安全性?

**A:** 检查JSON编码:

```python
import json

# 检查HTML特殊字符是否正确转义
response = {
    "title": '<script>alert("XSS")</script>',
    "content": '<img src=x onerror="alert(\'XSS\')">'
}

json_str = json.dumps(response)
print("JSON输出:", json_str)

# 再次解析验证数据完整性
parsed = json.loads(json_str)
assert parsed["title"] == response["title"]
assert parsed["content"] == response["content"]
```

---

## 性能测试

运行性能测试以确保安全清洗不会显著影响性能:

```bash
# 安装性能测试工具
pip install pytest-benchmark

# 运行性能测试
pytest tests/test_security_xss_injection.py::test_sanitize_performance -v --benchmark-only
```

---

## 日志和调试

### 启用调试日志

```python
# 在 app/main.py 中
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 在 sanitize 函数中添加日志
def sanitize_html(raw_html: str) -> str:
    logger.debug(f"Sanitizing HTML: {raw_html[:100]}...")
    result = bleach.clean(...)
    logger.debug(f"Result: {result[:100]}...")
    return result
```

### 检查清洗过程

```python
# test_debug.py
from app.utils.sanitize import sanitize_html, html_to_text

test_html = '<p>Safe</p><script>alert("XSS")</script>'
print(f"Input: {test_html}")
print(f"Sanitized: {sanitize_html(test_html)}")
print(f"Text: {html_to_text(test_html)}")
```

运行: `python test_debug.py`

---

## 持续集成配置

将测试集成到CI/CD流程:

### GitHub Actions 示例

```yaml
name: Security Tests

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: |
          pip install -r src/backend/requirements.txt
          pip install pytest pytest-cov
      
      - name: Run XSS tests
        run: |
          pytest src/backend/tests/test_security_xss_injection.py -v --cov=app
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 结果解释

### 测试通过的标志

✅ **所有测试通过**: 
- 所有XSS向量都被正确处理
- 没有发现可执行的脚本
- 文件名安全

⚠️ **部分测试失败**:
- 发现XSS漏洞
- 需要修复和重新测试

❌ **多个测试失败**:
- 系统安全防护不足
- 需要全面安全审查

---

## 下一步行动

1. **完成所有测试**: 确保通过率为100%
2. **实现修复**: 按优先级修复发现的漏洞
3. **定期复测**: 每月运行一次完整测试
4. **代码审查**: 新功能合并前进行安全审查
5. **安全培训**: 团队成员学习XSS防护知识

---

**最后更新**: 2026-06-13  
**下次计划复测**: 2026-07-13
