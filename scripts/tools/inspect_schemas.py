from langchain_community.tools import (
    YouTubeSearchTool,
    StackExchangeTool,
    HumanInputRun,
    OpenWeatherMapQueryRun,
    SleepTool,
    GoogleSerperRun,
    YahooFinanceNewsTool,
    GoogleTrendsQueryRun,
    BraveSearch
)
from langchain_community.utilities import OpenWeatherMapAPIWrapper, GoogleSerperAPIWrapper, BraveSearchWrapper

try:
    from langchain_community.tools.openai_dalle_image_generation.tool import OpenAIDALLEImageGenerationTool
except ImportError:
    OpenAIDALLEImageGenerationTool = None

tools = [
    YouTubeSearchTool(),
    StackExchangeTool(),
    HumanInputRun(),
    OpenWeatherMapQueryRun(api_wrapper=OpenWeatherMapAPIWrapper()),
    SleepTool(),
    GoogleSerperRun(api_wrapper=GoogleSerperAPIWrapper()),
    YahooFinanceNewsTool(),
    GoogleTrendsQueryRun(api_wrapper=GoogleSerperAPIWrapper()), # Trends often uses Serper or similar wrapper
]

# Print schemas
import json
for tool in tools:
    print(f"--- {tool.name} ---")
    print(f"Import: {tool.__class__.__module__}.{tool.__class__.__name__}")
    if tool.args_schema:
        print(json.dumps(tool.args_schema.schema(), indent=2))
    else:
        print("No args_schema")
