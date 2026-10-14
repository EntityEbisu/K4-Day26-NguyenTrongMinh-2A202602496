# Báo cáo Day 26 — Phân biệt MCP và Function Calling

- **Sinh viên:** Nguyễn Trọng Minh — MSSV 2A202602496 (K4)
- **Repo:** https://github.com/EntityEbisu/K4-Day26-NguyenTrongMinh-2A202602496
- **Ngày chạy:** 2026-10-14 (giờ Việt Nam, UTC+07:00)
- **Môi trường:** Windows 11, Git Bash (MSYS), Python 3.14.7, `uv 0.12.13`

---

## 1. Mục tiêu

Chạy được trọn vẹn 4 phần của lab (Function Calling → MCP basics → MCP production → ADK agent + MCP server thật),
chứng minh bằng console output thật, và làm rõ mối quan hệ: **MCP dùng Function Calling ở tầng dưới, hai khái niệm bổ sung cho nhau**.

---

## 2. Các API đã dùng

| API | Dùng ở đâu | Ghi chú |
|---|---|---|
| **OpenCode Go** (`https://opencode.ai/zen/go/v1`, OpenAI-compatible) | Lab 01 và Lab 04 (LLM) | Model `step-5-preview-free` — **chạy được, không phải fallback** |
| **WeatherAPI.com** | Lab 04 (MCP server lấy dữ liệu thật) | Dùng **key thật**, dữ liệu thật |
| Gemini / `GOOGLE_API_KEY` | **Không dùng** | Lab 01 và 04 đã chuyển sang OpenCode Go |

**Quirk của OpenCode Go đã xử lý trong code** (nếu bỏ qua sẽ hỏng lặng lẽ):

- Header `x-opencode-session` là **bắt buộc** — thiếu sẽ trả `HTTP 400 MissingSessionID`.
- Phải gửi `User-Agent` riêng — UA mặc định của SDK bị Cloudflare chặn `403 error code: 1010`.
- Đây là **reasoning model**: `max_tokens` nhỏ ⇒ `content = null` (`finish_reason=length`).
  Code đặt budget ≥ 2048 và **coi `content` rỗng là lỗi**, không nhận `None` làm câu trả lời.
- Có ladder model: `step-5-preview-free` → `deepseek-v4.1-flash` (reasoning effort thấp).

---

## 3. Phần 01 — Function Calling thuần

**Cách chạy:** `cd 01-function-calling && ../.venv/Scripts/python.exe weather_function_calling.py`

**Thay đổi so với bản gốc:** thay `google-genai` (Gemini) bằng **OpenAI SDK** trỏ OpenCode Go.
Ý tưởng function calling **không đổi**: app tự khai schema tool → model chỉ quyết định gọi tool nào → **app tự thực thi hàm** → trả kết quả lại cho model tổng hợp.
Thêm `llm_client.py` (factory dùng chung, đã mã hoá các quirk ở mục 2) và `test_llm_client.py`.

**Console output (nguyên văn):**

```
User: Thời tiết Hà Nội và Đà Nẵng hôm nay thế nào?

✅ model đã trả lời: step-5-preview-free
  [model yêu cầu] get_weather({'city': 'Hà Nội'})
  [app thực thi]  -> {"city": "Hà Nội", "nhiệt_độ": "29°C", "thời_tiết": "trời mưa nhẹ", "độ_ẩm": "82%", "gió": {"hướng": "Đông Nam", "tốc_độ": "12 km/h"}}
  [model yêu cầu] get_weather({'city': 'Đà Nẵng'})
  [app thực thi]  -> {"city": "Đà Nẵng", "nhiệt_độ": "30°C", "thời_tiết": "nhiều mây", "độ_ẩm": "78%", "gió": {"hướng": "Đông", "tốc_độ": "10 km/h"}}
✅ model đã trả lời: step-5-preview-free
Trả lời: Đây là thời tiết hôm nay ở hai thành phố nha:

**🌧️ Hà Nội:** 29°C – trời mưa nhẹ, độ ẩm 82%, gió nhẹ Đông Nam ~12km/h.

**🌤️ Đà Nẵng:** 30°C – nhiều mây, độ ẩm 78%, gió Đông ~10km/h.

**💡 Lời khuyên:**
- Ở **Hà Nội**: Hãy mang theo ô/áo mưa khi ra đường, vì trời có mưa nhẹ. Độ ẩm cao nên có thể hơi bí, nên mặc áo thoáng khí cho dễ chịu.
- Ở **Đà Nẵng**: Trời chỉ nhiều mây nên rất mát mẻ phù hợp để đi chơi hoặc dạo biển. Có thể ra ngoài không cần ô, nhưng để phòng ngờ thì vẫn mang theo áo khoác mỏng khi gió về chiều.
```

**Nhận xét:** model trả về **2 yêu cầu gọi tool** `get_weather({'city': 'Hà Nội'})` và `get_weather({'city': 'Đà Nẵng'})`.
Bản thân model **không chạy** hàm — dòng `[app thực thi]` do app in ra. Đúng đặc trưng của Function Calling thuần.

---

## 4. Phần 02 — MCP basics (stdio)

**Cách chạy:** `cd 02-mcp-basics && ../.venv/Scripts/python.exe weather_client.py`
**Không cần API key.**

```
Tools server cung cấp:
  - get_weather: Lấy thời tiết hiện tại của một thành phố.

call_tool get_weather(city='Hanoi'):
  -> Hanoi: 29°C, trời mưa

call_tool get_weather(city='Danang'):
  -> Danang: 30°C, nhiều mây

call_tool get_weather(city='Haiphong'):
  -> Haiphong: 33°C, mưa rào
```

**Nhận xét:** client **không hard-code tool** — nó hỏi server bằng `list_tools()` tại runtime.
Server (`weather_server.py`, MCP SDK v2 `MCPServer`) tự công bố tool và **tự thực thi** `get_weather`.
Khác biệt cốt lõi so với phần 01: nơi thực thi tool đã tách khỏi app.

---

## 5. Phần 03 — MCP trong Production

### 5a. Authentication (Streamable HTTP + Bearer token)

**Cách chạy:** `python auth_server.py` (terminal 1) → `python auth_client.py` (terminal 2).

```
Tools (có auth):
  - get_weather: Lấy thời tiết hiện tại của một thành phố.

Kết quả: Hanoi: 29°C, trời mưa

=== Sai token (mong đợi 401/403) ===
      |     raw = await self._dispatcher.send_raw_request(method, data.get("params"), opts)
      |           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      |   File "D:\VinUni\day26\K4-Day26-NguyenTrongMinh-2A202602496\.venv\Lib\site-packages\mcp\shared\jsonrpc_dispatcher.py", line 461, in send_raw_request
      |     raise MCPError(code=outcome.code, message=outcome.message, data=outcome.data)
      | mcp.shared.exceptions.MCPError: Server returned an error response
      +------------------------------------

=== HTTP status trực tiếp (bằng chứng auth ở tầng transport) ===
không token : 401
token sai   : 401
token đúng  : 200
```

**Nhận xét:** đúng như thiết kế — **không token → 401**, **token sai → 401**, **token đúng → 200**.
Logic tool hoàn toàn không biết gì về auth; SDK xử lý ở tầng transport.

### 5b. Tool Registry & Discovery

**Cách chạy:** `python registry_client.py`

```
=== Tool Registry ===

  get_weather v1.0.0
    Lấy thời tiết hiện tại của một thành phố
    tags: ['weather', 'current', 'vietnam']  →  server: weather
  get_weather_v2 v2.0.0
    Lấy thời tiết chi tiết — JSON, hỗ trợ forecast và đơn vị đo
    tags: ['weather', 'forecast', 'detailed', 'vietnam']  →  server: weather-v2
  send_email v1.0.0
    Gửi email tới một hoặc nhiều người nhận
    tags: ['email', 'notification', 'communication']  →  server: email-service
  query_db v1.2.0
    Chạy truy vấn SQL trên database nội bộ
    tags: ['database', 'sql', 'query', 'analytics']  →  server: db-gateway

--- Agent cần tool có tag "weather" ---
Tìm thấy 2 tool(s):
  • get_weather v1.0.0 (server: weather)
  • get_weather_v2 v2.0.0 (server: weather-v2)

Best match: get_weather_v2 v2.0.0
Kết nối tới server [weather-v2]...
Kết quả: {"api_version": "2.0", "city": "Hanoi", "temp": 29, "units": "celsius", "condition": "trời mưa", "humidity": 82, "wind_speed_kmh": 12, "timestamp": "2026-10-14T16:40:43.652502+00:00"}

--- Agent tìm tool có keyword "forecast" ---
  • get_weather_v2: Lấy thời tiết chi tiết — JSON, hỗ trợ forecast và đơn vị đo
```

**Nhận xét:** agent **không hard-code** tool. Nó tra registry theo tag `weather`, nhận 2 ứng viên,
rồi `best_match()` chọn **`get_weather_v2` v2.0.0** (version cao nhất, không deprecated) và tự kết nối đúng server.

### 5c. Versioning & Backward Compatibility

**Cách chạy:** `python versioned_client.py`

```
Server: weather-v2 v2.0.0
Deprecated tools: ['get_weather']
Migration: Chuyển từ get_weather sang get_weather_v2. Tham số 'city' giữ nguyên, thêm include_forecast và units.

Tools:
  - get_weather: [v1] Lấy thời tiết hiện tại — trả chuỗi đơn giản. Deprecated, dùng get_weather_v2.
  - get_weather_v2: [v2] Lấy thời tiết chi tiết — JSON, hỗ trợ forecast và đơn vị đo.

Args:
    city: Tên thành phố (ví dụ: Hanoi, Danang)
    include_forecast: Có trả thêm dự báo 2 ngày tới không (mặc định: False)
    units: Đơn vị nhiệt độ — "celsius" hoặc "fahrenheit" (mặc định: celsius)


[v1] get_weather('Hanoi'):
  Hanoi: 29°C, trời mưa

[v2] get_weather_v2('Hanoi', forecast=True):
  {
  "api_version": "2.0",
  "city": "Hanoi",
  "temp": 29,
  "units": "celsius",
  "condition": "trời mưa",
  "humidity": 82,
  "wind_speed_kmh": 12,
  "timestamp": "2026-10-14T16:40:46.254665+00:00",
  "forecast": [
    {
      "day": "tomorrow",
      "temp": 27,
      "condition": "mưa nhẹ"
    },
    {
      "day": "day_after",
      "temp": 31,
      "condition": "nắng"
    }
  ]
}
```

**Nhận xét:** tool v1 (`get_weather`) **vẫn hoạt động** dù đã deprecated; tool v2 thêm `include_forecast`/`units`
với giá trị mặc định nên client cũ không bị vỡ; resource `server://info` công bố version + hướng migration.

### 5d. Kiểm thử tự động (TDD)

Test cho `ToolRegistry` (chạy được **offline**, không cần API key):

```
cd 03-production && ../.venv/Scripts/python.exe -m pytest test_registry.py -v
```

- **RED** (cố tình đổi kỳ vọng thành `get_weather_BOGUS`): `2 failed`
- **GREEN**: `2 passed`

Đã kiểm chứng test thực sự "cắn" (không phải test rỗng). Tương tự với `01-function-calling/test_llm_client.py`: **5 passed**.

---

## 6. Phần 04 — ADK agent + MCP server thật (WeatherAPI)

**Kiến trúc đã chạy thật:**

```
ADK Agent (LiteLlm → OpenCode Go)  ──Streamable HTTP──▶  MCP Server (:8085/mcp)  ──REST──▶  WeatherAPI.com
```

**Thay đổi so với bản gốc:** model ADK đổi từ `gemini-2.5-flash` sang **`LiteLlm(model="openai/step-5-preview-free")`**
trỏ OpenCode Go (kèm header `x-opencode-session` + `max_tokens=2048`).

### 6a. MCP server + 3 tool (dữ liệu WeatherAPI thật)

Server chạy ở `http://localhost:8085/mcp`. Gọi trực tiếp 3 tool qua MCP client:

```
Tools server công bố: ['get_current_weather', 'get_forecast', 'health_check']
health_check -> ✅ Weather MCP Server is running! Ready to provide weather data for Australian cities and worldwide.
get_current_weather(Hanoi) -> 
Current Weather for Hanoi, , Vietnam:

Temperature: 26.5°C (79.7°F)
Feels like: 28.3°C (82.9°F)
Condition: Smoky haze
Humidity: 76%
Wind: 16.2 km/h (10.1 mph) SSE
Pressure: 1015.0 mb
UV Index: 0.0
Visibility: 4.0 km

Last updated: 2026-10-14 23:30

get_forecast(Hanoi, 2) -> Weather Forecast for Hanoi, , Vietnam:
---

2026-10-14:
High: 34.3°C (93.8°F)
Low: 24.9°C (76.8°F)
Condition: Smoky haze
Chance of Rain: 5%
Max Wind: 18.0 km/h
UV Index: 7.6

---

2026-10-15:
High: 33.8°C (92.9°F)
Low: 24.6°C (76.2°F)
Condition: Smoky haze
Chance of Rain: 7%
Max Wind: 20.9 km/h
UV Index: 7.4
```

**Nhận xét:** đây là **dữ liệu thật** từ WeatherAPI (Hà Nội 26.5°C, độ ẩm 76%, tầm nhìn 4 km), không phải mock.

### 6b. Agent end-to-end (LLM + MCP + WeatherAPI)

Chạy headless để lấy bằng chứng (không cần browser): `./.venv/Scripts/python.exe smoke_agent.py`

```
D:\VinUni\day26\K4-Day26-NguyenTrongMinh-2A202602496\04-lab\mcp-client\.venv\Lib\site-packages\google\adk\features\_feature_decorator.py:72: UserWarning: [EXPERIMENTAL] feature FeatureName.PLUGGABLE_AUTH is enabled.
  check_feature_enabled()
INFO:weather_agent.agent:🌐 Initializing weather agent with remote MCP server
INFO:weather_agent.agent:📡 MCP Server: http://localhost:8085/mcp
INFO:weather_agent.agent:🤖 Model: openai/step-5-preview-free via https://opencode.ai/zen/go/v1
INFO:weather_agent.agent:🔌 Connecting to MCP server...
INFO:weather_agent.agent:✅ MCP toolset created successfully
INFO:weather_agent.agent:✅ Weather agent initialized with remote MCP tools:
INFO:weather_agent.agent:   - get_current_weather(city)
INFO:weather_agent.agent:   - get_forecast(city, days)
INFO:weather_agent.agent:   - health_check()
INFO:weather_agent.agent:🎉 Remote MCP connection successful!
WARNING:google_adk.google.adk.tools.mcp_tool.mcp_session_manager:Failed to configure mTLS using AsyncAuthorizedSession: Your default credentials were not found. To set up Application Default Credentials, see https://cloud.google.com/docs/authentication/external/set-up-adc for more information.
D:\VinUni\day26\K4-Day26-NguyenTrongMinh-2A202602496\04-lab\mcp-client\.venv\Lib\site-packages\google\adk\tools\mcp_tool\mcp_toolset.py:304: UserWarning: [EXPERIMENTAL] feature FeatureName._MCP_GRACEFUL_ERROR_HANDLING is enabled.
  session = await self._mcp_session_manager.create_session(
INFO:httpx:HTTP Request: POST http://localhost:8085/mcp "HTTP/1.1 200 OK"
INFO:mcp.client.streamable_http:Received session ID: 61d2499b301d45e2b66a7016d2fae219
INFO:mcp.client.streamable_http:Negotiated protocol version: 2025-11-25
INFO:httpx:HTTP Request: GET http://localhost:8085/mcp "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST http://localhost:8085/mcp "HTTP/1.1 202 Accepted"
INFO:httpx:HTTP Request: POST http://localhost:8085/mcp "HTTP/1.1 200 OK"
D:\VinUni\day26\K4-Day26-NguyenTrongMinh-2A202602496\04-lab\mcp-client\.venv\Lib\site-packages\google\adk\features\_feature_decorator.py:72: UserWarning: [EXPERIMENTAL] feature FeatureName.BASE_AUTHENTICATED_TOOL is enabled.
  check_feature_enabled()
D:\VinUni\day26\K4-Day26-NguyenTrongMinh-2A202602496\04-lab\mcp-client\.venv\Lib\site-packages\google\adk\models\llm_request.py:256: UserWarning: [EXPERIMENTAL] feature FeatureName.JSON_SCHEMA_FOR_FUNC_DECL is enabled.
  declaration = tool._get_declaration()
User: Thời tiết Hà Nội hôm nay thế nào?

23:46:55 - LiteLLM:INFO: utils.py:4516 - 
LiteLLM completion() model= step-5-preview-free; provider = openai
INFO:LiteLLM:
LiteLLM completion() model= step-5-preview-free; provider = openai
  [agent gọi tool] get_current_weather({'city': 'Hanoi'})
23:47:03 - LiteLLM:INFO: utils.py:4516 - 
LiteLLM completion() model= step-5-preview-free; provider = openai
INFO:LiteLLM:
LiteLLM completion() model= step-5-preview-free; provider = openai
Trả lời: Hà Nội hiện đang có mưa rào nhẹ, nhiệt độ khoảng 26,5°C (cảm giác như 28,3°C), độ ẩm khá cao 76% có gió nhẹ 16 km/h. Lưu ý tầm nhìn chỉ còn 4 km do sương mù khói, bạn ra đường nhớ đeo khẩu trang nhé!
```

**Nhận xét:** agent **tự gọi tool MCP** `get_current_weather({'city': 'Hanoi'})`, nhận kết quả thật,
rồi tổng hợp câu trả lời tiếng Việt. Đây chính là minh chứng cho luận điểm của lab:
**MCP (giao thức) + Function Calling (model quyết định gọi tool) hoạt động cùng nhau.**

### 6c. Kiểm tra cấu hình

```
INFO:weather_agent.agent:🌐 Initializing weather agent with remote MCP server
INFO:weather_agent.agent:📡 MCP Server: http://localhost:8085/mcp
INFO:weather_agent.agent:🤖 Model: openai/step-5-preview-free via https://opencode.ai/zen/go/v1
INFO:weather_agent.agent:🔌 Connecting to MCP server...
INFO:weather_agent.agent:✅ MCP toolset created successfully
INFO:weather_agent.agent:✅ Weather agent initialized with remote MCP tools:
INFO:weather_agent.agent:   - get_current_weather(city)
INFO:weather_agent.agent:   - get_forecast(city, days)
INFO:weather_agent.agent:   - health_check()
INFO:weather_agent.agent:🎉 Remote MCP connection successful!
============================================================
Weather Agent Setup Verification
============================================================

🔍 Checking environment configuration...
✅ OPENCODE_API_KEY đã được cấu hình

🔍 Checking dependencies...
✅ Google ADK
✅ LiteLLM (OpenCode Go provider)
✅ openai
✅ MCP
✅ FastMCP
✅ python-dotenv
✅ httpx

🔍 Checking agent structure...
✅ weather_agent/agent.py
✅ weather_agent/__init__.py

🔍 Checking MCP server connectivity...
✅ MCP server reachable at http://localhost:8085/mcp (HTTP 406)

🔍 Checking agent import...
✅ Agent imported successfully: weather_agent
   Model: model='openai/step-5-preview-free' llm_client=<google.adk.models.lite_llm.LiteLLMClient object at 0x0000029F7E19C050>

============================================================
✅ All checks passed!

🚀 Ready to start!
   Run: uv run adk web

📍 Then open: http://localhost:8000
```

### 6d. Giao diện web (`adk web`)

```
=== adk web (giao diện web của lab 04) ===
GET http://localhost:8000/  -> HTTP 307
GET /list-apps             -> ["weather_agent"]
```

`/list-apps` trả về `["weather_agent"]` — agent đã được ADK web nạp đúng.

---

## 7. Kết luận: MCP vs Function Calling

| Tiêu chí | Function Calling (phần 01) | MCP (phần 02–04) |
|---|---|---|
| Bản chất | Khả năng của **model** | **Giao thức** client–server |
| Khai báo schema | Viết **tay** trong app | `@mcp.tool()` **tự sinh** từ type hints |
| Nơi thực thi tool | **Trong app** | **Trong MCP server** |
| Khám phá tool | Hard-code danh sách | `list_tools()` tại runtime |
| Tái sử dụng | Copy code sang app khác | Cắm thêm client, không sửa server |
| Dùng ở production | — | Auth (401/403), Registry, Versioning |

**Kết luận quan trọng nhất:** hai khái niệm **không thay thế nhau**.
MCP là *chuẩn kết nối* client ↔ server; còn việc *model quyết định gọi tool nào* vẫn là **Function Calling** —
đúng như luồng đã chạy ở phần 04: ADK (client) dùng function calling để chọn tool, rồi gọi tool đó **qua giao thức MCP**.

---

## 8. Hạn chế & trung thực học thuật

1. **Dữ liệu ở phần 01 là mock** (đúng thiết kế gốc của lab — phần 01 minh hoạ cơ chế, không gọi API thật).
   Dữ liệu ở **phần 04 là thật** từ WeatherAPI.
2. **Model dùng để chạy:** `step-5-preview-free` (OpenCode Go) — **không cần fallback** ở cả phần 01 và 04.
   Ladder `deepseek-v4.1-flash` đã được cài sẵn trong code nhưng **không phải dùng**.
3. **Giao diện web** chỉ được xác nhận qua HTTP (`307` + `/list-apps` → `["weather_agent"]`),
   **không có ảnh chụp màn hình** chat thật trên UI. Bằng chứng chức năng nằm ở `smoke_agent.py` (mục 6b).
4. **Phần 03 (auth) không có token riêng cho từng scope** — đây là ví dụ mức lab; production thật cần JWT/OAuth + scopes.
5. Toàn bộ output trong báo cáo này được sinh từ lệnh thật và lưu trong `docs/evidence/`;
   không có dòng nào được gõ tay lại hay hard-code.

---

## 9. Các thay đổi so với repo gốc

- `01-function-calling/`: thêm `llm_client.py`, `test_llm_client.py`; viết lại `weather_function_calling.py` sang OpenAI SDK (OpenCode Go).
- `03-production/`: thêm `test_registry.py`.
- `04-lab/mcp-client/`: `agent.py` dùng `LiteLlm` (OpenCode Go); thêm `smoke_agent.py`; cập nhật `verify_setup.py` (kiểm tra `OPENCODE_API_KEY`, không in key).
- `04-lab/mcp-server/weather.py`: nạp `.env` để lấy `WEATHERAPI_KEY`/`PORT`.
- Thêm `.env.example`, `docs/evidence/`, `report.md`; bỏ track `.DS_Store`; ignore `.hermes/`.
