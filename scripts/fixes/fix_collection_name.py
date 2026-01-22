"""
Quick fix for existing Agent with Chinese characters in collection name
"""

import re
from pathlib import Path

# Agent directory
agent_dir = Path(r"C:\Users\Administrator\Desktop\game\Agent_Zero\agents\AgentZero文档助手")
agent_file = agent_dir / "agent.py"

if not agent_file.exists():
    print(f"❌ Agent file not found: {agent_file}")
    exit(1)

# Read content
content = agent_file.read_text(encoding='utf-8')

# Original problematic collection name
old_pattern = r'collection_name="AgentZero文档助手_docs"'
# New sanitized collection name (replace non-ASCII with underscores)
new_value = 'collection_name="AgentZero______docs"'

# Replace
new_content = re.sub(old_pattern, new_value, content)

# Check if replacement was made
if new_content != content:
    # Backup
    backup_file = agent_dir / "agent.py.backup"
    agent_file.rename(backup_file)
    print(f"✅ Backup created: {backup_file}")
    
    # Write fixed content
    agent_file.write_text(new_content, encoding='utf-8')
    print(f"✅ Fixed collection name in: {agent_file}")
    print(f"   Old: AgentZero文档助手_docs")
    print(f"   New: AgentZero______docs")
else:
    print("⚠️ No replacement made - pattern not found")

print("\n🧪 Now run tests:")
print(f"cd {agent_dir}")
print(r"venv\Scripts\python.exe -m pytest tests\test_deepeval.py -v")
