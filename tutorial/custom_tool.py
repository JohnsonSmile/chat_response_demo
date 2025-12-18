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


def get_stock_price(symbol: str) -> dict:
    return {
        "symbol": "AAPL",
        "price": 150.25,
        "currency": "USD",
    }

# schema for get_stock_price request
class GetStockPriceRequest(BaseModel):
    symbol: str = Field(description="股票代码,例如: AAPL, GOOGL, TSLA")

    model_config = ConfigDict(extra="forbid")



# schema for get_stock_price response
class GetStockPriceResponse(BaseModel):
    symbol: str
    price: float
    currency: str

    model_config = ConfigDict(extra="forbid")


def get_tools():

    get_stock_price_schema = GetStockPriceRequest.model_json_schema()
    print("get_stock_price schema:", get_stock_price_schema)
    tools = [
        {
            "type": "function",
            "name": "get_stock_price",
            "description": "get stock price for a given stock symbol",
            "parameters": get_stock_price_schema,
            "strict": True,
        },
    ]
    return tools

def main():
    tools = get_tools()
    print("Registered tools:", tools)
    client = get_client()
    input = [
                {
                    "role": "user",
                    "content": "What is the stock price of AAPL?",
                }
    ]
    while True:
        response = client.responses.create(
            model="g4o",
            input=input,
            tools=tools
        )
        for response_output in response.output:
            response_type = response_output.type
            if response_type == "function_call":
                function_name = response_output.name
                function_args = response_output.arguments
                args = json.loads(function_args)
                if function_name == "get_stock_price":
                    symbol = args.get("symbol")
                    stock_price_info = get_stock_price(symbol)
                    print(f"response_output: {response_output}")
                    # 将 function call 添加到 input
                    function_call_dict = {
                        "type": "function_call",
                        "call_id": response_output.call_id,
                        "name": response_output.name,
                        "arguments": response_output.arguments,
                    }
                    input.append(function_call_dict)
                    
                    # 添加 function call 的输出
                    function_output_dict = {
                        "type": "function_call_output",
                        "call_id": response_output.call_id,
                        "output": json.dumps(stock_price_info),
                    }
                    input.append(function_output_dict)
            elif response_type == "message":
                print("Model response text:", response.output_text)
                return
            else:
                print("Unknown response:", response_output)
                return
            


if __name__ == "__main__":
    main()
