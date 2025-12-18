from typing import Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ConfigDict


class WebSearchAnswer(BaseModel):
    answer: str = Field(..., description="The answer to the user's question.")

    model_config = ConfigDict(
        extra="forbid",
    )

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
    # print("Client initialized")
    # print( f"base_url: {_client.base_url}")
    # print( f"api_key: {_client.api_key}")
    return _client


def get_tools():
    tools = [
        {
            "type": "web_search",
        }
    ]
    return tools


def chat_loop():
    response_id = None
    # history = []
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("GoodBye.")
            break
        # history.append({"role": "user", "content": user_input})
        client = get_client()
        tools = get_tools()
        response = client.responses.create(
            model="g4o",
            input=[
                {
                    "role": "user",
                    "content": user_input,
                }
            ],
            tools=tools,
            previous_response_id=response_id,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "web_search_answer",
                    "schema": WebSearchAnswer.model_json_schema(),
                    # "schema": {
                    #     "type": "object",
                    #     "properties": {
                    #         "answer": {
                    #             "type": "string",
                    #             "description": "The answer to the user's question.",
                    #         },
                    #     },
                    #     "required": ["answer"],
                    #     "additionalProperties": False,
                    # },
                }
            }
        )
        # history.append({"role": "assistant", "content": response.output_text})
        response_id = response.id
        print("Bot:", response.output_text)


if __name__ == "__main__":
    chat_loop()
