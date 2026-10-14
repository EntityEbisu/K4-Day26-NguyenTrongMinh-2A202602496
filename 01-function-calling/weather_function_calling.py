"""Minh hoạ FUNCTION CALLING thuần — LLM gọi qua OpenCode Go (OpenAI-compatible).

Giống bản gốc (google-genai/Gemini) về Ý TƯỞNG: app TỰ KHAI schema tool,
model chỉ QUYẾT ĐỊNH gọi tool nào, app TỰ THỰC THI hàm, rồi trả kết quả
lại cho model tổng hợp. Chỉ khác: provider là OpenCode Go
(model `step-5-preview-free`, dự phòng `deepseek-v4.1-flash`).

Cách chạy:
    cd 01-function-calling
    ../.venv/Scripts/python.exe weather_function_calling.py
"""

from __future__ import annotations

import json

from dotenv import load_dotenv

from llm_client import build_client, chat_with_tools

load_dotenv()

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thời tiết thân thiện, trả lời bằng tiếng Việt tự nhiên. "
    "Dùng emoji phù hợp (🌧️ 🌤️ 💨 💧). "
    "Tóm tắt ngắn gọn, dễ hiểu, và đưa ra lời khuyên thực tế "
    "(ví dụ: mang ô, mặc áo mỏng, ...)."
)

# 1. App tự định nghĩa schema của tool (viết TAY — nhược điểm của Function Calling thuần)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Lấy thời tiết hiện tại của một thành phố",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Tên thành phố"}
                },
                "required": ["city"],
            },
        },
    }
]

# Dữ liệu mock — trong thực tế sẽ gọi API thời tiết thật
_MOCK_DATA = {
    "Hà Nội": {
        "nhiệt_độ": "29°C",
        "thời_tiết": "trời mưa nhẹ",
        "độ_ẩm": "82%",
        "gió": {"hướng": "Đông Nam", "tốc_độ": "12 km/h"},
    },
    "Hồ Chí Minh": {
        "nhiệt_độ": "33°C",
        "thời_tiết": "mưa rào",
        "độ_ẩm": "75%",
        "gió": {"hướng": "Tây Nam", "tốc_độ": "15 km/h"},
    },
    "Đà Nẵng": {
        "nhiệt_độ": "30°C",
        "thời_tiết": "nhiều mây",
        "độ_ẩm": "78%",
        "gió": {"hướng": "Đông", "tốc_độ": "10 km/h"},
    },
}


# 2. App tự thực thi tool (model KHÔNG chạy hàm này)
def get_weather(city: str) -> str:
    """Trả về thời tiết (mock) của *city*. Dùng làm tool cho model."""
    default = {"nhiệt_độ": "28°C", "thời_tiết": "không có dữ liệu chi tiết"}
    return json.dumps(
        {"city": city, **_MOCK_DATA.get(city, default)}, ensure_ascii=False
    )


def run(prompt: str) -> str:
    """Gửi *prompt* tới model, tự động xử lý function calling và trả về câu trả lời cuối."""
    client = build_client()
    messages: list = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": prompt},
    ]

    # 3+4. Vòng lặp: model quyết định gọi tool -> APP tự thực thi -> trả kết quả lại
    while True:
        msg = chat_with_tools(client, messages, TOOLS, max_tokens=2048)
        # Thêm phản hồi của model (kể cả tool_calls) vào lịch sử hội thoại
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            # 5. Model tổng hợp câu trả lời cuối
            return msg.content

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            print(f"  [model yêu cầu] {tc.function.name}({args})")
            result = get_weather(**args)  # <-- app chạy, không phải model
            print(f"  [app thực thi]  -> {result}")
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": result}
            )


if __name__ == "__main__":
    question = "Thời tiết Hà Nội và Đà Nẵng hôm nay thế nào?"
    print(f"User: {question}\n")
    print("Trả lời:", run(question))
