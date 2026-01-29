"""重新编译 Agent 以应用模板修复"""
from src.core.compiler import Compiler
from pathlib import Path
import json

agent_dir = Path('agents/AgentZeroDocAssistant')
graph_file = agent_dir / 'graph.json'
template_dir = Path('src/templates')

print("🔄 重新编译 Agent...")
print(f"   Agent 目录: {agent_dir}")

# 读取 graph.json
with open(graph_file, 'r', encoding='utf-8') as f:
    graph_data = json.load(f)

# 编译
compiler = Compiler(template_dir=template_dir)
result = compiler.compile(graph_data, agent_dir)

print("✅ 编译完成!")
print(f"   生成的文件: {result}")
print("\n下一步: 运行测试验证修复")
