import asyncio
from src.core.simulator import Simulator
from src.llm import BuilderClient
from src.schemas import (
    GraphStructure, NodeDef, EdgeDef, ConditionalEdgeDef,
    StateSchema, PatternConfig, PatternType, StateField, StateFieldType
)

async def test_llm_response():
    """Test to see actual LLM response"""
    builder = BuilderClient.from_env()
    sim = Simulator(builder)
    
    # Create simple graph with tool
    nodes = [
        NodeDef(id='agent', type='llm', role_description='Agent'),
        NodeDef(id='tool_tavily_search', type='tool', config={'tool_name': 'tavily_search'})
    ]
    
    cond_edges = [
        ConditionalEdgeDef(
            source='agent',
            condition='check_tool',
            condition_logic='',
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
    
    print("=" * 60)
    print("TESTING LLM RESPONSE WITH TOOL CONTEXT")
    print("=" * 60)
    
    # Run simulation with max_steps=2 to see first iteration
    result = await sim.simulate(graph, '搜索一下最新的 AI 新闻', max_steps=2, use_llm=True)
    
    print("\n" + "=" * 60)
    print("CHECKING MESSAGES")
    print("=" * 60)
    
    for i, msg in enumerate(result.final_state.get('messages', [])):
        print(f"\nMessage {i}:")
        print(f"  Type: {type(msg)}")
        print(f"  Role: {getattr(msg, 'role', 'N/A')}")
        print(f"  Content: {getattr(msg, 'content', 'N/A')[:100]}...")
        print(f"  tool_calls: {getattr(msg, 'tool_calls', 'N/A')}")

if __name__ == '__main__':
    asyncio.run(test_llm_response())
