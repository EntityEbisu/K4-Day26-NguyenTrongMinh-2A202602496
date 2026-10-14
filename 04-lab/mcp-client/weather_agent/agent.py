"""
Weather Agent — kết nối MCP server qua Streamable HTTP.

LLM: OpenCode Go (OpenAI-compatible) qua ADK LiteLlm, model `step-5-preview-free`.
Quirk OpenCode Go: BẮT BUỘC header `x-opencode-session`, cần User-Agent riêng,
và là reasoning model nên cần budget token lớn (>= 2048).
"""
import logging
import os

from dotenv import load_dotenv

load_dotenv()  # đọc .env ở thư mục mcp-client/ (hoặc thư mục cha)

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mặc định: server chạy local. Deploy lên Cloud Run thì đặt MCP_SERVER_URL trong .env
# (ví dụ: https://<service>.run.app/mcp). verify_setup.py đọc cùng biến này.
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")

# OpenCode Go (OpenAI-compatible)
OC_BASE_URL = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/go/v1")
OC_SESSION = os.getenv("OPENCODE_SESSION_ID", "day26-minh-001")
MODEL_ID = os.getenv("OPENCODE_MODEL", "step-5-preview-free")

logger.info("🌐 Initializing weather agent with remote MCP server")
logger.info(f"📡 MCP Server: {MCP_SERVER_URL}")
logger.info(f"🤖 Model: openai/{MODEL_ID} via {OC_BASE_URL}")


def _build_model() -> LiteLlm:
    """LiteLlm trỏ OpenCode Go. Header `x-opencode-session` là BẮT BUỘC."""
    return LiteLlm(
        model=f"openai/{MODEL_ID}",
        api_base=OC_BASE_URL,
        api_key=os.getenv("OPENCODE_API_KEY"),
        extra_headers={
            "x-opencode-session": OC_SESSION,
            "User-Agent": "day26-weather-lab/1.0",
        },
        max_tokens=2048,  # reasoning model cần budget lớn
    )


try:
    # Create connection parameters for the remote MCP server
    connection_params = StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,
        timeout=30.0,  # Increased timeout for Cloud Run cold starts
    )

    # Create the MCP toolset - this will connect to the remote server
    logger.info("🔌 Connecting to MCP server...")
    weather_tools = McpToolset(
        connection_params=connection_params,
    )
    logger.info("✅ MCP toolset created successfully")

    # Create the agent with remote MCP tools
    root_agent = Agent(
        name="weather_agent",
        model=_build_model(),
        tools=[weather_tools],
        instruction=(
            "Bạn là trợ lý thời tiết, trả lời bằng tiếng Việt tự nhiên, ngắn gọn. "
            "Dùng công cụ MCP để lấy dữ liệu thời tiết thật trước khi trả lời."
        ),
    )
    logger.info("✅ Weather agent initialized with remote MCP tools:")
    logger.info("   - get_current_weather(city)")
    logger.info("   - get_forecast(city, days)")
    logger.info("   - health_check()")
    logger.info("🎉 Remote MCP connection successful!")

except Exception as e:
    logger.error(f"❌ Failed to connect to remote MCP server: {e}")
    logger.error(f"   Server URL: {MCP_SERVER_URL}")
    import traceback
    traceback.print_exc()

    # Create a fallback agent without tools
    logger.warning("⚠️  Creating fallback agent without MCP tools")
    root_agent = Agent(
        name="weather_agent",
        model=_build_model(),
    )
