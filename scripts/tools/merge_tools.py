import json
import sys
from pathlib import Path

# Add src to path to import definitions
sys.path.insert(0, str(Path.cwd()))
from src.tools.definitions import CURATED_TOOLS as EXISTING_TOOLS

def merge_tools():
    # Load scanned tools
    with open("scanned_tools_v2.json", "r", encoding="utf-8") as f:
        scanned_tools = json.load(f)
        
    print(f"Existing tools: {len(EXISTING_TOOLS)}")
    print(f"Scanned tools: {len(scanned_tools)}")
    
    # Create a map of existing imports for quick lookup
    existing_imports = {t["import_path"]: t for t in EXISTING_TOOLS}
    existing_ids = {t["id"]: t for t in EXISTING_TOOLS}
    
    merged_tools = list(EXISTING_TOOLS)
    added_count = 0
    
    for tool in scanned_tools:
        # Check for duplicates
        if tool["import_path"] in existing_imports:
            continue
        if tool["id"] in existing_ids:
            continue
            
        # Add defaults for missing fields
        if "tags" not in tool:
            tool["tags"] = ["community", tool["id"]]
        if "examples" not in tool:
            tool["examples"] = []
            
        merged_tools.append(tool)
        added_count += 1
        
    print(f"Added {added_count} new tools.")
    print(f"Total tools: {len(merged_tools)}")
    
    # Generate python file content
    content = '"""Curated tool definitions for Agent Zero v8.0.\n\n'
    content += 'This module contains a comprehensive list of tools from LangChain Community,\n'
    content += 'including both hand-picked curated tools and auto-discovered ones.\n'
    content += '"""\n\n'
    
    content += '# 全量工具列表 - 包含精选和扫描发现的工具\n'
    content += 'CURATED_TOOLS = [\n'
    
    for tool in merged_tools:
        content += '    {\n'
        for key, value in tool.items():
            content += f'        "{key}": {repr(value)},\n'
        content += '    },\n'
        
    content += ']\n\n'
    
    # Add footer statistics code
    content += """# 工具统计
TOOL_COUNT = len(CURATED_TOOLS)
CATEGORIES = list(set(tool["category"] for tool in CURATED_TOOLS))
FREE_TOOLS = [tool for tool in CURATED_TOOLS if not tool["requires_api_key"]]
API_KEY_TOOLS = [tool for tool in CURATED_TOOLS if tool["requires_api_key"]]

print(f\"\"\"
📊 Agent Zero v8.0 工具库统计:
- 总工具数: {TOOL_COUNT}
- 分类数: {len(CATEGORIES)}
- 免费工具: {len(FREE_TOOLS)}
- 需要 API Key: {len(API_KEY_TOOLS)}
- 分类: {', '.join(CATEGORIES)}
\"\"\")
"""

    with open("src/tools/definitions.py", "w", encoding="utf-8") as f:
        f.write(content)
        
    print("✅ Successfully updated src/tools/definitions.py")

if __name__ == "__main__":
    merge_tools()
