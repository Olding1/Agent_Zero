import inspect
import pkgutil
import importlib
import json
import traceback
from pathlib import Path
from langchain_core.tools import BaseTool

# Skip these modules as they are known to be problematic or duplicates
SKIP_MODULES = {
    'langchain_community.tools.convert_to_openai', # Utility
    'langchain_community.tools.plugin', # Deprecated
    'langchain_community.tools.render', # Utility
    'langchain_community.tools.format_tool_to_openai_function', # Utility
    'langchain_community.tools.gmail', # Complex auth, often fails import
    'langchain_community.tools.office365', # Complex auth
    'langchain_community.tools.file_management', # Already have some
}

def scan_tools():
    import langchain_community.tools
    package = langchain_community.tools
    prefix = package.__name__ + "."
    
    found_tools = []
    
    print(f"Scanning {prefix}...")
    
    for _, name, is_pkg in pkgutil.walk_packages(package.__path__, prefix):
        if name in SKIP_MODULES:
            continue
            
        try:
            module = importlib.import_module(name)
        except Exception as e:
            # print(f"Skipping {name}: {e}")
            continue
            
        # Find Tool classes
        for attr_name, attr_value in inspect.getmembers(module):
            if (inspect.isclass(attr_value) 
                and issubclass(attr_value, BaseTool) 
                and attr_value is not BaseTool
                and attr_value.__module__.startswith("langchain_community")):
                
                # Filter out base classes or mixins if possible
                if attr_name.startswith("Base") or "Mixin" in attr_name:
                    continue

                try:
                    # Generic instantiation attempt
                    # Many tools need params, so this might fail.
                    # We strictly prefer tools that can be instantiated with defaults OR we extract schema class-side if possible.
                    # Actually, we can get args_schema from the class if it's defined as a Pydantic model
                    
                    tool_name = getattr(attr_value, "name", None)
                    tool_desc = getattr(attr_value, "description", None)
                    
                    # If name/desc are properties, they might need instance
                    if isinstance(tool_name, property) or isinstance(tool_desc, property):
                         # Try instantiating with no args
                        try:
                            instance = attr_value()
                            tool_name = instance.name
                            tool_desc = instance.description
                            args_schema = instance.args_schema
                        except:
                            # Try with common mock api wrappers
                            # This is hard to do generically. 
                            # Let's Skip tools we can't inspect easily for now, or just record them for manual review?
                            # User said "ALL", so let's try our best.
                            continue
                    else:
                        # Class attributes
                        args_schema = getattr(attr_value, "args_schema", None)

                    if not tool_name or not tool_desc:
                        continue
                        
                    # Infer package name from module
                    # This is a guess. e.g. langchain_community.tools.arxiv -> arxiv
                    pkg_name_guess = name.split('.')[-1]
                    # Map some common ones
                    pkg_map = {
                        'google_serper': 'google-search-results',
                        'google_search': 'google-search-results',
                        'wikipedia': 'wikipedia',
                        'arxiv': 'arxiv',
                        'duckduckgo_search': 'duckduckgo-search',
                        'bing_search': 'langchain-community', # Needs azure key
                        'wolfram_alpha': 'wolframalpha',
                        'youtube': 'youtube-search',
                    }
                    pkg_req = pkg_map.get(pkg_name_guess, "langchain-community")

                    # Schema to dict
                    schema_json = None
                    if args_schema:
                        try:
                            schema_json = args_schema.schema()
                        except:
                            pass
                    
                    # Create definition entry
                    entry = {
                        "id": tool_name.replace(" ", "_").lower(),
                        "name": tool_name,
                        "description": tool_desc,
                        "package_name": pkg_req, # Best guess
                        "import_path": f"{name}.{attr_name}",
                        "category": "utility", # Default
                        "requires_api_key": True, # Assume true for safety unless listed
                        "tags": [pkg_name_guess, "community"],
                        "args_schema": schema_json
                    }
                    
                    # Check duplicates by ID
                    if not any(t['id'] == entry['id'] for t in found_tools):
                        found_tools.append(entry)
                        print(f"✅ Found: {tool_name} ({attr_name})")
                        
                except Exception as e:
                    # print(f"Error inspecting {attr_name}: {e}")
                    pass
                    
    return found_tools

if __name__ == "__main__":
    tools = scan_tools()
    print(f"\nTotal tools found: {len(tools)}")
    
    # Write to a temp json file
    with open("scanned_tools.json", "w", encoding="utf-8") as f:
        json.dump(tools, f, indent=2, ensure_ascii=False)
