"""
快速测试脚本 - 验证 RAG 路由修复
"""
import os
import sys

# 切换到 Agent 目录
os.chdir('agents/AgentZeroDocAssistant')

from agent import run_agent

# 测试查询
test_query = "Agent Zero 项目的 Slogan 是什么？"

print("=" * 60)
print("🧪 测试 RAG 路由修复")
print("=" * 60)
print(f"\n查询: {test_query}\n")

# 运行 Agent 并获取 trace
output, trace = run_agent(test_query, return_trace=True)

print(f"✅ Agent 输出:\n{output}\n")
print("=" * 60)
print(f"📊 Trace 分析:")
print(f"   - 总步骤数: {len(trace)}")

# 检查是否有 RAG 检索步骤
rag_steps = [s for s in trace if s.get("action") == "rag_retrieval"]
print(f"   - RAG 检索步骤: {len(rag_steps)}")

if rag_steps:
    print(f"\n✅ RAG 节点被正确调用!")
    for i, step in enumerate(rag_steps, 1):
        print(f"\n   步骤 {step['step']}:")
        print(f"      - 查询: {step.get('query', 'N/A')[:50]}...")
        print(f"      - 检索文档数: {step.get('num_docs', 0)}")
        print(f"      - 文档文件: {step.get('docs_file', 'N/A')}")
        
        # 尝试加载文档
        docs_file = step.get('docs_file')
        if docs_file:
            import json
            try:
                with open(docs_file, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                print(f"      - 文档内容预览:")
                for j, doc in enumerate(docs[:2], 1):
                    print(f"         {j}. {doc[:100]}...")
            except Exception as e:
                print(f"      - ❌ 无法加载文档: {e}")
else:
    print(f"\n❌ RAG 节点未被调用!")
    print("\n所有步骤:")
    for step in trace:
        print(f"   - 步骤 {step['step']}: {step.get('action', 'unknown')} ({step.get('node_id', 'unknown')})")

print("\n" + "=" * 60)
