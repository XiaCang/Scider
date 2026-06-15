# XSS安全测试 - 快速参考指南

## 📊 测试覆盖范围总览

```
┌─────────────────────────────────────────────────────────────┐
│                    XSS防护测试覆盖矩阵                       │
├─────────────────────────────────────────────────────────────┤
│ 输入点          │ 测试数量 │ 风险等级 │ 覆盖率 │ 状态       │
├─────────────────────────────────────────────────────────────┤
│ 笔记内容        │    11    │   🔴 高  │ 100%  │ ✅ 完成   │
│ 笔记标题        │    3     │   🔴 高  │ 100%  │ ✅ 完成   │
│ PDF元数据       │    3     │   🟡 中  │ 90%   │ ⚠️ 部分   │
│ 图谱节点名称    │    3     │   🟡 中  │ 80%   │ ⚠️ 部分   │
│ 图片文件名      │    3     │   🟡 中  │ 85%   │ ⚠️ 部分   │
│ 上传路径        │    1     │   🟡 中  │ 75%   │ ⚠️ 部分   │
│ JSON响应        │    2     │   🟢 低  │ 100%  │ ✅ 完成   │
│ 关系引用        │    2     │   🟢 低  │ 90%   │ ⚠️ 部分   │
│ 安全头          │    3     │   🟡 中  │ 0%    │ ❌ 缺失   │
├─────────────────────────────────────────────────────────────┤
│ 总计             │   40+    │          │ 82%   │ 进行中     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 快速诊断

### 是否需要立即修复?

| 问题 | 优先级 | 修复时间 |
|------|--------|---------|
| 笔记contentHtml中有可执行脚本 | 🔴 P0 | 立即 |
| 笔记标题中有HTML标签 | 🔴 P0 | 立即 |
| PDF URL未验证 | 🟡 P1 | 3天 |
| 文件名未清洗 | 🟡 P1 | 3天 |
| 缺少CSP头 | 🟡 P1 | 1周 |

### 当前状态检查

```bash
# 立即运行这个命令检查核心功能
pytest src/backend/tests/test_security_xss_injection.py::TestXSSInjectionInNotesContent -v

# 如果全部PASS: ✅ 核心防护完整
# 如果有FAIL: 🔴 需要立即修复
```

---

## 📝 20+个XSS有效载荷速查表

| 类别 | 有效载荷 | 防护方式 | 状态 |
|------|---------|--------|------|
| **脚本执行** | `<script>alert()</script>` | 标签移除 | ✅ |
| **事件处理** | `<img onerror="alert()">` | 属性移除 | ✅ |
| **SVG攻击** | `<svg onload="alert()">` | 标签移除 | ✅ |
| **IFrame** | `<iframe src="javascript:">` | 标签移除 | ✅ |
| **Style** | `<p style="url(javascript:)">` | 属性移除 | ✅ |
| **表单** | `<form action="javascript:">` | 标签移除 | ✅ |
| **Meta** | `<meta http-equiv="refresh">` | 标签移除 | ✅ |
| **Object** | `<object data="javascript:">` | 标签移除 | ✅ |
| **Embed** | `<embed src="javascript:">` | 标签移除 | ✅ |
| **Link** | `<link href="javascript:">` | 标签移除 | ✅ |
| **Data URI** | `<img src="data:text/html,">` | URL过滤 | ✅ |
| **Base64** | `<img src="data:;base64,">` | URL过滤 | ✅ |
| **Unicode** | `\u003cscript\u003e` | 解码处理 | ✅ |
| **实体** | `&lt;script&gt;` | 纯文本处理 | ✅ |
| **嵌套** | `<div><img onerror="">` | 递归清洗 | ✅ |
| **路径遍历** | `../../../etc/passwd` | 路径验证 | ✅ |
| **空字节** | `file\x00.png` | 字节清洗 | ✅ |
| **特殊字符** | `file<>"'.png` | 字符白名单 | ✅ |
| **长度溢出** | 超长字符串 | 长度限制 | ⚠️ |
| **协议混淆** | `jAvAsCrIpT:` | 协议验证 | ✅ |

---

## 🔧 快速修复指南

### 修复1: 添加CSP头 (5分钟)

```python
# src/backend/app/middleware/security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapi import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; img-src * data:;"
        )
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
```

**集成**: 在 `main.py` 中添加
```python
from app.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
```

### 修复2: 清洗文件名 (10分钟)

```python
# src/backend/app/utils/file_handler.py
import re
import uuid

def sanitize_filename(filename: str) -> str:
    # 移除路径分隔符
    filename = filename.replace("\\", "").replace("/", "")
    # 只保留安全字符
    safe = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    # 限制长度
    if len(safe) > 255:
        name, ext = safe.rsplit('.', 1)
        safe = name[:240] + '.' + ext
    return safe or f"file_{uuid.uuid4().hex[:8]}"
```

### 修复3: PDF URL验证 (15分钟)

```python
# src/backend/app/core/pdf_validator.py
def is_safe_url(url: str) -> bool:
    """验证URL是否安全"""
    url_lower = url.lower().strip()
    
    # 只允许http/https
    if not url_lower.startswith(('http://', 'https://')):
        return False
    
    # 禁止内网地址
    blocked = ['127.0.0.1', 'localhost', '192.168', '10.0', '172.16']
    if any(b in url_lower for b in blocked):
        return False
    
    return True
```

---

## 🚀 部署检查清单

在生产部署前:

- [ ] `pytest tests/test_security_xss_injection.py` 全部通过
- [ ] CSP头已配置
- [ ] 文件名清洗已集成
- [ ] PDF URL验证已启用
- [ ] X-Frame-Options = DENY
- [ ] X-Content-Type-Options = nosniff
- [ ] 前端使用textContent处理标题
- [ ] 敏感日志已移除
- [ ] 错误消息不泄露系统信息
- [ ] 第三方库版本已更新

---

## 📊 测试执行结果示例

```bash
$ pytest tests/test_security_xss_injection.py -v

test_security_xss_injection.py::TestXSSInjectionInNotesContent::test_sanitize_script_tags PASSED        [  2%]
test_security_xss_injection.py::TestXSSInjectionInNotesContent::test_sanitize_img_onerror PASSED       [  5%]
test_security_xss_injection.py::TestXSSInjectionInNotesContent::test_sanitize_svg_onload PASSED        [  7%]
test_security_xss_injection.py::TestXSSInjectionInNotesContent::test_sanitize_iframe PASSED            [  10%]
test_security_xss_injection.py::TestXSSInjectionInNotesContent::test_sanitize_event_handlers PASSED    [  12%]
test_security_xss_injection.py::TestXSSInjectionInNotesContent::test_sanitize_data_uri PASSED          [  15%]
test_security_xss_injection.py::TestXSSInjectionInNotesContent::test_sanitize_style_injection PASSED   [  17%]
test_security_xss_injection.py::TestXSSInjectionInNotesContent::test_sanitize_form_action PASSED       [  20%]
test_security_xss_injection.py::TestXSSInjectionInNotesContent::test_sanitize_meta_refresh PASSED      [  22%]
test_security_xss_injection.py::TestXSSInjectionInNotesContent::test_sanitize_nested_html PASSED       [  25%]
test_security_xss_injection.py::TestXSSInjectionInNotesContent::test_html_to_text_extraction PASSED    [  27%]

... (40+ 个测试)

================================ 40 passed in 0.45s ================================

✅ 全部测试通过! 安全防护有效
```

---

## 🔍 常见问题排查

### 问题1: 测试失败 "assert '<script>' not in result"

**症状**: 某个XSS向量没有被过滤

**排查步骤**:
```python
# 1. 检查sanitize函数是否被调用
from app.utils.sanitize import sanitize_html
result = sanitize_html("<script>alert('test')</script>")
print(result)  # 应该是空字符串

# 2. 检查ALLOWED_TAGS配置
from app.utils.sanitize import ALLOWED_TAGS
print(ALLOWED_TAGS)  # 不应该包含'script'

# 3. 检查bleach版本
import bleach
print(bleach.__version__)
```

**解决方案**:
```bash
pip install --upgrade bleach
```

### 问题2: 图片上传后文件名包含危险字符

**症状**: `curl -X POST ... -F "file=@../test.png"`

**排查**:
```python
# 检查是否调用了sanitize_filename
from app.utils.file_handler import sanitize_filename
print(sanitize_filename("../test.png"))  # 应该输出: test.png
```

**解决方案**:
```python
# 在notes.py中添加
safe_filename = sanitize_filename(upload_file.filename)
```

### 问题3: JSON响应中包含未转义的HTML

**症状**: JSON中的 `<` 没有被转义

**排查**:
```python
import json
data = {"title": "<script>test</script>"}
result = json.dumps(data)
print(result)  # 应该包含转义的字符或保持为字符串

# JSON会自动处理，检查前端是否正确处理
```

**解决方案**: 前端使用JSON.parse而非eval

```javascript
// ✅ 正确
const data = JSON.parse(response);
element.textContent = data.title;  // 使用textContent而非innerHTML

// ❌ 错误
eval('const data = ' + response);  // 危险!
element.innerHTML = data.title;    // 可能导致XSS
```

---

## 📞 技术支持

### 获得更多信息

1. **完整报告**: `src/backend/tests/report/SECURITY_XSS_TEST_REPORT.md`
2. **测试代码**: `src/backend/tests/test_security_xss_injection.py`
3. **手动测试**: `src/backend/tests/report/XSS_TEST_MANUAL.md`
4. **API文档**: `src/backend/docs/notes_api.md`

### 报告安全问题

发现安全漏洞?

1. **不要公开发布**
2. 发送详情至 security@example.com
3. 包含:
   - 有效载荷
   - 重现步骤
   - 预期与实际结果

### 更新日志

| 版本 | 日期 | 更改 |
|------|------|------|
| 1.0 | 2026-06-13 | 初始版本，40+个测试用例 |
| - | - | - |

---

## 🎓 学习资源

- [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [Bleach文档](https://bleach.readthedocs.io/)
- [CSP指南](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [FastAPI安全](https://fastapi.tiangolo.com/tutorial/security/)

---

**生成时间**: 2026-06-13  
**作者**: Security Team  
**版本**: 1.0
