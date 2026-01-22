"""Startup script for Agent Zero system."""

import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.llm import (
    BuilderAPIConfig,
    RuntimeAPIConfig,
    check_all_apis,
    HealthStatus,
)


def print_banner():
    """Print Agent Zero banner."""
    print("=" * 70)
    print("🚀 Agent Zero v6.0 - 智能 Agent 构建工厂")
    print("=" * 70)
    print()


async def check_system_health():
    """Check system health before starting."""
    print("📊 系统健康检查")
    print("-" * 70)
    
    # Load environment variables
    load_dotenv()
    
    # Check Builder API
    builder_config = BuilderAPIConfig(
        provider=os.getenv("BUILDER_PROVIDER", "openai"),
        model=os.getenv("BUILDER_MODEL", "gpt-4o"),
        api_key=os.getenv("BUILDER_API_KEY", ""),
        base_url=os.getenv("BUILDER_BASE_URL"),
        timeout=int(os.getenv("BUILDER_TIMEOUT", "60")),
        max_retries=int(os.getenv("BUILDER_MAX_RETRIES", "3")),
        temperature=float(os.getenv("BUILDER_TEMPERATURE", "0.7")),
    )
    
    # Check Runtime API
    runtime_config = RuntimeAPIConfig(
        provider=os.getenv("RUNTIME_PROVIDER", "openai"),
        model=os.getenv("RUNTIME_MODEL", "gpt-3.5-turbo"),
        api_key=os.getenv("RUNTIME_API_KEY"),
        base_url=os.getenv("RUNTIME_BASE_URL"),
        timeout=int(os.getenv("RUNTIME_TIMEOUT", "30")),
        temperature=float(os.getenv("RUNTIME_TEMPERATURE", "0.7")),
    )
    
    print("\n🔍 正在检查 Builder API...")
    print(f"   提供商: {builder_config.provider}")
    print(f"   模型: {builder_config.model}")
    print(f"   API Key: {'✓ 已配置' if builder_config.api_key else '✗ 缺失'}")
    
    print("\n🔍 正在检查 Runtime API...")
    print(f"   提供商: {runtime_config.provider}")
    print(f"   模型: {runtime_config.model}")
    print(f"   API Key: {'✓ 已配置' if runtime_config.api_key else '✗ 缺失'}")
    
    # Perform health checks
    print("\n⏳ 正在测试连接性...")
    try:
        builder_result, runtime_result = await check_all_apis(
            builder_config, runtime_config
        )
        
        print(f"\n   Builder API: {_get_status_emoji(builder_result.status)} {builder_result.status.value.upper()}")
        print(f"   {builder_result.message}")
        if builder_result.response_time_ms:
            print(f"   响应时间: {builder_result.response_time_ms}ms")
        
        print(f"\n   Runtime API: {_get_status_emoji(runtime_result.status)} {runtime_result.status.value.upper()}")
        print(f"   {runtime_result.message}")
        if runtime_result.response_time_ms:
            print(f"   响应时间: {runtime_result.response_time_ms}ms")
        
        # Check if both are healthy
        both_healthy = (
            builder_result.status == HealthStatus.HEALTHY
            and runtime_result.status == HealthStatus.HEALTHY
        )
        
        print("\n" + "-" * 70)
        if both_healthy:
            print("✅ 所有系统运行正常！")
        else:
            print("⚠️  部分系统运行异常")
            print("\n请检查:")
            print("1. .env 文件中是否配置了正确 API Key")
            print("2. 网络连接状态")
            print("3. API 服务状态")
        
        return both_healthy
        
    except Exception as e:
        print(f"\n❌ 健康检查失败: {e}")
        return False


def _get_status_emoji(status: HealthStatus) -> str:
    """Get emoji for health status."""
    if status == HealthStatus.HEALTHY:
        return "✅"
    elif status == HealthStatus.UNHEALTHY:
        return "❌"
    else:
        return "❓"


def show_menu():
    """Show main menu."""
    print("\n" + "=" * 70)
    print("📋 主菜单")
    print("=" * 70)
    print("\n1. 🏗️  新建 Agent")
    print("2. 📦 查看已生成 Agent")
    print("3. 🔄 重新测试现有 Agent (迭代优化)")  # 🆕 Phase 6
    print("4. 🔧 配置 API 设置")
    print("5. 🧪 运行测试")
    print("6. 📖 查看文档")
    print("7. 🚪 退出")
    print()


async def main():
    """Main entry point."""
    print_banner()
    
    # Check if .env exists
    if not Path(".env").exists():
        print("⚠️  未找到 .env 文件!")
        print("\n请从模板创建 .env 文件:")
        print("   cp .env.template .env")
        print("\n然后编辑 .env 并添加您的 API Keys。")
        print()
        return
    
    # Run health check
    is_healthy = await check_system_health()
    
    if not is_healthy:
        print("\n⚠️  系统健康检查未通过。您可以继续，但")
        print("   部分功能可能无法正常工作。")
        response = input("\n仍要继续吗? (y/n): ")
        if response.lower() != 'y':
            print("\n正在退出...")
            return
    
    # Show menu
    while True:
        show_menu()
        choice = input("请选择 (1-7): ").strip()
        
        # 🔄 辅助函数: 重新加载核心模块
        def reload_core_modules():
            """重新加载核心模块,避免 Python 模块缓存问题"""
            import importlib
            import sys
            
            modules = [
                'src.core.runner',
                'src.core.compiler',
                'src.core.graph_designer',
                'src.core.graph_optimizer',
                'src.core.rag_optimizer',
                'src.core.tool_optimizer',
                'src.core.compiler_optimizer',
            ]
            
            for module_name in modules:
                if module_name in sys.modules:
                    try:
                        importlib.reload(sys.modules[module_name])
                    except Exception as e:
                        # 静默失败,不影响主流程
                        pass
        
        if choice == "1":
            try:
                from src.cli.factory_cli import run_interactive_factory
                await run_interactive_factory()
                
                # 🔄 重新加载核心模块
                reload_core_modules()
                print("✅ 核心模块已更新")
                
            except ImportError as e:
                print(f"❌ 无法加载 Agent 工厂: {e}")
            except Exception as e:
                print(f"❌ 运行工厂时出错: {e}")
        elif choice == "2":
            print("\n📦 已生成的 Agent")
            agents_dir = Path("agents")
            if agents_dir.exists():
                agents = [d for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
                if agents:
                    for i, agent in enumerate(agents, 1):
                        print(f"   {i}. {agent.name}")
                    
                    print("\n请输入序号选择要运行的 Agent (或输入 0 返回):")
                    try:
                        idx = int(input("> "))
                        if idx > 0 and idx <= len(agents):
                            target_agent = agents[idx-1].resolve()
                            print(f"\n🚀 正在启动 {target_agent.name}...")
                            
                            # Decide action
                            print("请选择操作:")
                            print("1. 💬 交互式运行 (python agent.py)")
                            print("2. 🧪 运行测试 (pytest)")
                            action = input("> ").strip()
                            
                            if action == "1":
                                # Run python agent.py
                                install_script = target_agent / ("install.bat" if os.name == "nt" else "install.sh")
                                agent_script = target_agent / "agent.py"
                                
                                # Check venv
                                if os.name == "nt":
                                    venv_python = target_agent / "venv" / "Scripts" / "python.exe"
                                else:
                                    venv_python = target_agent / "venv" / "bin" / "python"
                                    
                                if not venv_python.exists():
                                    print("⚠️  未检测到虚拟环境，尝试使用系统 Python...")
                                    venv_python = "python"
                                
                                import subprocess
                                # Use subprocess to run agent.py in new window or current console
                                # For simplicity, current console but blocking
                                try:
                                    print("-" * 50)
                                    print(f"Executing with: {venv_python}")
                                    subprocess.run([str(venv_python), str(agent_script)], cwd=str(target_agent))
                                except Exception as e:
                                    print(f"执行出错: {e}")
                                    
                            elif action == "2":
                                # Run pytest
                                if os.name == "nt":
                                    venv_python = target_agent / "venv" / "Scripts" / "python.exe"
                                else:
                                    venv_python = target_agent / "venv" / "bin" / "python"
                                    
                                if not venv_python.exists():
                                    venv_python = "python"
                                    
                                test_file = target_agent / "tests" / "test_deepeval.py"
                                if not test_file.exists():
                                    print("⚠️  未找到 DeepEval 测试文件，尝试运行所有测试...")
                                    test_args = []
                                else:
                                    test_args = [str(test_file)]
                                
                                import subprocess
                                try:
                                    cmd = [str(venv_python), "-m", "pytest"] + test_args + ["-v", "-s"]
                                    print(f"Executing: {' '.join(cmd)}")
                                    subprocess.run(cmd, cwd=str(target_agent))
                                except Exception as e:
                                    print(f"测试出错: {e}")
                        elif idx == 0:
                            pass
                        else:
                            print("无效序号")
                    except ValueError:
                        print("无效输入")
                else:
                    print("   (空) 尚未生成任何 Agent")
            else:
                print("   (空) agents 目录不存在")
        elif choice == "3":
            print("\n🔄 重新测试现有 Agent (迭代优化)")
            print("=" * 50)
            
            agents_dir = Path("agents")
            if agents_dir.exists():
                agents = [d for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
                
                if agents:
                    print("\n可用的 Agent:")
                    for i, agent in enumerate(agents, 1):
                        print(f"   {i}. {agent.name}")
                    
                    try:
                        idx = int(input("\n请选择 Agent 编号 (0=取消): ").strip())
                        if 1 <= idx <= len(agents):
                            target_agent = agents[idx - 1]
                            
                            # Load graph.json and metadata
                            graph_file = target_agent / "graph.json"
                            if not graph_file.exists():
                                print(f"❌ 未找到 graph.json: {graph_file}")
                                continue
                            
                            print(f"\n📂 Agent: {target_agent.name}")
                            print(f"📁 路径: {target_agent}")
                            
                            # 🔄 重新加载核心模块 (在导入之前!)
                            reload_core_modules()
                            
                            # Import necessary modules (在 reload 之后导入!)
                            from src.core.agent_factory import AgentFactory
                            from src.core.runner import Runner
                            from src.core.judge import Judge
                            from src.core.report_manager import ReportManager
                            from src.cli.cli_callback import CLICallback
                            from src.schemas.graph_structure import GraphStructure
                            from src.schemas.rag_config import RAGConfig
                            from src.schemas.tools_config import ToolsConfig
                            from src.schemas.project_meta import ProjectMeta
                            from src.config.factory_config import AgentFactoryConfig
                            from src.llm.builder_client import BuilderClient
                            from src.core.graph_designer import GraphDesigner
                            from src.core.simulator import Simulator
                            from src.core.compiler import Compiler
                            from src.core.tool_selector import ToolSelector
                            import json
                            
                            # Load graph
                            with open(graph_file, 'r', encoding='utf-8') as f:
                                graph_data = json.load(f)
                            graph = GraphStructure.model_validate(graph_data)
                            
                            # Load RAG config if exists
                            rag_config = None
                            rag_file = target_agent / "rag_config.json"
                            if rag_file.exists():
                                with open(rag_file, 'r', encoding='utf-8') as f:
                                    rag_data = json.load(f)
                                rag_config = RAGConfig.model_validate(rag_data)
                            
                            # Load Tools config if exists
                            tools_config = None
                            tools_file = target_agent / "tools_config.json"
                            if tools_file.exists():
                                with open(tools_file, 'r', encoding='utf-8') as f:
                                    tools_data = json.load(f)
                                tools_config = ToolsConfig.model_validate(tools_data)
                            
                            # Create minimal metadata
                            pattern_data = graph_data.get('pattern', {})
                            if isinstance(pattern_data, dict):
                                pattern_type = pattern_data.get('pattern_type', 'sequential')
                            else:
                                pattern_type = str(pattern_data)
                            
                            task_type_map = {
                                'sequential': 'rag',
                                'router': 'rag',
                                'reflection': 'analysis',
                                'agent_supervisor': 'custom'
                            }
                            task_type = task_type_map.get(pattern_type, 'rag')
                            
                            meta = ProjectMeta(
                                agent_name=target_agent.name,
                                description=f"Retest of {target_agent.name}",
                                task_type=task_type,
                                has_rag=any('rag' in node.id.lower() for node in graph.nodes),
                                has_tools=False,
                                file_paths=[],
                                user_intent_summary=f"重新测试 {target_agent.name}"
                            )
                            
                            # Initialize components
                            runner = Runner(target_agent)
                            judge = Judge()
                            report_manager = ReportManager(target_agent)
                            callback = CLICallback()
                            
                            # Initialize components for optimization
                            builder_client = BuilderClient.from_env()
                            designer = GraphDesigner(builder_client)
                            simulator = Simulator(builder_client)
                            compiler = Compiler(Path("src/templates"))
                            tool_selector = ToolSelector(builder_client)
                            
                            # Load history to determine next iteration
                            history = report_manager.load_history()
                            start_iteration = len(history.iterations)
                            
                            print(f"\n🔍 当前迭代历史: {len(history.iterations)} 次")
                            print(f"📊 下一次迭代: {start_iteration}")
                            
                            if history.iterations:
                                latest = history.get_latest_iteration()
                                print(f"📈 最新通过率: {latest.pass_rate:.1%}")
                            
                            # 🆕 Ask user if they want to skip testing
                            print("\n选择模式:")
                            print("  1. 运行测试 (约6分钟)")
                            print("  2. 跳过测试,使用上次结果直接优化 (快速)")
                            mode_choice = input("请选择 (1/2): ").strip()
                            
                            skip_testing = (mode_choice == "2")
                            
                            if skip_testing and not history.iterations:
                                print("⚠️  没有历史测试结果,必须先运行测试")
                                skip_testing = False
                            
                            print("\n选择迭代模式:")
                            print("  y.    手动确认 (每次迭代询问)")
                            print("  auto. 自动连续 (自动运行4次, 满分即停)")
                            confirm = input("\n请选择 (y/auto): ").strip().lower()
                            
                            auto_mode = (confirm == 'auto')
                            if confirm not in ['y', 'auto']:
                                print("已取消")
                                continue
                            
                            # 🆕 Automatic Iteration Loop
                            max_iterations = 4 if auto_mode else 5
                            
                            for iteration in range(start_iteration, start_iteration + max_iterations):
                                print("\n" + "=" * 70)
                                print(f"🚀 开始迭代 {iteration} ({'自动模式' if auto_mode else '手动模式'})")
                                print("=" * 70)
                                
                                try:
                                    # 1. Run tests or reuse previous results
                                    if skip_testing and iteration == start_iteration and history.iterations:
                                        # Reuse last iteration's report
                                        callback.on_log("   ⏭️  跳过测试,使用上次结果...")
                                        iteration_report = history.get_latest_iteration()
                                        # Update iteration ID
                                        iteration_report.iteration_id = iteration
                                        iteration_report.timestamp = datetime.now()
                                        
                                        # Create dummy test_results for compatibility
                                        from src.schemas.execution_result import ExecutionStatus, ExecutionResult, TestResult
                                        test_results = ExecutionResult(
                                            overall_status=ExecutionStatus.FAILED if iteration_report.failed_tests > 0 else ExecutionStatus.PASS,
                                            test_results=[
                                                TestResult(
                                                    test_id=tc.test_id,
                                                    status=ExecutionStatus.FAIL if tc.status.upper() in ["FAIL", "FAILED"] else ExecutionStatus.PASS,
                                                    actual_output=tc.actual_output,
                                                    error_message=tc.error_message,
                                                    duration_ms=int(tc.duration_seconds * 1000) if hasattr(tc, 'duration_seconds') else 0
                                                )
                                                for tc in iteration_report.test_cases
                                            ]
                                        )
                                    else:
                                        # Run tests normally
                                        callback.on_log("   ℹ️  执行测试...")
                                        test_results = runner.run_deepeval_tests(timeout=1200)
                                        
                                        # 2. Create report
                                        from src.schemas.test_report import TestCaseReport, IterationReport
                                        from src.schemas.execution_result import ExecutionStatus
                                        
                                        test_cases = []
                                        for test in test_results.test_results:
                                            test_cases.append(TestCaseReport(
                                                test_id=test.test_id,
                                                test_name=test.test_id,
                                                status=test.status.value.upper() if hasattr(test.status, 'value') else str(test.status).upper(),
                                                actual_output=test.actual_output or "",
                                                expected_output="",
                                                error_message=test.error_message,
                                                metrics={},
                                                duration_seconds=test.duration_ms / 1000.0 if test.duration_ms else 0.0
                                            ))
                                        
                                        total_tests = len(test_results.test_results)
                                        passed_tests = sum(1 for t in test_results.test_results if t.status.value in ['pass', 'success'])
                                        failed_tests = total_tests - passed_tests
                                        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
                                        
                                        iteration_report = IterationReport(
                                            iteration_id=iteration,
                                            timestamp=datetime.now(),
                                            agent_name=meta.agent_name,
                                            total_tests=total_tests,
                                            passed_tests=passed_tests,
                                            failed_tests=failed_tests,
                                            skipped_tests=0,
                                            pass_rate=pass_rate,
                                            test_cases=test_cases,
                                            graph_snapshot=graph.model_dump(),
                                            rag_config_snapshot=rag_config.model_dump() if rag_config else None,
                                            tools_config_snapshot=tools_config.model_dump() if tools_config else None
                                        )
                                    
                                    # 3. Save initial report
                                    report_manager.save_iteration_report(iteration_report)
                                    
                                    # 4. Analyze with Judge
                                    judge_result = None
                                    analysis = None
                                    
                                    if test_results.overall_status != ExecutionStatus.SKIPPED:
                                        judge_result = judge.analyze_result(test_results)
                                        iteration_report.fix_target = judge_result.fix_target.value if judge_result.fix_target else None
                                        
                                        # 5. 🆕 LLM 智能分析
                                        if judge_result.error_type != "none":
                                            callback.on_log("   🤖 LLM 智能分析中...")
                                            
                                            from src.core.test_analyzer import TestAnalyzer
                                            test_analyzer = TestAnalyzer(builder_client)
                                            
                                            current_config = {
                                                "graph": graph.model_dump(),
                                                "rag": rag_config.model_dump() if rag_config else None,
                                                "tools": tools_config.model_dump() if tools_config else None
                                            }
                                            
                                            try:
                                                analysis = await test_analyzer.analyze_test_report(
                                                    iteration_report,
                                                    current_config
                                                )
                                                
                                                # Enhanced feedback
                                                enhanced_feedback = (
                                                    f"{judge_result.feedback}\n\n"
                                                    f"🤖 AI 分析:\n"
                                                    f"  主要问题: {analysis.primary_issue}\n"
                                                    f"  根本原因: {analysis.root_cause}\n"
                                                    f"  预计成功率: {analysis.estimated_success_rate:.1%}\n"
                                                )
                                                
                                                if analysis.fix_strategy:
                                                    enhanced_feedback += "\n💡 修复策略:\n"
                                                    for i, step in enumerate(analysis.fix_strategy[:3], 1):
                                                        enhanced_feedback += (
                                                            f"  {i}. [{step.priority.upper()}] {step.action}\n"
                                                            f"     目标: {step.target}\n"
                                                        )
                                                
                                                iteration_report.judge_feedback = enhanced_feedback
                                                
                                                # 🔍 Debug: 显示修复策略详情
                                                callback.on_log(f"\n🔍 [DEBUG] 修复策略详情:")
                                                callback.on_log(f"  策略总数: {len(analysis.fix_strategy)}")
                                                for i, step in enumerate(analysis.fix_strategy, 1):
                                                    callback.on_log(f"  策略 {i}: target={step.target}, priority={step.priority}")
                                                    callback.on_log(f"         action={step.action[:80]}...")
                                            except Exception as e:
                                                callback.on_log(f"   ⚠️ LLM 分析失败: {str(e)}")
                                                iteration_report.judge_feedback = judge_result.feedback
                                        else:
                                            iteration_report.judge_feedback = judge_result.feedback if judge_result else ""
                                        
                                        # Update and save report
                                        report_manager.save_iteration_report(iteration_report)
                                    
                                    # 6. Display summary
                                    summary = report_manager.generate_summary(iteration)
                                    print(summary)
                                    
                                    # 7. Check pass rate threshold (BREAK ON 100%)
                                    if iteration_report.pass_rate >= 1.0:
                                        callback.on_log("✅ 测试通过率达标 (100%), 停止迭代")
                                        break
                                    
                                    # 8. 🆕 Apply fix strategies
                                    if analysis and analysis.fix_strategy:
                                        callback.on_log("🔧 开始执行修复策略...")
                                        
                                        for fix_step in analysis.fix_strategy[:3]:
                                            # 🔍 Debug: 显示当前步骤详情
                                            callback.on_log(f"\n  📍 执行步骤 {fix_step.step}: {fix_step.action[:60]}...")
                                            callback.on_log(f"     [DEBUG] target={fix_step.target}, priority={fix_step.priority}")
                                            
                                            try:
                                                if fix_step.target == "rag_builder" and rag_config:
                                                    callback.on_log(f"     [DEBUG] 进入 RAGOptimizer 分支")
                                                    from src.core.rag_optimizer import RAGOptimizer
                                                    rag_optimizer = RAGOptimizer(builder_client)
                                                    
                                                    new_rag_config = await rag_optimizer.optimize_config(
                                                        rag_config,
                                                        analysis,
                                                        iteration_report
                                                    )
                                                    
                                                    callback.on_log(
                                                        f"    ✅ RAG 优化: k_retrieval {rag_config.k_retrieval} → {new_rag_config.k_retrieval}"
                                                    )
                                                    
                                                    rag_config = new_rag_config
                                                    
                                                    # 💾 保存配置到文件
                                                    import json
                                                    rag_config_file = target_agent / "rag_config.json"
                                                    with open(rag_config_file, 'w', encoding='utf-8') as f:
                                                        json.dump(rag_config.model_dump(), f, indent=2, ensure_ascii=False)
                                                    callback.on_log(f"    💾 已保存配置到 {rag_config_file.name}")
                                                    
                                                    compiler.compile(meta, graph, rag_config, tools_config, target_agent)
                                                
                                                elif fix_step.target == "rag_builder" and not rag_config:
                                                    callback.on_log(f"     [DEBUG] 跳过 RAGOptimizer: rag_config 不存在")
                                                
                                                elif fix_step.target == "tool_selector" and tools_config:
                                                    callback.on_log(f"     [DEBUG] 进入 ToolOptimizer 分支")
                                                    from src.core.tool_optimizer import ToolOptimizer
                                                    tool_optimizer = ToolOptimizer(builder_client, tool_selector)
                                                    
                                                    new_tools_config = await tool_optimizer.optimize_tools(
                                                        tools_config,
                                                        analysis,
                                                        meta
                                                    )
                                                    
                                                    callback.on_log(
                                                        f"    ✅ Tools 优化: {tools_config.enabled_tools} → {new_tools_config.enabled_tools}"
                                                    )
                                                    
                                                    tools_config = new_tools_config
                                                
                                                elif fix_step.target == "tool_selector" and not tools_config:
                                                    callback.on_log(f"     [DEBUG] 跳过 ToolOptimizer: tools_config 不存在")
                                                    compiler.compile(meta, graph, rag_config, tools_config, target_agent)
                                                
                                                elif fix_step.target == "graph_designer":
                                                    callback.on_log(f"     [DEBUG] 进入 GraphOptimizer 分支")
                                                    from src.core.graph_optimizer import GraphOptimizer
                                                    graph_optimizer = GraphOptimizer(designer, simulator)
                                                    
                                                    new_graph, sim_result = await graph_optimizer.optimize_graph(
                                                        graph,
                                                        analysis,
                                                        meta
                                                    )
                                                    
                                                    sim_status = "✅ 通过" if not sim_result.has_errors() else "⚠️ 仍有问题"
                                                    callback.on_log(f"    ✅ Graph 优化完成, 仿真结果: {sim_status}")
                                                    
                                                    graph = new_graph
                                                    compiler.compile(meta, graph, rag_config, tools_config, target_agent)
                                                
                                                elif fix_step.target == "compiler":
                                                    callback.on_log(f"     [DEBUG] 进入 CompilerOptimizer 分支")
                                                    from src.core.compiler_optimizer import CompilerOptimizer
                                                    compiler_optimizer = CompilerOptimizer(compiler)
                                                    
                                                    error_msg = test_results.stderr or ""
                                                    success = await compiler_optimizer.optimize_dependencies(
                                                        target_agent,
                                                        analysis,
                                                        error_msg
                                                    )
                                                    
                                                    if success:
                                                        callback.on_log(f"    ✅ Compiler 优化: 已更新依赖项")
                                            
                                                else:
                                                    callback.on_log(f"     [DEBUG] 未匹配任何优化器分支")
                                                    callback.on_log(f"     [DEBUG] target='{fix_step.target}', rag_config={rag_config is not None}, tools_config={tools_config is not None}")
                                            
                                            except Exception as e:
                                                callback.on_log(f"    ⚠️ 修复步骤失败: {str(e)}")
                                                import traceback
                                                callback.on_log(f"    [DEBUG] 异常详情: {traceback.format_exc()[:200]}")
                                    
                                    # 9. Iteration Control
                                    if iteration < start_iteration + max_iterations - 1:
                                        if auto_mode:
                                            callback.on_log(f"\n🤖 [Auto] 3秒后开始下一次迭代...")
                                            import time
                                            time.sleep(3)
                                        else:
                                            confirm = input("\n继续下一次迭代? (y/n): ").strip().lower()
                                            if confirm != 'y':
                                                callback.on_log("用户选择停止迭代")
                                                break
                                
                                except Exception as e:
                                    print(f"\n❌ 迭代 {iteration} 失败: {e}")
                                    import traceback
                                    traceback.print_exc()
                                    break
                                    # 1. Run tests or reuse previous results
                                    if skip_testing and iteration == start_iteration and history.iterations:
                                        # Reuse last iteration's report
                                        callback.on_log("   ⏭️  跳过测试,使用上次结果...")
                                        iteration_report = history.get_latest_iteration()
                                        # Update iteration ID
                                        iteration_report.iteration_id = iteration
                                        iteration_report.timestamp = datetime.now()
                                        
                                        # Create dummy test_results for compatibility
                                        from src.schemas.execution_result import ExecutionStatus, ExecutionResult, TestResult
                                        test_results = ExecutionResult(
                                            overall_status=ExecutionStatus.FAILED if iteration_report.failed_tests > 0 else ExecutionStatus.PASS,
                                            test_results=[
                                                TestResult(
                                                    test_id=tc.test_id,
                                                    status=ExecutionStatus.FAIL if tc.status.upper() in ["FAIL", "FAILED"] else ExecutionStatus.PASS,
                                                    actual_output=tc.actual_output,
                                                    error_message=tc.error_message,
                                                    duration_ms=int(tc.duration_seconds * 1000) if hasattr(tc, 'duration_seconds') else 0
                                                )
                                                for tc in iteration_report.test_cases
                                            ]
                                        )
                                    else:
                                        # Run tests normally
                                        callback.on_log("   ℹ️  执行测试...")
                                        test_results = runner.run_deepeval_tests(timeout=600)
                                        
                                        # 2. Create report
                                        from src.schemas.test_report import TestCaseReport, IterationReport
                                        from src.schemas.execution_result import ExecutionStatus
                                        
                                        test_cases = []
                                        for test in test_results.test_results:
                                            test_cases.append(TestCaseReport(
                                                test_id=test.test_id,
                                                test_name=test.test_id,
                                                status=test.status.value.upper() if hasattr(test.status, 'value') else str(test.status).upper(),
                                                actual_output=test.actual_output or "",
                                                expected_output="",
                                                error_message=test.error_message,
                                                metrics={},
                                                duration_seconds=test.duration_ms / 1000.0 if test.duration_ms else 0.0
                                            ))
                                        
                                        total_tests = len(test_results.test_results)
                                        passed_tests = sum(1 for t in test_results.test_results if t.status.value in ['pass', 'success'])
                                        failed_tests = total_tests - passed_tests
                                        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
                                        
                                        iteration_report = IterationReport(
                                            iteration_id=iteration,
                                            timestamp=datetime.now(),
                                            agent_name=meta.agent_name,
                                            total_tests=total_tests,
                                            passed_tests=passed_tests,
                                            failed_tests=failed_tests,
                                            skipped_tests=0,
                                            pass_rate=pass_rate,
                                            test_cases=test_cases,
                                            graph_snapshot=graph.model_dump(),
                                            rag_config_snapshot=rag_config.model_dump() if rag_config else None,
                                            tools_config_snapshot=tools_config.model_dump() if tools_config else None
                                        )
                                    
                                    # 3. Save initial report
                                    report_manager.save_iteration_report(iteration_report)
                                    
                                    # 4. Analyze with Judge
                                    judge_result = None
                                    analysis = None
                                    
                                    if test_results.overall_status != ExecutionStatus.SKIPPED:
                                        judge_result = judge.analyze_result(test_results)
                                        iteration_report.fix_target = judge_result.fix_target.value if judge_result.fix_target else None
                                        
                                        # 5. 🆕 LLM 智能分析
                                        if judge_result.error_type != "none":
                                            callback.on_log("   🤖 LLM 智能分析中...")
                                            
                                            from src.core.test_analyzer import TestAnalyzer
                                            test_analyzer = TestAnalyzer(builder_client)
                                            
                                            current_config = {
                                                "graph": graph.model_dump(),
                                                "rag": rag_config.model_dump() if rag_config else None,
                                                "tools": tools_config.model_dump() if tools_config else None
                                            }
                                            
                                            try:
                                                analysis = await test_analyzer.analyze_test_report(
                                                    iteration_report,
                                                    current_config
                                                )
                                                
                                                # Enhanced feedback
                                                enhanced_feedback = (
                                                    f"{judge_result.feedback}\n\n"
                                                    f"🤖 AI 分析:\n"
                                                    f"  主要问题: {analysis.primary_issue}\n"
                                                    f"  根本原因: {analysis.root_cause}\n"
                                                    f"  预计成功率: {analysis.estimated_success_rate:.1%}\n"
                                                )
                                                
                                                if analysis.fix_strategy:
                                                    enhanced_feedback += "\n💡 修复策略:\n"
                                                    for i, step in enumerate(analysis.fix_strategy[:3], 1):
                                                        enhanced_feedback += (
                                                            f"  {i}. [{step.priority.upper()}] {step.action}\n"
                                                            f"     目标: {step.target}\n"
                                                        )
                                                
                                                iteration_report.judge_feedback = enhanced_feedback
                                                
                                                # 🔍 Debug: 显示修复策略详情
                                                callback.on_log(f"\n🔍 [DEBUG] 修复策略详情:")
                                                callback.on_log(f"  策略总数: {len(analysis.fix_strategy)}")
                                                for i, step in enumerate(analysis.fix_strategy, 1):
                                                    callback.on_log(f"  策略 {i}: target={step.target}, priority={step.priority}")
                                                    callback.on_log(f"         action={step.action[:80]}...")
                                            except Exception as e:
                                                callback.on_log(f"   ⚠️ LLM 分析失败: {str(e)}")
                                                iteration_report.judge_feedback = judge_result.feedback
                                        else:
                                            iteration_report.judge_feedback = judge_result.feedback if judge_result else ""
                                        
                                        # Update and save report
                                        report_manager.save_iteration_report(iteration_report)
                                    
                                    # 6. Display summary
                                    summary = report_manager.generate_summary(iteration)
                                    print(summary)
                                    
                                    # 7. Check pass rate threshold
                                    if iteration_report.pass_rate >= 0.9:
                                        callback.on_log("✅ 测试通过率达标 (≥90%), 停止迭代")
                                        break
                                    
                                    # 8. 🆕 Apply fix strategies
                                    if analysis and analysis.fix_strategy:
                                        callback.on_log("🔧 开始执行修复策略...")
                                        
                                        for fix_step in analysis.fix_strategy[:3]:
                                            # 🔍 Debug: 显示当前步骤详情
                                            callback.on_log(f"\n  📍 执行步骤 {fix_step.step}: {fix_step.action[:60]}...")
                                            callback.on_log(f"     [DEBUG] target={fix_step.target}, priority={fix_step.priority}")
                                            
                                            try:
                                                if fix_step.target == "rag_builder" and rag_config:
                                                    callback.on_log(f"     [DEBUG] 进入 RAGOptimizer 分支")
                                                    from src.core.rag_optimizer import RAGOptimizer
                                                    rag_optimizer = RAGOptimizer(builder_client)
                                                    
                                                    new_rag_config = await rag_optimizer.optimize_config(
                                                        rag_config,
                                                        analysis,
                                                        iteration_report
                                                    )
                                                    
                                                    callback.on_log(
                                                        f"    ✅ RAG 优化: k_retrieval {rag_config.k_retrieval} → {new_rag_config.k_retrieval}"
                                                    )
                                                    
                                                    rag_config = new_rag_config
                                                    
                                                    # 💾 保存配置到文件
                                                    import json
                                                    rag_config_file = target_agent / "rag_config.json"
                                                    with open(rag_config_file, 'w', encoding='utf-8') as f:
                                                        json.dump(rag_config.model_dump(), f, indent=2, ensure_ascii=False)
                                                    callback.on_log(f"    💾 已保存配置到 {rag_config_file.name}")
                                                    
                                                    compiler.compile(meta, graph, rag_config, tools_config, target_agent)
                                                
                                                elif fix_step.target == "rag_builder" and not rag_config:
                                                    callback.on_log(f"     [DEBUG] 跳过 RAGOptimizer: rag_config 不存在")
                                                
                                                elif fix_step.target == "tool_selector" and tools_config:
                                                    callback.on_log(f"     [DEBUG] 进入 ToolOptimizer 分支")
                                                    from src.core.tool_optimizer import ToolOptimizer
                                                    tool_optimizer = ToolOptimizer(builder_client, tool_selector)
                                                    
                                                    new_tools_config = await tool_optimizer.optimize_tools(
                                                        tools_config,
                                                        analysis,
                                                        meta
                                                    )
                                                    
                                                    callback.on_log(
                                                        f"    ✅ Tools 优化: {tools_config.enabled_tools} → {new_tools_config.enabled_tools}"
                                                    )
                                                    
                                                    tools_config = new_tools_config
                                                
                                                elif fix_step.target == "tool_selector" and not tools_config:
                                                    callback.on_log(f"     [DEBUG] 跳过 ToolOptimizer: tools_config 不存在")
                                                    compiler.compile(meta, graph, rag_config, tools_config, target_agent)
                                                
                                                elif fix_step.target == "graph_designer":
                                                    callback.on_log(f"     [DEBUG] 进入 GraphOptimizer 分支")
                                                    from src.core.graph_optimizer import GraphOptimizer
                                                    graph_optimizer = GraphOptimizer(designer, simulator)
                                                    
                                                    new_graph, sim_result = await graph_optimizer.optimize_graph(
                                                        graph,
                                                        analysis,
                                                        meta
                                                    )
                                                    
                                                    sim_status = "✅ 通过" if not sim_result.has_errors() else "⚠️ 仍有问题"
                                                    callback.on_log(f"    ✅ Graph 优化完成, 仿真结果: {sim_status}")
                                                    
                                                    graph = new_graph
                                                    compiler.compile(meta, graph, rag_config, tools_config, target_agent)
                                                
                                                elif fix_step.target == "compiler":
                                                    callback.on_log(f"     [DEBUG] 进入 CompilerOptimizer 分支")
                                                    from src.core.compiler_optimizer import CompilerOptimizer
                                                    compiler_optimizer = CompilerOptimizer(compiler)
                                                    
                                                    error_msg = test_results.stderr or ""
                                                    success = await compiler_optimizer.optimize_dependencies(
                                                        target_agent,
                                                        analysis,
                                                        error_msg
                                                    )
                                                    
                                                    if success:
                                                        callback.on_log(f"    ✅ Compiler 优化: 已更新依赖项")
                                            
                                                else:
                                                    callback.on_log(f"     [DEBUG] 未匹配任何优化器分支")
                                                    callback.on_log(f"     [DEBUG] target='{fix_step.target}', rag_config={rag_config is not None}, tools_config={tools_config is not None}")
                                            
                                            except Exception as e:
                                                callback.on_log(f"    ⚠️ 修复步骤失败: {str(e)}")
                                                import traceback
                                                callback.on_log(f"    [DEBUG] 异常详情: {traceback.format_exc()[:200]}")
                                    
                                    # 9. User confirmation
                                    if iteration < start_iteration + max_iterations - 1:
                                        confirm = input("\n继续下一次迭代? (y/n): ").strip().lower()
                                        if confirm != 'y':
                                            callback.on_log("用户选择停止迭代")
                                            break
                                
                                except Exception as e:
                                    print(f"\n❌ 迭代 {iteration} 失败: {e}")
                                    import traceback
                                    traceback.print_exc()
                                    break
                            
                            # Final summary
                            print("\n" + "=" * 70)
                            evolution_summary = report_manager.generate_evolution_summary()
                            print(evolution_summary)
                            print(f"\n✅ 迭代优化完成!")
                            print(f"📊 报告已保存到: {target_agent / '.reports'}")
                        
                        elif idx == 0:
                            print("已取消")
                        else:
                            print("无效序号")
                    except ValueError as e:
                        print(f"无效输入: {e}")
                        import traceback
                        traceback.print_exc()
                    except Exception as e:
                        print(f"错误: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print("   (空) 尚未生成任何 Agent")
            else:
                print("   (空) agents 目录不存在")
        
        elif choice == "4":
            print("\n🔧 API 配置")
            print("   请编辑 .env 文件以配置 API 设置")
            print(f"   位置: {Path('.env').absolute()}")
        elif choice == "5":
            print("\n🧪 正在运行测试...")
            print("   python tests/e2e/test_phase1_hello_world.py")
        elif choice == "6":
            print("\n📖 文档")
            print("   README.md - 项目概览")
            print("   Agent Zero项目计划书.md - 项目计划")
            print("   Agent_Zero_详细实施计划.md - 实施细节")
        elif choice == "7":
            print("\n👋 再见!")
            break
        else:
            print("\n❌ 无效选项，请选择 1-7。")
        
        input("\n按回车键继续...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
