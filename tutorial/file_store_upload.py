from typing import Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field
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


def main():
    
    """
    https://llm.traderwtf.ai
    不支持 file store 功能 "/vector_stores"
    openai.APIStatusError: Error code: 405 - {'detail': 'Method Not Allowed'}

    Storage	Cost:
        Up to 1 GB (across all stores)	Free
        Beyond 1 GB	$0.10/GB/day

    """
    client = get_client()
    vector_store =client.vector_stores.create(
        name="DeTony FAQ",
        description="DeTony FAQ 文件存储",
    )
    print("Created vector store:", vector_store.id)
    client.vector_stores.files.upload_and_poll(
        vector_store_id=vector_store.id,
        file=open("./data/DeTony_FAQ.pdf", "rb"),
        attributes={
            "source": "DeTony_FAQ.pdf",
            "tags": ["faq", "support", "finance"],
            "category": "finance",
            "date": 1672531200,  # Unix timestamp
        },
    )

    results =client.vector_stores.search(
        vector_store_id=vector_store.id,
        query="What is DeTony?",
        max_num_results=3,
        filters={
            "type": "and",
            "filters": [
                {
                    "type": "eq",
                    "key": "category",
                    "value": "finance"
                },
                {
                    "type": "gte",
                    "key": "date",
                    "value": 1672531200 # Unix timestamp, 这个时间之后生效的
                }
            ]
        }
    )
    for idx, result in enumerate(results):
        print(f"Result {idx + 1}:")
        print("Content:", result.content)
        print("Metadata:", result.attributes)
        print("Score:", result.score)
        print("-" * 20)


if __name__ == "__main__":
    main()