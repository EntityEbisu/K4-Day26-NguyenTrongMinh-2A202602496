"""Factory cho mọi lời gọi LLM của lab — trỏ OpenCode Go (OpenAI-compatible).

Quirk ĐÃ KIỂM CHỨNG của OpenCode Go (không được bỏ qua):
  - BẮT BUỘC header `x-opencode-session`  (thiếu -> HTTP 400 MissingSessionID)
  - PHẢI gửi User-Agent riêng             (UA mặc định SDK -> Cloudflare 403 error 1010)
  - Là reasoning model: max_tokens nhỏ -> content = null (finish_reason=length)
    => luôn budget >= 2048; coi content rỗng là LỖI, thử cấu hình kế tiếp
  - `n` phải <= 1

Ladder model: `step-5-preview-free` (chính) -> `deepseek-v4.1-flash` (dự phòng, effort thấp).
Model dự phòng được thử kèm `reasoning_effort` (mặc định "low") rồi thử lại KHÔNG kèm,
vì tên giá trị effort là đặc thù từng model và có thể bị từ chối.
"""
from __future__ import annotations

import os

from openai import OpenAI

DEFAULT_BASE_URL = "https://opencode.ai/zen/go/v1"
USER_AGENT = "day26-weather-lab/1.0"
DEFAULT_SESSION_ID = "day26-minh-001"


class LlmError(RuntimeError):
    """Lỗi cấu hình hoặc lỗi model — không bao giờ trả câu trả lời rỗng."""


def _is_set(value: str | None) -> bool:
    """True nếu biến có giá trị thật (không phải placeholder 'your_...')."""
    return bool(value) and not value.startswith("your_")


def build_client() -> OpenAI:
    """Tạo OpenAI client trỏ OpenCode Go, kèm header bắt buộc."""
    api_key = os.getenv("OPENCODE_API_KEY")
    if not _is_set(api_key):
        raise LlmError("Thiếu OPENCODE_API_KEY — điền vào .env (xem .env.example)")
    return OpenAI(
        base_url=os.getenv("OPENCODE_BASE_URL", DEFAULT_BASE_URL),
        api_key=api_key,
        default_headers={
            "x-opencode-session": os.getenv("OPENCODE_SESSION_ID", DEFAULT_SESSION_ID),
            "User-Agent": USER_AGENT,
        },
        timeout=60.0,
        max_retries=1,
    )


def model_ladder() -> list[str]:
    """Thứ tự model sẽ thử: chính trước, dự phòng sau (bỏ trùng lặp)."""
    primary = os.getenv("OPENCODE_MODEL", "step-5-preview-free")
    fallback = os.getenv("OPENCODE_FALLBACK_MODEL", "deepseek-v4.1-flash")
    if fallback and fallback != primary:
        return [primary, fallback]
    return [primary]


def fallback_effort() -> str:
    """Reasoning effort cho model dự phòng. Rỗng = không gửi tham số."""
    return os.getenv("OPENCODE_FALLBACK_EFFORT", "low").strip()


def _attempts() -> list[tuple[str, dict]]:
    """Danh sách (model, extra_kwargs) theo thứ tự thử.

    - Model chính: không set effort (giữ mặc định provider).
    - Model dự phòng: thử kèm reasoning_effort trước, rồi thử lại không kèm.
    """
    attempts: list[tuple[str, dict]] = []
    for index, model in enumerate(model_ladder()):
        if index == 0:
            attempts.append((model, {}))
        else:
            effort = fallback_effort()
            if effort:
                attempts.append((model, {"reasoning_effort": effort}))
            attempts.append((model, {}))
    return attempts


def chat_with_tools(client: OpenAI, messages: list, tools: list, *, max_tokens: int = 2048):
    """Gọi chat.completions với tool-calling, tự thử từng cấu hình trong ladder.

    Trả về `message` của assistant (có thể chứa `tool_calls`).
    Ném LlmError nếu mọi cấu hình đều thất bại hoặc trả nội dung rỗng.
    """
    last_err: Exception | None = None
    for model, extra in _attempts():
        label = model + (f" (effort={extra['reasoning_effort']})" if extra else "")
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                max_tokens=max_tokens,
                **extra,
            )
            msg = resp.choices[0].message
            if not msg.tool_calls and not (msg.content or "").strip():
                raise LlmError(f"{model}: content rỗng (reasoning ăn hết budget?)")
            print(f"✅ model đã trả lời: {getattr(resp, 'model', model)}{' [effort=' + extra['reasoning_effort'] + ']' if extra else ''}")
            return msg
        except Exception as e:  # noqa: BLE001 - ladder cần bắt mọi lỗi provider
            last_err = e
            print(f"⚠️  {label} lỗi: {e} — thử cấu hình kế tiếp")
    raise LlmError(f"Tất cả cấu hình model đều lỗi: {last_err}")
