import asyncio
from src.core.simulator import Simulator
from src.llm import BuilderClient
from src.schemas import (
    GraphStructure, NodeDef, EdgeDef, ConditionalEdgeDef,
    StateSchema, PatternConfig, PatternType, StateField, StateFieldType
)

async def test_simulator_debug():
    """Quick test to see debug output"""
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
    print("STARTING SIMULATION WITH DEBUG LOGS")
    print("=" * 60)
    
    result = await sim.simulate(graph, '搜索一下最新的 AI 新闻', max_steps=5)
    
    print("\n" + "=" * 60)
    print("SIMULATION RESULT")
    print("=" * 60)
    print(f'Success: {result.success}')
    print(f'Total Steps: {result.total_steps}')
    print(f'Issues: {[(i.issue_type, i.description) for i in result.issues]}')
    
    # Check if tool was visited
    tool_visited = any(step.node_id == 'tool_tavily_search' for step in result.steps)
    print(f'\nTool Node Visited: {tool_visited}')

if __name__ == '__main__':
    asyncio.run(test_simulator_debug())
