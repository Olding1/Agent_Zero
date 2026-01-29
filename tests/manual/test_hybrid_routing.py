import asyncio
from src.core.simulator import Simulator
from src.llm import BuilderClient
from src.schemas import (
    GraphStructure, NodeDef, EdgeDef, ConditionalEdgeDef,
    StateSchema, PatternConfig, PatternType, StateField, StateFieldType
)
from types import SimpleNamespace

async def test_hybrid_routing_logic():
    """Test hybrid simulation routing logic with mocked state"""
    builder = BuilderClient.from_env()
    
    # Create simulator with hybrid mode
    sim = Simulator(builder, hybrid_mode=True)
    
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
    print("🧪 TEST 1: State WITH tool_calls → Should route to tool")
    print("=" * 70)
    
    # Create state with tool_calls
    state_with_tools = {
        "messages": [
            SimpleNamespace(role="user", content="Search AI news", type="human"),
            SimpleNamespace(
                role="assistant",
                content="Searching...",
                tool_calls=[{"name": "tavily_search", "args": {}}],
                type="ai"
            )
        ]
    }
    
    # Test routing
    next_node = sim._execute_condition_logic(cond_edges[0], state_with_tools)
    print(f"✅ Result: {next_node}")
    assert next_node == "tool_tavily_search", f"Expected tool_tavily_search, got {next_node}"
    print("✅ PASS: Correctly routed to tool node\n")
    
    print("=" * 70)
    print("🧪 TEST 2: State WITHOUT tool_calls → Should route to end")
    print("=" * 70)
    
    # Create state without tool_calls
    state_without_tools = {
        "messages": [
            SimpleNamespace(role="user", content="Hello", type="human"),
            SimpleNamespace(
                role="assistant",
                content="Hi there!",
                tool_calls=[],
                type="ai"
            )
        ]
    }
    
    # Test routing
    next_node = sim._execute_condition_logic(cond_edges[0], state_without_tools)
    print(f"✅ Result: {next_node}")
    assert next_node == "END", f"Expected END, got {next_node}"
    print("✅ PASS: Correctly routed to END\n")
    
    print("=" * 70)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 70)
    print("\n✅ Hybrid Simulation Routing Logic is CORRECT!")
    print("✅ Deterministic routing works as expected!")
    print("✅ No more reliance on probabilistic heuristics!")

if __name__ == '__main__':
    asyncio.run(test_hybrid_routing_logic())
