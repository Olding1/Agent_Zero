import asyncio
from src.core.simulator import Simulator
from src.llm import BuilderClient
from src.schemas import (
    GraphStructure, NodeDef, EdgeDef, ConditionalEdgeDef,
    StateSchema, PatternConfig, PatternType, StateField, StateFieldType
)

async def test_hybrid_simulation():
    """Test hybrid simulation mode"""
    builder = BuilderClient.from_env()
    
    # Create simulator with hybrid mode
    sim_hybrid = Simulator(builder, hybrid_mode=True)
    
    # Create simple graph with tool
    nodes = [
        NodeDef(id='agent', type='llm', role_description='Agent'),
        NodeDef(id='tool_tavily_search', type='tool', config={'tool_name': 'tavily_search'})
    ]
    
    # Condition logic (deterministic)
    condition_logic = """
last_msg = state["messages"][-1]
if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
    return last_msg.tool_calls[0]["name"]
return "end"
"""
    
    cond_edges = [
        ConditionalEdgeDef(
            source='agent',
            condition='check_tool',
            condition_logic=condition_logic,
            branches={'tavily_search': 'tool_tavily_search', 'end': 'END'}
        )
    ]
    
    edges = [
        EdgeDef(source='tool_tavily_search', target='agent')
    ]
    
    state_schema = StateSchema(fields=[
        StateField(name='messages', type=StateFieldType.LIST_MESSAGE, default=[])
    ])
    
    graph = GraphStructure(
        pattern=PatternConfig(pattern_type=PatternType.SEQUENTIAL),
        nodes=nodes,
        edges=edges,
        conditional_edges=cond_edges,
        entry_point='agent',
        state_schema=state_schema
    )
    
    print("=" * 70)
    print("🆕 HYBRID SIMULATION MODE TEST")
    print("=" * 70)
    
    result = await sim_hybrid.simulate(graph, '搜索一下最新的 AI 新闻', max_steps=5)
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f'✅ Success: {result.success}')
    print(f'📊 Total Steps: {result.total_steps}')
    print(f'⚠️  Issues: {[(i.issue_type, i.description) for i in result.issues]}')
    
    # Check if tool was visited
    tool_visited = any(step.node_id == 'tool_tavily_search' for step in result.steps)
    print(f'\n🔧 Tool Node Visited: {tool_visited}')
    
    # Check final state
    final_messages = result.final_state.get('messages', [])
    print(f'\n💬 Final Messages Count: {len(final_messages)}')
    
    if final_messages:
        last_msg = final_messages[-1]
        if hasattr(last_msg, 'tool_calls'):
            print(f'🛠️  Last Message tool_calls: {last_msg.tool_calls}')
    
    print("\n" + "=" * 70)
    
    # Expected: No unreachable_node warning!
    assert len([i for i in result.issues if i.issue_type == "unreachable_node"]) == 0, \
        "❌ FAILED: Still has unreachable_node warning!"
    
    print("✅ TEST PASSED: No unreachable_node warnings!")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(test_hybrid_simulation())
