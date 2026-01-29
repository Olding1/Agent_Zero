"""Test script for v7.3-v7.6 new features.

This script tests:
- v7.3: uv integration and Trace visualization
- v7.4: PM inference mode
- v7.5: Tool metadata with schema
- v7.6: Pattern auto-selection
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file
from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件中的环境变量

from src.core.env_manager import EnvManager
from src.core.pm import PM
from src.core.graph_designer import GraphDesigner
from src.core.simulator import Simulator
from src.llm import BuilderClient
from src.tools.registry import ToolRegistry, ToolMetadata
from src.utils import generate_trace_html, generate_trace_summary


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"🧪 {title}")
    print("=" * 70)


async def test_uv_integration():
    """Test v7.3: uv integration."""
    print_section("v7.3 测试: uv 集成")
    
    # Create a test agent directory
    test_dir = Path("agents/test_uv_agent")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple requirements.txt
    (test_dir / "requirements.txt").write_text("pydantic>=2.0.0\n")
    
    # Test with uv enabled
    print("\n📦 测试 uv 集成...")
    env_manager = EnvManager(test_dir, use_uv=True)
    
    result = env_manager.setup_environment()
    
    print(f"\n结果:")
    print(f"  ✅ 成功: {result.success}")
    print(f"  ⚡ 使用 uv: {result.used_uv}")
    print(f"  📊 性能指标: {result.metrics}")
    
    if result.metrics:
        print(f"\n性能报告:")
        print(f"  - 下载时间: {result.metrics.get('download_time', 0):.2f}s")
        print(f"  - 创建环境: {result.metrics.get('venv_create_time', 0):.2f}s")
        print(f"  - 安装依赖: {result.metrics.get('install_time', 0):.2f}s")
        print(f"  - 总计: {result.metrics.get('total_time', 0):.2f}s")
    
    # Cleanup
    env_manager.cleanup()
    
    return result.success


async def test_trace_visualization():
    """Test v7.3: Trace visualization."""
    print_section("v7.3 测试: 结构化 Trace 可视化")
    
    # Create a mock simulation result
    from src.schemas import SimulationResult, SimulationStep, SimulationIssue, SimulationStepType
    from datetime import datetime
    
    trace = SimulationResult(
        success=True,
        total_steps=3,
        steps=[
            SimulationStep(
                step_number=1,
                step_type=SimulationStepType.ENTER_NODE,
                node_id="agent",
                description="进入 agent 节点,准备处理用户输入"
            ),
            SimulationStep(
                step_number=2,
                step_type=SimulationStepType.STATE_UPDATE,
                node_id="agent",
                description="更新状态,添加用户消息"
            ),
            SimulationStep(
                step_number=3,
                step_type=SimulationStepType.EXIT_NODE,
                node_id="agent",
                description="退出 agent 节点,返回响应"
            ),
        ],
        execution_trace="Step 1: Enter agent\nStep 2: Update state\nStep 3: Exit agent",
        simulated_at=datetime.now()
    )
    
    # Generate HTML
    output_path = Path("test_trace_report.html")
    html = generate_trace_html(trace, output_path)
    
    print(f"\n✅ HTML 报告已生成: {output_path}")
    print(f"   文件大小: {len(html)} 字节")
    
    # Generate summary
    summary = generate_trace_summary(trace)
    print(f"\n📝 文本摘要:")
    print(summary)
    
    return True


async def test_pm_inference():
    """Test v7.4: PM inference mode."""
    print_section("v7.4 测试: PM 推断式分析")
    
    # Initialize PM
    builder_client = BuilderClient.from_env()
    pm = PM(builder_client)
    
    # Test cases
    test_cases = [
        ("帮我做个聊天机器人", "简短输入"),
        ("创建一个能够查询公司文档并回答问题的 RAG Agent,需要支持 PDF 和 Word 文档", "详细输入"),
    ]
    
    for user_input, case_name in test_cases:
        print(f"\n🧪 测试用例: {case_name}")
        print(f"   输入: {user_input}")
        
        # Analyze with inference
        project_meta = await pm.analyze_with_inference(user_input)
        
        print(f"\n   结果:")
        print(f"   - Agent 名称: {project_meta.agent_name}")
        print(f"   - 置信度: {project_meta.confidence:.0%}")
        print(f"   - 状态: {project_meta.status}")
        print(f"   - 复杂度: {project_meta.complexity_score}/10")
        
        if project_meta.missing_info:
            print(f"   - 缺失信息: {', '.join(project_meta.missing_info)}")
        
        if project_meta.clarification_questions:
            print(f"   - 澄清问题:")
            for i, q in enumerate(project_meta.clarification_questions, 1):
                print(f"     {i}. {q}")
    
    return True


async def test_tool_metadata():
    """Test v7.5: Tool metadata with schema."""
    print_section("v7.5 测试: 工具元数据 Schema 支持")
    
    # Create a tool metadata with schema
    metadata = ToolMetadata(
        name="test_search",
        description="测试搜索工具",
        category="search",
        tags=["search", "web"],
        requires_api_key=True,
        openapi_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询"},
                "max_results": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        },
        examples=[
            {"query": "Agent Zero 是什么", "max_results": 3},
            {"query": "LangGraph 教程"}
        ]
    )
    
    print(f"\n✅ 工具元数据创建成功:")
    print(f"   - 名称: {metadata.name}")
    print(f"   - 分类: {metadata.category}")
    print(f"   - 标签: {', '.join(metadata.tags)}")
    print(f"   - Schema: {'✓ 已定义' if metadata.openapi_schema else '✗ 未定义'}")
    print(f"   - 示例数量: {len(metadata.examples)}")
    
    if metadata.openapi_schema:
        print(f"\n   Schema 详情:")
        print(f"   - 参数: {list(metadata.openapi_schema.get('properties', {}).keys())}")
        print(f"   - 必需: {metadata.openapi_schema.get('required', [])}")
    
    return True


async def test_pattern_selection():
    """Test v7.6: Pattern auto-selection."""
    print_section("v7.6 测试: 架构自动映射")
    
    # Initialize components
    builder_client = BuilderClient.from_env()
    designer = GraphDesigner(builder_client)
    
    # Test cases
    from src.schemas import ProjectMeta, TaskType, ExecutionStep
    
    test_cases = [
        (
            ProjectMeta(
                agent_name="SimpleBot",
                description="简单问答",
                user_intent_summary="简单聊天",
                complexity_score=2
            ),
            "简单任务"
        ),
        (
            ProjectMeta(
                agent_name="CodeReviewer",
                description="代码审查并提供改进建议",
                user_intent_summary="迭代改进代码",
                complexity_score=5
            ),
            "迭代改进任务"
        ),
        (
            ProjectMeta(
                agent_name="ComplexAgent",
                description="复杂多步骤任务",
                user_intent_summary="多步骤执行",
                complexity_score=8,
                execution_plan=[
                    ExecutionStep(step=1, role="Planner", goal="规划"),
                    ExecutionStep(step=2, role="Executor", goal="执行"),
                    ExecutionStep(step=3, role="Reviewer", goal="审查"),
                    ExecutionStep(step=4, role="Finalizer", goal="完成"),
                ]
            ),
            "复杂多步骤任务"
        ),
    ]
    
    for project_meta, case_name in test_cases:
        print(f"\n🧪 测试用例: {case_name}")
        print(f"   复杂度: {project_meta.complexity_score}/10")
        
        # Select pattern
        pattern = await designer.select_pattern(project_meta)
        
        print(f"\n   ✅ 自动选择 Pattern:")
        pattern_type_str = pattern.pattern_type.value if hasattr(pattern.pattern_type, 'value') else str(pattern.pattern_type)
        print(f"   - 类型: {pattern_type_str}")
        print(f"   - 描述: {pattern.description}")
        print(f"   - 最大迭代: {pattern.max_iterations}")
    
    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("🚀 Agent Zero v7.3-v7.6 功能测试")
    print("=" * 70)
    
    results = {}
    
    # v7.3 Tests
    try:
        results['uv_integration'] = await test_uv_integration()
    except Exception as e:
        print(f"\n❌ uv 集成测试失败: {e}")
        results['uv_integration'] = False
    
    try:
        results['trace_visualization'] = await test_trace_visualization()
    except Exception as e:
        print(f"\n❌ Trace 可视化测试失败: {e}")
        results['trace_visualization'] = False
    
    # v7.4 Tests
    try:
        results['pm_inference'] = await test_pm_inference()
    except Exception as e:
        print(f"\n❌ PM 推断测试失败: {e}")
        results['pm_inference'] = False
    
    # v7.5 Tests
    try:
        results['tool_metadata'] = await test_tool_metadata()
    except Exception as e:
        print(f"\n❌ 工具元数据测试失败: {e}")
        results['tool_metadata'] = False
    
    # v7.6 Tests
    try:
        results['pattern_selection'] = await test_pattern_selection()
    except Exception as e:
        print(f"\n❌ Pattern 选择测试失败: {e}")
        results['pattern_selection'] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for s in results.values() if s)
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
