"""Chạy 1 lượt hỏi–đáp với agent để lấy bằng chứng console (không cần `adk web`).

Cần MCP server đang chạy ở :8085. Chạy:
    cd 04-lab/mcp-client
    ./.venv/Scripts/python.exe smoke_agent.py
"""
import asyncio

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from weather_agent import root_agent

PROMPT = "Thời tiết Hà Nội hôm nay thế nào?"


async def main() -> None:
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="weather_agent", user_id="minh", session_id="s1"
    )
    runner = Runner(
        app_name="weather_agent", agent=root_agent, session_service=session_service
    )

    message = types.Content(role="user", parts=[types.Part(text=PROMPT)])
    print(f"User: {PROMPT}\n")

    async for event in runner.run_async(
        user_id="minh", session_id="s1", new_message=message
    ):
        # In các lời gọi tool để thấy agent thật sự dùng MCP
        for fc in (event.get_function_calls() or []):
            print(f"  [agent gọi tool] {fc.name}({fc.args})")
        if event.is_final_response() and event.content:
            text = "".join(p.text for p in event.content.parts if p.text)
            print("Trả lời:", text)


if __name__ == "__main__":
    asyncio.run(main())
