from langchain_community.tools.youtube.search import YouTubeSearchTool
from langchain_community.tools.stackexchange.tool import StackExchangeTool
from langchain_community.tools.human.tool import HumanInputRun
from langchain_community.tools.openweathermap.tool import OpenWeatherMapQueryRun
from langchain_community.tools.sleep.tool import SleepTool
from langchain_community.tools.google_serper.tool import GoogleSerperRun
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool

# Mock wrappers
class MockWrapper:
    def run(self, *args, **kwargs): pass

try:
    from langchain_community.utilities import OpenWeatherMapAPIWrapper
    weather_wrapper = OpenWeatherMapAPIWrapper()
except:
    weather_wrapper = MockWrapper()

try:
    from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
    serper_wrapper = GoogleSerperAPIWrapper()
except:
    serper_wrapper = MockWrapper()

tools = [
    YouTubeSearchTool(),
    StackExchangeTool(),
    HumanInputRun(),
    OpenWeatherMapQueryRun(api_wrapper=weather_wrapper),
    SleepTool(),
    GoogleSerperRun(api_wrapper=serper_wrapper),
    YahooFinanceNewsTool(),
]

import json
for tool in tools:
    print(f"--- {tool.name} ---")
    print(f"Import: {tool.__class__.__module__}.{tool.__class__.__name__}")
    if tool.args_schema:
        print(json.dumps(tool.args_schema.schema(), indent=2))
    else:
        print("No args_schema")
