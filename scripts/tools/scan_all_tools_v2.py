import importlib
import inspect
import json
from langchain_core.tools import BaseTool

# List from previous step
MODULES = [
    "langchain_community.tools.ainetwork",
    "langchain_community.tools.amadeus",
    "langchain_community.tools.arxiv",
    "langchain_community.tools.asknews",
    "langchain_community.tools.audio",
    "langchain_community.tools.azure_ai_services",
    "langchain_community.tools.azure_cognitive_services",
    "langchain_community.tools.bearly",
    "langchain_community.tools.bing_search",
    "langchain_community.tools.brave_search",
    "langchain_community.tools.cassandra_database",
    "langchain_community.tools.clickup",
    "langchain_community.tools.cogniswitch",
    "langchain_community.tools.connery",
    "langchain_community.tools.databricks",
    "langchain_community.tools.dataforseo_api_search",
    "langchain_community.tools.dataherald",
    "langchain_community.tools.ddg_search",
    "langchain_community.tools.e2b_data_analysis",
    "langchain_community.tools.edenai",
    "langchain_community.tools.eleven_labs",
    "langchain_community.tools.few_shot",
    "langchain_community.tools.financial_datasets",
    "langchain_community.tools.github",
    "langchain_community.tools.gitlab",
    "langchain_community.tools.gmail",
    "langchain_community.tools.golden_query",
    "langchain_community.tools.google_cloud",
    "langchain_community.tools.google_finance",
    "langchain_community.tools.google_jobs",
    "langchain_community.tools.google_lens",
    "langchain_community.tools.google_places",
    "langchain_community.tools.google_scholar",
    "langchain_community.tools.google_search",
    "langchain_community.tools.google_serper",
    "langchain_community.tools.google_trends",
    "langchain_community.tools.graphql",
    "langchain_community.tools.human",
    "langchain_community.tools.interaction",
    "langchain_community.tools.jina_search",
    "langchain_community.tools.jira",
    "langchain_community.tools.json",
    "langchain_community.tools.memorize",
    "langchain_community.tools.merriam_webster",
    "langchain_community.tools.metaphor_search",
    "langchain_community.tools.mojeek_search",
    "langchain_community.tools.multion",
    "langchain_community.tools.nasa",
    "langchain_community.tools.nuclia",
    "langchain_community.tools.office365",
    "langchain_community.tools.openai_dalle_image_generation",
    "langchain_community.tools.openapi",
    "langchain_community.tools.openweathermap",
    "langchain_community.tools.passio_nutrition_ai",
    "langchain_community.tools.playwright",
    "langchain_community.tools.polygon",
    "langchain_community.tools.powerbi",
    "langchain_community.tools.pubmed",
    "langchain_community.tools.requests",
    "langchain_community.tools.riza",
    "langchain_community.tools.scenexplain",
    "langchain_community.tools.searchapi",
    "langchain_community.tools.searx_search",
    "langchain_community.tools.semanticscholar",
    "langchain_community.tools.shell",
    "langchain_community.tools.slack",
    "langchain_community.tools.sleep",
    "langchain_community.tools.spark_sql",
    "langchain_community.tools.sql_database",
    "langchain_community.tools.stackexchange",
    "langchain_community.tools.steam",
    "langchain_community.tools.steamship_image_generation",
    "langchain_community.tools.tavily_search",
    "langchain_community.tools.vectorstore",
    "langchain_community.tools.wikidata",
    "langchain_community.tools.wikipedia",
    "langchain_community.tools.wolfram_alpha",
    "langchain_community.tools.you",
    "langchain_community.tools.youtube",
    "langchain_community.tools.zapier",
    "langchain_community.tools.zenguard",
]

found_tools = []

for mod_name in MODULES:
    try:
        # print(f"Checking {mod_name}...")
        module = importlib.import_module(mod_name)
        
        # Look for BaseTool inside
        for attr_name, attr_value in inspect.getmembers(module):
            if (inspect.isclass(attr_value) 
                and issubclass(attr_value, BaseTool) 
                and attr_value is not BaseTool):
                
                # Check for concrete implementation
                if attr_name.startswith("Base") or "Mixin" in attr_name:
                    continue
                
                # Try simple instantiations
                try:
                    name = None
                    desc = None
                    args_schema = None
                    
                    # 1. Try class attributes first (safer)
                    if hasattr(attr_value, "name") and isinstance(attr_value.name, str):
                        name = attr_value.name
                    if hasattr(attr_value, "description") and isinstance(attr_value.description, str):
                        desc = attr_value.description
                    if hasattr(attr_value, "args_schema"):
                        args_schema = attr_value.args_schema

                    # 2. If missing, try instantiation
                    if not name or not desc:
                        try:
                            # Try no-arg
                            instance = attr_value()
                            name = instance.name
                            desc = instance.description
                            args_schema = instance.args_schema
                        except:
                            # 3. Fallback: Parse from docstring or class name
                            if not name:
                                name = attr_name
                            if not desc:
                                desc = getattr(attr_value, "__doc__", "") or "No description available."
                    
                    # 4. Filter out empty or abstract tools
                    if not name or "Base" in name or desc == "No description available.":
                         # try harder to get name
                         name = getattr(attr_value, "name", attr_name)

                    # Ensure we have a string for name
                    if not isinstance(name, str):
                        name = str(name)
                        
                    if name and desc:
                        # Extract schema json
                        schema_json = None
                        if args_schema:
                            try:
                                schema_json = args_schema.schema()
                            except:
                                try:
                                    schema_json = args_schema.model_json_schema()
                                except:
                                    pass
                        elif hasattr(attr_value, "args_schema") and attr_value.args_schema:
                             # Try getting schema from class attribute
                             try:
                                 schema_json = attr_value.args_schema.model_json_schema()
                             except:
                                 pass
                                
                        entry = {
                            "id": name.replace(" ", "_").replace(":", "").lower(),
                            "name": name,
                            "description": desc,
                            "package_name": "langchain-community", # Default
                            "import_path": f"{mod_name}.{attr_name}",
                            "category": "community",
                            "requires_api_key": True, # Conservative
                            "args_schema": schema_json
                        }
                        
                        # Add if unique
                        if not any(t['id'] == entry['id'] for t in found_tools):
                             found_tools.append(entry)
                             print(f"✅ Found: {name}")

                except:
                    pass

    except Exception as e:
        # print(f"Failed {mod_name}: {e}")
        pass

print(f"Total tools: {len(found_tools)}")
with open("scanned_tools_v2.json", "w", encoding="utf-8") as f:
    json.dump(found_tools, f, indent=2, ensure_ascii=False)
