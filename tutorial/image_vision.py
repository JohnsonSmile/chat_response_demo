from typing import Optional
import os
from dotenv import load_dotenv
from openai import OpenAI

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
    client = get_client()
    response = client.responses.create(
        model="g4o",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "请描述一下这张图片的内容。",
                    },
                    {
                        "type": "input_image",
                        "image_url": "https://images.pexels.com/photos/1181244/pexels-photo-1181244.jpeg"
                    }
                ],
            }
        ]
    )
    print("Response:", response.output_text)

if __name__ == "__main__":
    main()