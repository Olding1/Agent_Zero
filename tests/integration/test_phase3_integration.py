"""
Integration Test for Phase 3 Blueprint Simulation System

This test verifies the complete workflow:
1. PM Clarifier + Planner
2. Graph Designer (3-step method)
3. Simulator (with real LLM)
4. Compiler

Run with: python tests/integration/test_phase3_integration.py
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.pm import PM
from src.core.graph_designer import GraphDesigner
from src.core.simulator import Simulator
from src.core.compiler import Compiler
from src.llm import BuilderClient
from src.schemas import ToolsConfig, RAGConfig


async def test_simple_chat_agent():
    """Test 1: Simple chat agent (Sequential pattern)"""
    print("\n" + "="*60)
    print("Test 1: Simple Chat Agent (Sequential Pattern)")
    print("="*60)
    
    # Initialize components
    builder = BuilderClient.from_env()  # Load from .env
    pm = PM(builder)
    designer = GraphDesigner(builder)
    simulator = Simulator(builder)
    compiler = Compiler(project_root / "src" / "templates")
    
    # Step 1: PM Analysis
    print("\n[Step 1] PM 分析需求...")
    user_query = "创建一个简单的聊天助手，能够回答用户的问题"
    
    project_meta = await pm.analyze_with_clarification_loop(
        user_query=user_query,
        chat_history=[],
        file_paths=None
    )
    
    print(f"✓ Agent Name: {project_meta.agent_name}")
    print(f"✓ Status: {project_meta.status}")
    print(f"✓ Complexity: {project_meta.complexity_score}/10")
    
    if project_meta.status == "clarifying":
        print("⚠️ 需要澄清:")
        for q in project_meta.clarification_questions:
            print(f"  - {q}")
        return False
    
    # Step 2: Graph Designer
    print("\n[Step 2] Graph Designer 设计图结构...")
    graph = await designer.design_graph(
        project_meta=project_meta,
        tools_config=ToolsConfig(enabled_tools=[]),
        rag_config=None
    )
    
    print(f"✓ Pattern: {graph.pattern.pattern_type.value}")
    print(f"✓ Nodes: {len(graph.nodes)} ({', '.join([n.id for n in graph.nodes])})")
    print(f"✓ State Fields: {len(graph.state_schema.fields)}")
    
    # Step 3: Simulator (with real LLM)
    print("\n[Step 3] Simulator 沙盘推演 (使用真实 LLM)...")
    sim_result = await simulator.simulate(
        graph=graph,
        sample_input="你好，请介绍一下自己",
        use_llm=True  # Use real LLM
    )
    
    print(f"✓ Success: {sim_result.success}")
    print(f"✓ Total Steps: {sim_result.total_steps}")
    print(f"✓ Issues: {len(sim_result.issues)}")
    
    if sim_result.issues:
        for issue in sim_result.issues:
            print(f"  [{issue.severity}] {issue.description}")
    
    print("\n执行轨迹:")
    print(sim_result.execution_trace)
    
    # Step 4: Compiler
    print("\n[Step 4] Compiler 生成代码...")
    output_dir = project_root / "agents" / "test_simple_chat"
    
    compile_result = compiler.compile(
        project_meta=project_meta,
        graph=graph,
        rag_config=None,
        tools_config=ToolsConfig(enabled_tools=[]),
        output_dir=output_dir
    )
    
    print(f"✓ Compilation: {'Success' if compile_result.success else 'Failed'}")
    print(f"✓ Output Dir: {compile_result.output_dir}")
    print(f"✓ Generated Files: {', '.join(compile_result.generated_files)}")
    
    return sim_result.success and compile_result.success


async def test_reflection_agent():
    """Test 2: Writing assistant with reflection (Reflection pattern)"""
    print("\n" + "="*60)
    print("Test 2: Writing Assistant (Reflection Pattern)")
    print("="*60)
    
    builder = BuilderClient.from_env()  # Load from .env
    pm = PM(builder)
    designer = GraphDesigner(builder)
    simulator = Simulator(builder)
    compiler = Compiler(project_root / "src" / "templates")
    
    # Step 1: PM Analysis
    print("\n[Step 1] PM 分析需求...")
    user_query = "创建一个写作助手，能够生成文章并根据反馈进行优化改进"
    
    project_meta = await pm.analyze_with_clarification_loop(
        user_query=user_query,
        chat_history=[],
        file_paths=None
    )
    
    print(f"✓ Agent Name: {project_meta.agent_name}")
    print(f"✓ Complexity: {project_meta.complexity_score}/10")
    
    if project_meta.execution_plan:
        print(f"✓ Execution Plan: {len(project_meta.execution_plan)} steps")
        for step in project_meta.execution_plan:
            print(f"  {step.step}. [{step.role}] {step.goal}")
    
    # Step 2: Graph Designer
    print("\n[Step 2] Graph Designer 设计图结构...")
    graph = await designer.design_graph(
        project_meta=project_meta,
        tools_config=ToolsConfig(enabled_tools=[]),
        rag_config=None
    )
    
    print(f"✓ Pattern: {graph.pattern.pattern_type.value}")
    print(f"✓ Nodes: {', '.join([n.id for n in graph.nodes])}")
    print(f"✓ Max Iterations: {graph.pattern.max_iterations}")
    
    # Check for reflection-specific state fields
    has_draft = graph.state_schema.has_field("draft")
    has_feedback = graph.state_schema.has_field("feedback")
    print(f"✓ Reflection State: draft={has_draft}, feedback={has_feedback}")
    
    # Step 3: Simulator
    print("\n[Step 3] Simulator 沙盘推演 (使用真实 LLM)...")
    sim_result = await simulator.simulate(
        graph=graph,
        sample_input="写一篇关于人工智能的短文",
        use_llm=True,
        max_steps=15  # Allow more steps for iteration
    )
    
    print(f"✓ Success: {sim_result.success}")
    print(f"✓ Total Steps: {sim_result.total_steps}")
    print(f"✓ Issues: {len(sim_result.issues)}")
    
    # Show final state
    if "iteration_count" in sim_result.final_state:
        print(f"✓ Iterations: {sim_result.final_state['iteration_count']}")
    
    print("\n执行轨迹 (前10步):")
    lines = sim_result.execution_trace.split('\n')[:12]
    print('\n'.join(lines))
    
    # Step 4: Compiler
    print("\n[Step 4] Compiler 生成代码...")
    output_dir = project_root / "agents" / "test_reflection_writer"
    
    compile_result = compiler.compile(
        project_meta=project_meta,
        graph=graph,
        rag_config=None,
        tools_config=ToolsConfig(enabled_tools=[]),
        output_dir=output_dir
    )
    
    print(f"✓ Compilation: {'Success' if compile_result.success else 'Failed'}")
    print(f"✓ Generated Files: {len(compile_result.generated_files)}")
    
    return sim_result.success and compile_result.success


async def test_rag_agent():
    """Test 3: RAG-based Q&A agent"""
    print("\n" + "="*60)
    print("Test 3: RAG Q&A Agent")
    print("="*60)
    
    builder = BuilderClient.from_env()  # Load from .env
    pm = PM(builder)
    designer = GraphDesigner(builder)
    simulator = Simulator(builder)
    compiler = Compiler(project_root / "src" / "templates")
    
    # Step 1: PM Analysis
    print("\n[Step 1] PM 分析需求...")
    user_query = "创建一个能够回答项目文档相关问题的智能助手"
    file_paths = [project_root / "README.md"]
    
    project_meta = await pm.analyze_with_clarification_loop(
        user_query=user_query,
        chat_history=[],
        file_paths=file_paths
    )
    
    print(f"✓ Agent Name: {project_meta.agent_name}")
    print(f"✓ Has RAG: {project_meta.has_rag}")
    print(f"✓ Files: {len(project_meta.file_paths or [])}")
    
    # Step 2: Graph Designer
    print("\n[Step 2] Graph Designer 设计图结构...")
    
    # Create RAG config
    rag_config = RAGConfig(
        vector_store="chroma",
        embedding_provider="ollama",
        embedding_model_name="nomic-embed-text",
        chunk_size=500,
        chunk_overlap=50,
        k_retrieval=3
    )
    
    graph = await designer.design_graph(
        project_meta=project_meta,
        tools_config=ToolsConfig(enabled_tools=[]),
        rag_config=rag_config
    )
    
    print(f"✓ Pattern: {graph.pattern.pattern_type.value}")
    print(f"✓ Nodes: {', '.join([n.id for n in graph.nodes])}")
    
    # Check for RAG node
    has_rag_node = any(n.type == "rag" for n in graph.nodes)
    print(f"✓ Has RAG Node: {has_rag_node}")
    
    # Step 3: Simulator
    print("\n[Step 3] Simulator 沙盘推演...")
    sim_result = await simulator.simulate(
        graph=graph,
        sample_input="这个项目是做什么的？",
        use_llm=True
    )
    
    print(f"✓ Success: {sim_result.success}")
    print(f"✓ Total Steps: {sim_result.total_steps}")
    
    # Step 4: Compiler
    print("\n[Step 4] Compiler 生成代码...")
    output_dir = project_root / "agents" / "test_rag_qa"
    
    compile_result = compiler.compile(
        project_meta=project_meta,
        graph=graph,
        rag_config=rag_config,
        tools_config=ToolsConfig(enabled_tools=[]),
        output_dir=output_dir
    )
    
    print(f"✓ Compilation: {'Success' if compile_result.success else 'Failed'}")
    
    # Check for RAG-specific files
    if compile_result.success:
        agent_file = output_dir / "agent.py"
        if agent_file.exists():
            content = agent_file.read_text(encoding='utf-8')
            has_rag_code = "rag_retriever" in content
            print(f"✓ RAG Code Generated: {has_rag_code}")
    
    return sim_result.success and compile_result.success


async def test_pm_clarification():
    """Test 4: PM Clarification for vague requirements"""
    print("\n" + "="*60)
    print("Test 4: PM Clarification (Vague Requirements)")
    print("="*60)
    
    builder = BuilderClient.from_env()  # Load from .env
    pm = PM(builder)
    
    print("\n[Test] 模糊需求: '帮我写个爬虫'")
    
    project_meta = await pm.analyze_with_clarification_loop(
        user_query="帮我写个爬虫",
        chat_history=[],
        file_paths=None
    )
    
    print(f"✓ Status: {project_meta.status}")
    
    if project_meta.status == "clarifying":
        print(f"✓ Clarification Needed: True")
        print(f"✓ Questions ({len(project_meta.clarification_questions or [])}):")
        for i, q in enumerate(project_meta.clarification_questions or [], 1):
            print(f"  {i}. {q}")
        return True
    else:
        print("⚠️ Expected clarification but got ready status")
        return False


async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("Phase 3 Integration Tests - Real API Calls")
    print("="*80)
    
    results = {}
    
    try:
        # Test 1: Simple Chat
        results["simple_chat"] = await test_simple_chat_agent()
        
        # Test 2: Reflection
        results["reflection"] = await test_reflection_agent()
        
        # Test 3: RAG
        results["rag"] = await test_rag_agent()
        
        # Test 4: PM Clarification
        results["clarification"] = await test_pm_clarification()
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(results.values())


if __name__ == "__main__":
    print("Starting Phase 3 Integration Tests...")
    print("This will make real API calls to test the complete workflow.\n")
    
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎉 All integration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
