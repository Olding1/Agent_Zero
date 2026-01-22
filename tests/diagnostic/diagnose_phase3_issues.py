"""
诊断脚本 - 调查 RAG Simulator 问题

这个脚本会详细输出 RAG 测试的每一步，帮助我们理解为什么 Simulator 检测到问题。
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.pm import PM
from src.core.graph_designer import GraphDesigner
from src.core.simulator import Simulator
from src.llm import BuilderClient
from src.schemas import ToolsConfig, RAGConfig


async def diagnose_rag_issue():
    """详细诊断 RAG Simulator 问题"""
    
    print("="*80)
    print("RAG Simulator 问题诊断")
    print("="*80)
    
    builder = BuilderClient.from_env()
    pm = PM(builder)
    designer = GraphDesigner(builder)
    simulator = Simulator(builder)
    
    # Step 1: PM 分析
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
    print(f"✓ Status: {project_meta.status}")
    
    # Step 2: Graph Designer
    print("\n[Step 2] Graph Designer 设计图结构...")
    
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
    print(f"✓ Entry Point: {graph.entry_point}")
    
    print("\n节点列表:")
    for i, node in enumerate(graph.nodes, 1):
        print(f"  {i}. {node.id} (type: {node.type})")
    
    print("\n普通边:")
    for i, edge in enumerate(graph.edges, 1):
        print(f"  {i}. {edge.source} → {edge.target}")
    
    print("\n条件边:")
    for i, cond_edge in enumerate(graph.conditional_edges, 1):
        print(f"  {i}. {cond_edge.source} [condition: {cond_edge.condition}]")
        for key, value in cond_edge.branches.items():
            print(f"      - {key} → {value}")
    
    # Step 3: Simulator (详细模式)
    print("\n[Step 3] Simulator 沙盘推演 (详细模式)...")
    
    sim_result = await simulator.simulate(
        graph=graph,
        sample_input="这个项目是做什么的？",
        use_llm=False,  # 使用启发式模式，更快
        max_steps=20
    )
    
    print(f"\n仿真结果:")
    print(f"  Success: {sim_result.success}")
    print(f"  Total Steps: {sim_result.total_steps}")
    print(f"  Issues: {len(sim_result.issues)}")
    
    # 详细输出问题
    if sim_result.issues:
        print("\n⚠️ 检测到的问题:")
        for i, issue in enumerate(sim_result.issues, 1):
            print(f"\n  问题 {i}:")
            print(f"    类型: {issue.issue_type}")
            print(f"    严重程度: {issue.severity}")
            print(f"    描述: {issue.description}")
            print(f"    受影响节点: {', '.join(issue.affected_nodes)}")
            if issue.suggestion:
                print(f"    建议: {issue.suggestion}")
    
    # 输出完整执行轨迹
    print("\n完整执行轨迹:")
    print(sim_result.execution_trace)
    
    # 分析节点访问次数
    print("\n节点访问统计:")
    node_visits = {}
    for step in sim_result.steps:
        if step.node_id:
            node_visits[step.node_id] = node_visits.get(step.node_id, 0) + 1
    
    for node_id, count in sorted(node_visits.items(), key=lambda x: x[1], reverse=True):
        status = "⚠️ 过多" if count > 5 else "✓ 正常"
        print(f"  {node_id}: {count} 次 {status}")
    
    # 分析边的遍历
    print("\n边遍历分析:")
    edge_traversals = []
    prev_node = None
    for step in sim_result.steps:
        if step.step_type.value == "enter_node" and step.node_id:
            if prev_node and prev_node != step.node_id:
                edge_traversals.append((prev_node, step.node_id))
            prev_node = step.node_id
    
    print(f"  总共遍历了 {len(edge_traversals)} 条边")
    edge_counts = {}
    for source, target in edge_traversals:
        edge_key = f"{source} → {target}"
        edge_counts[edge_key] = edge_counts.get(edge_key, 0) + 1
    
    for edge, count in sorted(edge_counts.items(), key=lambda x: x[1], reverse=True):
        status = "⚠️ 循环" if count > 2 else "✓ 正常"
        print(f"  {edge}: {count} 次 {status}")
    
    # 最终状态
    print("\n最终状态:")
    for key, value in sim_result.final_state.items():
        if key == "messages":
            print(f"  {key}: {len(value)} 条消息")
        elif isinstance(value, (str, int, bool)):
            print(f"  {key}: {value}")
        elif isinstance(value, list):
            print(f"  {key}: [{len(value)} 项]")
        else:
            print(f"  {key}: {type(value).__name__}")
    
    print("\n" + "="*80)
    print("诊断完成")
    print("="*80)
    
    # 返回是否有错误
    return not sim_result.has_errors()


async def explain_pm_clarifier():
    """解释 PM Clarifier 的行为"""
    
    print("\n" + "="*80)
    print("PM Clarifier 行为解释")
    print("="*80)
    
    builder = BuilderClient.from_env()
    pm = PM(builder)
    
    test_cases = [
        ("创建一个简单的聊天助手，能够回答用户的问题", "简单需求"),
        ("创建一个聊天助手", "非常简单"),
        ("帮我写个爬虫", "模糊需求"),
        ("创建一个能回答Agent Zero项目相关问题的智能助手，使用项目文档作为知识库", "详细需求"),
    ]
    
    for query, label in test_cases:
        print(f"\n测试: {label}")
        print(f"输入: \"{query}\"")
        print(f"长度: {len(query)} 字符")
        
        # 测试启发式模式
        is_ready_heuristic, questions_heuristic = pm._heuristic_clarify(query)
        print(f"\n启发式判断: {'✓ 清晰' if is_ready_heuristic else '⚠️ 需要澄清'}")
        if questions_heuristic:
            for q in questions_heuristic:
                print(f"  - {q}")
        
        # 测试 LLM 模式
        print("\nLLM 判断: 调用中...")
        is_ready_llm, questions_llm = await pm.clarify_requirements(query, [])
        print(f"结果: {'✓ 清晰' if is_ready_llm else '⚠️ 需要澄清'}")
        if questions_llm:
            print("澄清问题:")
            for q in questions_llm:
                print(f"  - {q}")
        
        print("-" * 60)
    
    print("\n" + "="*80)
    print("PM Clarifier 解释完成")
    print("="*80)
    
    print("\n💡 关键点:")
    print("1. 启发式模式: 基于长度和关键词，快速判断")
    print("2. LLM 模式: 使用 AI 深度分析，更准确但可能更严格")
    print("3. 你的观点是对的: 即使是'简单需求'，澄清也是有价值的")
    print("4. 这确保了生成的 Agent 更符合用户真实需求")


if __name__ == "__main__":
    print("Phase 3 问题诊断工具\n")
    
    # 1. 解释 PM Clarifier
    asyncio.run(explain_pm_clarifier())
    
    # 2. 诊断 RAG Simulator
    success = asyncio.run(diagnose_rag_issue())
    
    if success:
        print("\n✅ RAG Simulator 没有严重问题")
    else:
        print("\n⚠️ RAG Simulator 检测到问题，请查看上面的详细分析")
