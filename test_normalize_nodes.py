"""
测试 GraphDesigner._normalize_special_nodes() 方法
"""

# 模拟 LLM 生成的包含 __end__ 的 Graph
test_graph = {
    "pattern": {
        "pattern_type": "sequential",
        "max_iterations": 3,
        "description": "Test pattern"
    },
    "state_schema": {
        "name": "TestState",
        "fields": []
    },
    "nodes": [
        {"id": "agent", "type": "llm"},
        {"id": "router", "type": "conditional"}
    ],
    "edges": [
        {"source": "agent", "target": "__end__"}  # ← 应该被转换为 "END"
    ],
    "conditional_edges": [
        {
            "source": "router",
            "condition": "should_continue",
            "branches": {
                "continue": "agent",
                "finish": "__end__"  # ← 应该被转换为 "END"
            }
        }
    ],
    "entry_point": "router"
}

# 测试规范化
from src.core.graph_designer import GraphDesigner
from src.llm.builder_client import BuilderClient

# 创建 GraphDesigner 实例
client = BuilderClient.from_env()
designer = GraphDesigner(client)

# 调用规范化方法
normalized = designer._normalize_special_nodes(test_graph.copy())

# 验证结果
print("原始 Graph:")
print(f"  edges[0].target: {test_graph['edges'][0]['target']}")
print(f"  conditional_edges[0].branches['finish']: {test_graph['conditional_edges'][0]['branches']['finish']}")

print("\n规范化后:")
print(f"  edges[0].target: {normalized['edges'][0]['target']}")
print(f"  conditional_edges[0].branches['finish']: {normalized['conditional_edges'][0]['branches']['finish']}")

# 验证是否成功转换
assert normalized['edges'][0]['target'] == "END", "Regular edge 未正确转换"
assert normalized['conditional_edges'][0]['branches']['finish'] == "END", "Conditional edge 未正确转换"

print("\n✅ 所有测试通过!")
