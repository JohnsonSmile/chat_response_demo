from typing import Optional
import os
import base64
from dotenv import load_dotenv
from openai import OpenAI
from playwright.sync_api import sync_playwright
import time

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
            "type": "computer_use_preview",
            "display_width": 1024,
            "display_height": 768,
            "environment": "browser",
        },
    ]
    return tools


def get_screenshot(page):
    return page.screenshot()

def show_image(bs64_image):
    from PIL import Image
    from io import BytesIO
    image_data = base64.b64decode(bs64_image)
    image = Image.open(BytesIO(image_data))
    image.show()


def handle_model_action(browser, page, action):
    action_type = action.type

    try:
        print(f"Handling action: {action_type} with parameters: {action.parameters}")
        all_pages = browser.contexts[0].pages
        if len(all_pages) > 1 and all_pages[-1] != page:
            # 点击之后如果有新的页面，切换到新的页面
            print(f"Switching to new page: {all_pages[-1].url}")
            page = all_pages[-1]
        
        match action_type:
            case "click":
                x, y = action.x, action.y
                button = action.button
                print(f"Action: click at ({x}, {y}) with button '{button}'")
                # Not handling things like middle click, etc.
                if button != "left" and button != "right":
                    button = "left"
                page.mouse.click(x, y, button=button)

            case "scroll":
                x, y = action.x, action.y
                scroll_x, scroll_y = action.scroll_x, action.scroll_y
                print(f"Action: scroll at ({x}, {y}) with offsets (scroll_x={scroll_x}, scroll_y={scroll_y})")
                page.mouse.move(x, y)
                page.evaluate(f"window.scrollBy({scroll_x}, {scroll_y})")

            case "keypress":
                keys = action.keys
                for k in keys:
                    print(f"Action: keypress '{k}'")
                    # A simple mapping for common keys; expand as needed.
                    if k.lower() == "enter":
                        page.keyboard.press("Enter")
                    elif k.lower() == "space":
                        page.keyboard.press(" ")
                    else:
                        page.keyboard.press(k)
            
            case "type":
                text = action.text
                print(f"Action: type text: {text}")
                page.keyboard.type(text)
            
            case "wait":
                print(f"Action: wait")
                time.sleep(2)

            case "screenshot":
                # Nothing to do as screenshot is taken at each turn
                print(f"Action: screenshot")

            # Handle other actions here
            case _:
                print(f"Unrecognized action: {action}")
        return page
        
    except Exception as e:
        print(f"Error printing action details: {e}")

def computer_use_loop(browser, page, response):
    while True:
        computer_calls = [
            call for call in response.tool_calls
            if call.tool.type == "computer_call"
        ]
        if not computer_calls:
            print("No more computer calls.")
            for item in response.output:
                print(item)
            break 

    # 继续调用模型，传入截图
    call_id = computer_calls[0].call_id
    action = computer_calls[0].action

    # 执行模型指令
    page = handle_model_action(browser, page, action)
    time.sleep(2)  # 等待页面加载

    # 获取截图并传回模型
    screen_shot_bytes = get_screenshot(page)
    screen_shot_bs64 = base64.b64encode(screen_shot_bytes).decode('utf-8')
    show_image(screen_shot_bs64)

    client = get_client()
    tools = get_tools()
    response = client.responses.create(
        model="computer-use-preview",
        previous_response_id=response.id,
        tools=tools,
        input=[
            {
                "call_id": call_id,
                "type": "computer_call_output",
                "output": {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{screen_shot_bs64}"
                }
            }
        ],
        truncation="auto",
    )
    return response

def main():

    # playwright 环境
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            chromium_sandbox=True,
            env={},
            args=[
                "--disable-extensions",
                "--disable-file-system",
            ],
        )
        page = browser.new_page()
        page.set_viewport_size({"width": 1024, "height": 768})

        # 访问一个网页以确保浏览器正常工作
        page.goto("https://bing.com", wait_until="domcontentloaded")
        
        client = get_client()
        tools = get_tools()
        

        # TODO: 需要部署 computer-use-preview 模型
        response = client.responses.create(
            model="computer-use-preview",
            input=[
                {"role": "user", "content": "Open bing and search for image of Emma Watson. Then click on the first image that you found."}
            ],
            tools=tools,
            reasoning={
                "generate_summary": "concise",
            },
            truncation="auto",
        )
        print(response.output)

        final_response = computer_use_loop(browser, page, response)
        print("Final response output:")
        print(final_response.output)
        browser.close()

if __name__ == '__main__':
    main()
