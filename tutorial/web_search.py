from typing import Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
from playwright.sync_api import sync_playwright

# 加载环境变量
load_dotenv()


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
    print("Client initialized")
    print( f"base_url: {_client.base_url}")
    print( f"api_key: {_client.api_key}")
    return _client

def get_tools():
    tools = [
        {
            "type": "web_search_preview",
            "user_location": {
                "type": "approximate",
                "country": "CN",
                "city": "Shenzhen",
                "region": "Shenzhen",
            }

        },
    ]
    return tools

def main():
    client = get_client()
    tools = get_tools()
    print("Tools:", tools)
    response = client.responses.create(
        model="g4o",
        instructions="使用网络搜索工具回答用户的问题。不要询问用户的具体位置，用户位置信息会在工具中提供。",
        input=[
            {
                "role": "user",
                "content": "今天的天气怎么样？",
            }
        ],
        tools=tools,
    )

    print("Response:", response.output_text)

if __name__ == "__main__":
    main()
