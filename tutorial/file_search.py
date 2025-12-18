from typing import Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
import json

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
    # 搜索工具可以定义他的filters
    tools = [
        {
            "type": "file_search",
            "vector_store_ids": [""],
            "max_num_results": 10,
            "filter": {
                "type": "and",
                "filters": [
                    {
                        "type": "eq",
                        "key": "category",
                        "value": "finance"
                    }
                ]
            }
        },
    ]
    return tools


def main():
    client = get_client()
    tools = get_tools()
    print("Tools:", json.dumps(tools, indent=2))
    response = client.responses.create(
        model="g4o",
        input=[
            {
                "role": "user",
                "content": "Who is 周凯?",
            }
        ],
        tools=tools,
        include=["file_search_call.results"],
    )
    print("Agent answer:", response.output_text)

    print("Annotations:")
    for output_item in response.output:
        if output_item.type == "file_search_call":
            print("File Search Results:")
            for i, result in enumerate(output_item.results):
                print(f"Result {i+1}:")
                print(f"- Filename: {result.filename}")
                print(f"- File ID: {result.file_id}")
                print(f"- Score: {result.score}")
                print(f"- Attributes: {result.attributes}")
                print(f"- Text snnipet: {result.text[:100]}..." if len(result.text) > 100 else f"- Text snnipet: {result.text}")  # 打印前100个字符
        elif output_item.type == "message":
            for content_item in output_item.content:
                if content_item.type == "output_text":
                    for annotation in content_item.annotations:
                        if annotation.type == "file_citation":
                            print(f"- Citation from file {annotation.filename}")
                

if __name__ == "__main__":
    main()