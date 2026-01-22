"""
诊断 Compiler 失败问题

重现 Test 2 (Reflection Pattern) 的编译失败
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
from src.core.compiler import Compiler
from src.llm import BuilderClient
from src.schemas import ToolsConfig


async def diagnose_compiler_issue():
    """诊断 Compiler 编译失败问题"""
    
    print("="*80)
    print("Compiler 失败问题诊断")
    print("="*80)
    
    builder = BuilderClient.from_env()
    pm = PM(builder)
    designer = GraphDesigner(builder)
    compiler = Compiler(project_root / "src" / "templates")
    
    # Step 1: PM 分析（Reflection 模式）
    print("\n[Step 1] PM 分析需求...")
    user_query = "创建一个写作助手，能够生成文章并根据反馈进行优化改进"
    
    project_meta = await pm.analyze_with_clarification_loop(
        user_query=user_query,
        chat_history=[],
        file_paths=None
    )
    
    print(f"✓ Agent Name: {project_meta.agent_name}")
    print(f"✓ Status: {project_meta.status}")
    print(f"✓ Complexity: {project_meta.complexity_score}/10")
    
    # Step 2: Graph Designer
    print("\n[Step 2] Graph Designer 设计图结构...")
    graph = await designer.design_graph(
        project_meta=project_meta,
        tools_config=ToolsConfig(enabled_tools=[]),
        rag_config=None
    )
    
    print(f"✓ Pattern: {graph.pattern.pattern_type.value}")
    print(f"✓ Nodes: {len(graph.nodes)}")
    print(f"✓ State Fields: {len(graph.state_schema.fields)}")
    
    # 详细检查 GraphStructure
    print("\n[详细检查] GraphStructure 内容:")
    print(f"  pattern: {graph.pattern}")
    print(f"  pattern.pattern_type: {graph.pattern.pattern_type}")
    print(f"  pattern.max_iterations: {graph.pattern.max_iterations}")
    
    print(f"\n  state_schema: {graph.state_schema}")
    print(f"  state_schema.fields: {len(graph.state_schema.fields)} 个字段")
    for field in graph.state_schema.fields:
        print(f"    - {field.name}: {field.type.value}")
    
    print(f"\n  nodes: {len(graph.nodes)} 个节点")
    for node in graph.nodes:
        print(f"    - {node.id} (type: {node.type})")
    
    print(f"\n  edges: {len(graph.edges)} 条边")
    for edge in graph.edges:
        print(f"    - {edge.source} → {edge.target}")
    
    print(f"\n  conditional_edges: {len(graph.conditional_edges)} 条条件边")
    for cond_edge in graph.conditional_edges:
        print(f"    - {cond_edge.source} [condition: {cond_edge.condition}]")
        for key, value in cond_edge.branches.items():
            print(f"        {key} → {value}")
    
    # Step 3: Compiler（详细错误捕获）
    print("\n[Step 3] Compiler 生成代码...")
    output_dir = project_root / "agents" / "test_reflection_debug"
    
    try:
        compile_result = compiler.compile(
            project_meta=project_meta,
            graph=graph,
            rag_config=None,
            tools_config=ToolsConfig(enabled_tools=[]),
            output_dir=output_dir
        )
        
        print(f"\n编译结果:")
        print(f"  Success: {compile_result.success}")
        print(f"  Output Dir: {compile_result.output_dir}")
        print(f"  Generated Files: {len(compile_result.generated_files)}")
        
        if compile_result.success:
            print("\n✅ 编译成功！")
            for file in compile_result.generated_files:
                print(f"  - {file}")
            
            # 检查生成的代码
            agent_file = output_dir / "agent.py"
            if agent_file.exists():
                print(f"\n生成的 agent.py 文件大小: {agent_file.stat().st_size} bytes")
                
                # 读取前50行
                with open(agent_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:50]
                    print("\n前50行内容:")
                    for i, line in enumerate(lines, 1):
                        print(f"{i:3d}: {line.rstrip()}")
        else:
            print(f"\n❌ 编译失败！")
            print(f"错误信息: {compile_result.error_message}")
            
            # 详细分析错误
            if compile_result.error_message:
                print("\n错误分析:")
                if "AttributeError" in compile_result.error_message:
                    print("  - 可能是 graph.pattern 或 graph.state_schema 为 None")
                elif "KeyError" in compile_result.error_message:
                    print("  - 可能是模板缺少某个必需的变量")
                elif "TypeError" in compile_result.error_message:
                    print("  - 可能是类型不匹配")
                
                print(f"\n完整错误:")
                print(compile_result.error_message)
    
    except Exception as e:
        print(f"\n❌ 编译过程抛出异常！")
        print(f"异常类型: {type(e).__name__}")
        print(f"异常信息: {str(e)}")
        
        import traceback
        print("\n完整堆栈:")
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("诊断完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(diagnose_compiler_issue())
