# Chat Response Demo

基于 FastAPI 和 OpenAI API 的流式聊天演示项目，提供美观的 Web 界面和实时流式响应。

## ✨ 特性

### 🎨 前端界面
- ✅ 现代化的渐变色界面设计
- ✅ 实时流式文本显示（逐字输出）
- ✅ 打字指示器动画
- ✅ 响应式布局适配移动端
- ✅ 会话管理功能
- ✅ 流畅的用户体验

### 🚀 后端 API
- ✅ FastAPI 依赖注入和类型安全
- ✅ Server-Sent Events (SSE) 流式响应
- ✅ Pydantic 模型验证
- ✅ CORS 跨域支持
- ✅ 会话状态管理
- ✅ 热重载开发模式

### 🔧 代码质量
- ✅ 完整的类型注解
- ✅ 详细的文档字符串
- ✅ 环境变量配置管理
- ✅ 错误处理和日志记录
- ✅ 标准 JSON 格式输出

## 📸 预览

访问 http://127.0.0.1:8000 查看 Web 界面：
- 🟦 蓝色气泡：用户消息
- ⚪ 白色气泡：AI 回复（流式显示）
- 💬 打字指示器：AI 思考中

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install fastapi uvicorn openai
```

### 2. 配置环境变量

复制环境变量示例文件并配置：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置：
```env
OPENAI_BASE_URL=https://llm.traderwtf.ai
OPENAI_API_KEY=your-api-key-here
HOST=127.0.0.1
PORT=8000
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://127.0.0.1:8000` 启动，浏览器访问即可看到聊天界面。

## 📡 API 端点

### 1. Web 界面
```
GET /
```
自动重定向到 `/static/index.html`，显示聊天界面。

### 2. 聊天流式响应（POST）
```
POST /api/chat
Content-Type: application/json

{
  "question": "你的问题",
  "session_id": "default",
  "model": "g4o"
}
```

**请求体参数：**
- `question` (必填): 用户的问题
- `session_id` (可选): 会话 ID，用于多轮对话，默认 "default"
- `model` (可选): 使用的模型，默认 "g4o"

**返回：** Server-Sent Events (SSE) 格式的流式响应

**示例：**
```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"你好"}' \
  -N
```

### 3. 上传文件
```
POST /api/upload?file_path=customer_policies.txt
```

**参数：**
- `file_path` (必填): 要上传的文件路径

**返回：**
```json
{
  "success": true,
  "vector_store_id": "vs_xxx"
}
```

### 4. 清除会话
```
DELETE /api/session/{session_id}
```

**参数：**
- `session_id` (路径参数): 要清除的会话 ID

**返回：**
```json
{
  "success": true,
  "message": "会话 default 已清除"
}
```

## 📄 SSE 响应格式

流式响应使用 Server-Sent Events 格式，每个事件包含标准 JSON：

```
data: {"type": "event_type", ...}
```

**事件类型：**
- `created`: 响应创建，创建新的消息气泡
- `in_progress`: 响应处理中
- `output_item_added`: 输出项添加
- `content_part_added`: 内容部分添加
- `delta`: 文本增量，逐字更新消息内容
- `text_done`: 文本完成
- `content_part_done`: 内容部分完成
- `output_item_done`: 输出项完成
- `completed`: 响应完成
- `error`: 错误信息

**响应示例：**
```
data: {"type": "created", "id": "resp_xxx"}

data: {"type": "in_progress"}

data: {"type": "output_item_added"}

data: {"type": "content_part_added"}

data: {"type": "delta", "text": "你"}

data: {"type": "delta", "text": "好"}

data: {"type": "delta", "text": "！"}

data: {"type": "text_done"}

data: {"type": "content_part_done"}

data: {"type": "output_item_done"}

data: {"type": "completed"}

data: [DONE]
```

## 💡 前端实现说明

### 流式显示原理

1. **created 事件**：创建一个空白的 AI 消息气泡
2. **delta 事件**：逐字累积文本并更新同一个气泡
3. **completed 事件**：标记消息完成

```javascript
// 关键代码片段
if (event.type === 'created') {
    hideTypingIndicator();
    addMessage('assistant', '', false);  // 创建空气泡
}
else if (event.type === 'delta' && event.text) {
    assistantMessage += event.text;  // 累积文本
    addMessage('assistant', assistantMessage, true);  // 更新气泡
}
```

### 消息气泡管理

- `addMessage(role, content, false)` - 创建新气泡
- `addMessage(role, content, true)` - 更新最后一个气泡
- 确保整个对话过程只有一个 AI 回复气泡

## 📝 使用示例

### Python 客户端

```python
import requests
import json

# POST 请求流式接收
response = requests.post(
    "http://127.0.0.1:8000/api/chat",
    json={"question": "什么是 FastAPI？", "session_id": "my_session"},
    stream=True
)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data_str = line_str[6:]  # 去掉 'data: ' 前缀
            if data_str != '[DONE]':
                event = json.loads(data_str)
                if event['type'] == 'delta':
                    print(event['text'], end='', flush=True)
```

### JavaScript Fetch API

```javascript
async function sendMessage(question) {
    const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, session_id: 'default' })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data !== '[DONE]') {
                    const event = JSON.parse(data);
                    if (event.type === 'delta') {
                        console.log(event.text);
                    }
                }
            }
        }
    }
}
```

## 🏗️ 项目结构

```
chat_response_demo/
├── main.py                 # FastAPI 应用主文件
├── static/
│   └── index.html         # 前端聊天界面
├── .env.example           # 环境变量示例
├── .env                   # 环境变量配置（需创建）
├── pyproject.toml         # 项目依赖配置
├── uv.lock               # uv 锁文件
└── README.md             # 项目文档
```

## 🔧 技术栈

- **后端**: FastAPI + Uvicorn + Pydantic
- **AI**: OpenAI API (支持自定义 base_url)
- **前端**: 原生 HTML + CSS + JavaScript
- **包管理**: uv (推荐) 或 pip
- **Python**: 3.10+

## 🚨 常见问题

### 1. 前端看不到 AI 回复

**解决方法**：强制刷新浏览器清除缓存
- Mac: `Cmd + Shift + R`
- Windows/Linux: `Ctrl + Shift + R`

### 2. 端口被占用

```bash
# 查找占用端口的进程
lsof -ti:8000

# 终止进程
lsof -ti:8000 | xargs kill -9
```

### 3. EventStream 为空

确保：
- 后端正确返回标准 JSON 格式（双引号）
- 前端使用 POST 方法和 JSON 请求体
- 浏览器支持 Fetch API 和流式读取

## 📚 开发建议

### 生产环境部署
1. ✅ 使用环境变量管理敏感信息
2. ✅ 使用 Redis 等持久化存储管理会话状态
3. ✅ 添加身份验证和授权（JWT）
4. ✅ 配置日志记录和监控
5. ✅ 使用 Nginx 反向代理和 SSL
6. ✅ 配置 CORS 限制具体域名
7. ✅ 实现请求限流和防滥用

### 扩展功能建议
- [ ] 用户身份验证系统
- [ ] 会话持久化（Redis/PostgreSQL）
- [ ] 消息历史记录存储
- [ ] 多模型切换支持
- [ ] 文件上传和向量搜索
- [ ] Markdown 渲染支持
- [ ] 代码高亮显示
- [ ] 多轮对话上下文管理
- [ ] 导出聊天记录功能

## License

MIT
