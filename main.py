from openai import OpenAI
from fastapi import FastAPI, APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from typing import Optional, AsyncGenerator
import uvicorn
import os
from contextlib import asynccontextmanager


# 配置管理
class Config:
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://llm.traderwtf.ai")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))


# 全局 OpenAI 客户端（单例模式）
_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """获取 OpenAI 客户端实例（依赖注入）"""
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=Config.OPENAI_BASE_URL,
            api_key=Config.OPENAI_API_KEY,
        )
    return _client


def file_upload(client: OpenAI, file_path: str) -> str:
    """
    上传文件到 vector store
    
    Args:
        client: OpenAI 客户端
        file_path: 要上传的文件路径
        
    Returns:
        vector_store_id: 创建的 vector store ID
    """
    # 创建 vector store
    vector_store = client.vector_stores.create(
        name="Support QA",
    )
    
    # 上传文档
    with open(file_path, "rb") as f:
        client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store.id,
            file=f
        )
    
    # TODO: 保存映射关系到本地进行管理
    return vector_store.id


# 会话状态管理（简单实现，生产环境建议使用 Redis 等）
session_store: dict[str, str] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print(f"应用启动 - 监听 http://{Config.HOST}:{Config.PORT}")
    yield
    # 关闭时清理
    print("应用关闭")


app = FastAPI(
    title="Chat Response Demo",
    debug=True,
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api")


async def generate_chat_stream(
    client: OpenAI,
    question: str,
    session_id: str,
    model: str = "g4o"
) -> AsyncGenerator[str, None]:
    """
    生成聊天流式响应
    
    Args:
        client: OpenAI 客户端
        question: 用户问题
        session_id: 会话 ID
        model: 使用的模型
        
    Yields:
        str: 流式响应的文本片段
    """
    # 获取上一次的 response_id
    previous_response_id = session_store.get(session_id)
    
    try:
        response = client.responses.create(
            model=model,
            tool_choice="auto",
            tools=[{"type": "web_search_preview"}],
            input=[
                {"role": "user", "content": question}
            ],
            previous_response_id=previous_response_id,
            stream=True,
        )
        
        for event in response:
            if event.type == "response.created":
                # 保存新的 response_id
                session_store[session_id] = event.response.id
                yield f'data: {{"type": "created", "id": "{event.response.id}"}}\n\n'
                
            elif event.type == "response.in_progress":
                yield f'data: {{"type": "in_progress"}}\n\n'
                
            elif event.type == "response.output_item.added":
                yield f'data: {{"type": "output_item_added"}}\n\n'
                
            elif event.type == "response.content_part.added":
                yield f'data: {{"type": "content_part_added"}}\n\n'
                
            elif event.type == "response.output_text.delta":
                # 发送文本增量，需要转义特殊字符
                import json
                text = json.dumps(event.delta)
                yield f'data: {{"type": "delta", "text": {text}}}\n\n'
                
            elif event.type == "response.output_text.done":
                yield f'data: {{"type": "text_done"}}\n\n'
                
            elif event.type == "response.content_part.done":
                yield f'data: {{"type": "content_part_done"}}\n\n'
                
            elif event.type == "response.output_item.done":
                yield f'data: {{"type": "output_item_done"}}\n\n'
                
            elif event.type == "response.completed":
                yield f'data: {{"type": "completed"}}\n\n'
                
            else:
                yield f'data: {{"type": "unknown", "event": "{str(event)}"}}\n\n'
                
    except Exception as e:
        yield f"data: {{'type': 'error', 'message': '{str(e)}'}}\n\n"
    finally:
        yield "data: [DONE]\n\n"


from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"
    model: str = "g4o"

@router.post("/chat")
async def handle_chat_stream(
    request: ChatRequest,
    client: OpenAI = Depends(get_client)
) -> StreamingResponse:
    """
    处理聊天流式请求
    
    Args:
        request: 聊天请求（包含 question, session_id, model）
        client: OpenAI 客户端（依赖注入）
        
    Returns:
        StreamingResponse: Server-Sent Events (SSE) 格式的流式响应
    """
    return StreamingResponse(
        generate_chat_stream(client, request.question, request.session_id, request.model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/upload")
async def handle_file_upload(
    file_path: str = Query(..., description="要上传的文件路径"),
    client: OpenAI = Depends(get_client)
) -> dict:
    """
    上传文件到 vector store
    
    Args:
        file_path: 要上传的文件路径
        client: OpenAI 客户端（依赖注入）
        
    Returns:
        dict: 包含 vector_store_id 的响应
    """
    try:
        vector_store_id = file_upload(client, file_path)
        return {
            "success": True,
            "vector_store_id": vector_store_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/session/{session_id}")
async def clear_session(session_id: str) -> dict:
    """
    清除会话状态
    
    Args:
        session_id: 要清除的会话 ID
        
    Returns:
        dict: 操作结果
    """
    if session_id in session_store:
        del session_store[session_id]
        return {"success": True, "message": f"会话 {session_id} 已清除"}
    return {"success": False, "message": f"会话 {session_id} 不存在"}


# 注册路由
app.include_router(router)


@app.get("/")
async def root():
    """根路径 - 重定向到前端页面"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")


# 挂载静态文件目录（必须在所有路由之后）
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True  # 开发模式下启用热重载
    )
