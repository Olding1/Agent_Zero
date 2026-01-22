import asyncio
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..llm.builder_client import BuilderClient
from ..config.factory_config import AgentFactoryConfig
from ..schemas.project_meta import ProjectMeta
from ..schemas.graph_structure import GraphStructure
from ..schemas.rag_config import RAGConfig
from ..schemas.tools_config import ToolsConfig
from ..schemas.agent_result import AgentResult
from ..schemas.execution_result import ExecutionResult, ExecutionStatus
from ..schemas.judge_result import FixTarget, JudgeResult
from ..schemas.test_report import IterationReport, TestCaseReport

from .progress_callback import ProgressCallback
from .pm import PM
from .graph_designer import GraphDesigner
from .simulator import Simulator
from .compiler import Compiler
from .test_generator import TestGenerator
# Runner is imported on-demand to support hot reload
from .judge import Judge
from .rag_builder import RAGBuilder
from .tool_selector import ToolSelector
from .report_manager import ReportManager
from ..utils.git_utils import GitUtils

class AgentFactory:
    """Agent 工厂 - 编排所有组件生成 Agent"""
    
    def __init__(
        self,
        config: Optional[AgentFactoryConfig] = None,
        callback: Optional[ProgressCallback] = None
    ):
        self.config = config or AgentFactoryConfig.from_env()
        self.callback = callback
        
        # Initialize Core Components
        self.builder_client = BuilderClient.from_env()
        # Note: BuilderClient.from_env() logic might be needed if not default
        
        self.pm = PM(self.builder_client)
        self.designer = GraphDesigner(self.builder_client)
        self.simulator = Simulator(self.builder_client)
        self.compiler = Compiler(self.config.template_dir)
        self.test_gen = TestGenerator(self.builder_client)
        self.judge = Judge()
        self.rag_builder = RAGBuilder(self.builder_client)
        self.tool_selector = ToolSelector(self.builder_client)
        
    def set_callback(self, callback: ProgressCallback):
        self.callback = callback
        
    async def create_agent(
        self,
        user_input: str,
        file_paths: Optional[List[str]] = None,
        output_dir: Optional[Path] = None
    ) -> AgentResult:
        """
        全流程构建 Agent
        """
        start_time = time.time()
        
        # Initialize Result (Temporary)
        meta = ProjectMeta(
            agent_name="unknown",
            description="",
            user_intent_summary="",
            has_rag=False,
            task_type="chat"
        )
        agent_dir = Path("./temp") # will be updated
        graph = None
        
        try:
            # Step 1: PM Analysis
            meta = await self._step_pm_analysis(user_input, file_paths)
            
            # Update agent_dir based on agent_name
            agent_dir = output_dir or (self.config.output_base_dir / meta.agent_name)
            
            # Step 2: RAG & Tools
            rag_config, tools_config = await self._step_resources(meta)
            
            # Design & Review Loop
            sim_result = None
            feedback = None
            
            for review_round in range(5): # Limit review rounds
                if review_round == 0:
                    # Initial Design Loop
                    graph, sim_result = await self._design_loop(meta, rag_config, tools_config)
                else:
                    # Refine based on user feedback
                    if self.callback and feedback:
                        self.callback.on_log(f"根据用户反馈调整蓝图 (Round {review_round}): {feedback[:50]}...")
                        
                        # Use fix_logic with instructions
                        graph = await self.designer.fix_logic(graph, sim_result, feedback)
                        
                        # Re-simulate
                        if self.callback:
                            self.callback.on_log("重新运行仿真...")
                        sim_result = await self.simulator.simulate(graph, "Test Input")
                
                # Step 4: Blueprint Review (Interactive)
                if self.config.interactive and self.callback:
                     approved, feedback = self.callback.on_blueprint_review(graph, sim_result)
                     if approved:
                         break
                     
                     if not feedback:
                         # Rejected without feedback -> Abort
                         if self.callback:
                             self.callback.on_log("用户取消构建 (Review Rejected)")
                         return AgentResult(
                             agent_name=meta.agent_name,
                             agent_dir=agent_dir,
                             project_meta=meta,
                             graph=graph,
                             success=False
                         )
                else:
                    # No interactivity, assume approved
                    break

            # Step 5: Build & Evolve
            final_result = await self._build_and_evolve_loop(
                meta, graph, rag_config, tools_config, agent_dir
            )
            
            final_result.total_time = time.time() - start_time
            
            if self.callback:
                if final_result.success:
                    self.callback.on_log(f"Agent 构建成功! 位于: {agent_dir}")
                else:
                    self.callback.on_log("Agent 构建未完全通过测试。")
                    
            return final_result
            
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            if self.callback:
                self.callback.on_step_error("Create Agent", e)
            
            # Return failed result
            return AgentResult(
                agent_name=meta.agent_name if 'meta' in locals() else "unknown",
                agent_dir=agent_dir if 'agent_dir' in locals() else Path("./error"),
                project_meta=meta if 'meta' in locals() else ProjectMeta(agent_name="error", description=str(e), user_intent_summary="", has_rag=False, task_type="chat"),
                graph=graph if 'graph' in locals() and graph else None,
                success=False,
                judge_feedback=JudgeResult(error_type="runtime", fix_target="manual", feedback=error_msg, suggestions=[])
            )

    async def _step_pm_analysis(self, user_input: str, file_paths: Optional[List[str]]) -> ProjectMeta:
        """Step 1: PM 需求分析"""
        if self.callback:
            self.callback.on_step_start("PM Agent", 1, 5)
            self.callback.on_log(f"分析用户需求: {user_input[:50]}...")
            
        # Analyze requirements
        from pathlib import Path
        paths = [Path(p) for p in file_paths] if file_paths else []
        # Use clarification loop
        meta = await self.pm.analyze_with_clarification_loop(
            user_input, 
            file_paths=paths
        )
        
        # Handle clarification needed status
        while meta.status == "clarifying" and self.callback:
            # Ask user for clarification
            self.callback.on_clarification_needed(meta.clarification_questions)
            
            # Since CLI callback doesn't return answers directly (it just prints),
            # we need to implement input collection here or assume callback handles it?
            # Actually, standard callback interface doesn't return value.
            # But we are in an async loop in factory.
            # Let's implementation input collection here via stdin using input() is bad for library code.
            # Ideally callback should return answers. But Callback signature is void or simple.
            # Let's assume we modify callback interface or handle it here if it's CLI.
            # A better approach: 
            # In CLI usage, we might not easily inject input back.
            # Let's look at how we can get answers.
            
            # For now, let's just proceed with simple collected answers from CLI if possible.
            # Since we can't easily change the architecture now, let's input() here if CLI.
            # But self.callback is generic.
            
            # Let's iterate using a simple blocking input for now, printing via callback.
            answers = {}
            print("\n(请输入回答，按回车确认):")
            for q in meta.clarification_questions:
                try:
                    ans = input(f"Q: {q}\nA: ")
                except EOFError:
                    print(f"Q: {q}\nA: (Auto-skipped due to EOF)")
                    ans = "No specific preference"
                answers[q] = ans
            
            # Refine
            meta = await self.pm.refine_with_clarification(meta, answers)
            
            # Re-estimate complexity and plan after refinement
            complexity = await self.pm.estimate_complexity(user_input, bool(paths))
            meta.complexity_score = complexity
            if complexity >= 4:
                execution_plan = await self.pm.create_execution_plan(meta)
                meta.execution_plan = execution_plan
            
            meta.status = "ready" # Assume ready after one round for now to avoid infinite loops in strict mode
        
        if self.callback:
            self.callback.on_step_complete("PM Agent", meta)
            
        return meta

    async def _step_resources(self, meta: ProjectMeta) -> tuple[Optional[RAGConfig], Optional[ToolsConfig]]:
        """Step 2: 资源准备 (RAG & Tools)"""
        if self.callback:
            self.callback.on_step_start("Resource Config", 2, 5)
            
        rag_config = None
        tools_config = None
        
        # Parallel execution if possible, for now sequential
        if meta.has_rag:
            if self.callback:
                self.callback.on_log("配置 RAG 系统...")
            
            # Create a DataProfile on the fly or just rely on file paths
            # RAGBuilder normally needs DataProfile, but specific method signature might vary.
            # RAGBuilder.design_rag_strategy takes DataProfile.
            # We need to profile first if we want to use design_rag_strategy.
            # Or use RAGBuilder.build_config if it existed (my skeleton had it, but file didn't).
            # The file has design_rag_strategy(profile).
            # So we need to profile data first.
            from .profiler import Profiler
            profiler = Profiler()
            if meta.file_paths:
                from pathlib import Path
                paths = [Path(p) for p in meta.file_paths]
                profile = profiler.analyze(paths)
                rag_config = await self.rag_builder.design_rag_strategy(profile)
        
        # Tools
        if self.callback:
            self.callback.on_log("选择工具...")
        tools_config = await self.tool_selector.select_tools(meta)
        
        if self.callback:
            self.callback.on_step_complete("Resource Config", {"rag": bool(rag_config), "tools": len(tools_config.enabled_tools) if tools_config else 0})
            
        return rag_config, tools_config

    async def _design_loop(
        self, 
        meta: ProjectMeta, 
        rag_config: Optional[RAGConfig], 
        tools_config: Optional[ToolsConfig]
    ) -> tuple[GraphStructure, Any]:
        """Step 3: 设计与仿真闭环"""
        if self.callback:
            self.callback.on_step_start("Design & Simulation", 3, 5)
            
        graph = None
        sim_result = None
        
        for attempt in range(self.config.max_design_retries):
            if attempt == 0:
                # First design
                if self.callback:
                    self.callback.on_log("生成初始蓝图...")
                graph = await self.designer.design_graph(meta, tools_config, rag_config)
            else:
                # Refine design
                if self.callback:
                    self.callback.on_log(f"优化蓝图 (第 {attempt} 次迭代)...")
                # Using fix_logic with previous simulation result
                graph = await self.designer.fix_logic(graph, sim_result)
                
            # Simulate
            if self.callback:
                self.callback.on_log("运行沙盘推演...")
                
            # Create a sample input for simulation
            # Create a sample input for simulation based on task type
            if meta.has_rag:
                sample_input = "Agent Zero 是什么项目？"  # Trigger RAG keywords
            elif meta.task_type == "search":
                sample_input = "搜索一下最新的 AI 新闻"
            else:
                sample_input = "你好，请介绍一下你自己"
            sim_result = await self.simulator.simulate(graph, sample_input)
            
            # Check for critical errors
            if not sim_result.has_errors():
                if self.callback:
                    self.callback.on_log("仿真通过 ✅")
                break
            else:
                if self.callback:
                    self.callback.on_log(f"仿真发现问题: {[i.issue_type for i in sim_result.issues]}")
        
        if self.callback:
            self.callback.on_step_complete("Design & Simulation", sim_result)
            
        return graph, sim_result

    async def _build_and_evolve_loop(
        self, 
        meta: ProjectMeta, 
        graph: GraphStructure, 
        rag_config: Optional[RAGConfig], 
        tools_config: Optional[ToolsConfig], 
        agent_dir: Path
    ) -> AgentResult:
        """Step 5: 构建与进化闭环"""
        if self.callback:
            self.callback.on_step_start("Build & Evolve", 5, 5)
            
        final_result = AgentResult(
            agent_name=meta.agent_name,
            agent_dir=agent_dir,
            project_meta=meta,
            graph=graph,
            rag_config=rag_config,
            tools_config=tools_config
        )
        
        # Initial Compile
        if self.callback:
            self.callback.on_log("生成代码...")
        compile_result = self.compiler.compile(meta, graph, rag_config, tools_config, agent_dir)
        final_result.generated_files = compile_result.generated_files
        
        if not compile_result.success:
            if self.callback:
                self.callback.on_step_error("Compilation", Exception(compile_result.error_message))
            return final_result
            
        # Init Git
        if self.config.enable_git:
            git = GitUtils(agent_dir)
            git.init_repo()
            git.commit("Initial generation")

        # 🆕 Phase 6: Initialize ReportManager
        report_manager = ReportManager(agent_dir)
        
        # Instantiate Runner for this agent
        # 🔄 延迟导入 Runner,确保使用最新代码
        from .runner import Runner
        runner = Runner(agent_dir)
            
        # Evolution Loop
        for iteration in range(self.config.max_build_retries):
            final_result.iteration_count = iteration
            
            # 1. Generate Tests
            if self.callback:
                self.callback.on_log(f"生成测试 (Iter {iteration})...")
            
            test_code = await self.test_gen.generate_deepeval_tests(meta, rag_config)
            
            # Extract test questions for display using simple regex
            import re
            questions = re.findall(r'input="(.*?)",', test_code)
            if self.callback and questions:
                self.callback.on_log(f"已生成 {len(questions)} 个测试用例:")
                for i, q in enumerate(questions[:3], 1): # Show max 3
                    self.callback.on_log(f"  {i}. {q[:50]}...")
            
            # Write test file
            test_dir = agent_dir / "tests"
            test_dir.mkdir(exist_ok=True)
            (test_dir / "test_deepeval.py").write_text(test_code, encoding="utf-8")
            
            # 2. Run Tests
            should_run_tests = False
            if self.callback:
                if self.callback.on_install_request():
                    self.callback.on_log("正在安装依赖 (请耐心等待)...")
                    if runner.setup_environment():
                        self.callback.on_log("依赖安装完成。")
                        
                        # 🔄 重新加载 Runner 模块并重新创建实例
                        # 因为 install.bat 可能修改了代码
                        import importlib
                        import sys
                        if 'src.core.runner' in sys.modules:
                            importlib.reload(sys.modules['src.core.runner'])
                        from .runner import Runner
                        runner = Runner(agent_dir)  # 重新创建实例
                        self.callback.on_log("✅ 已更新 Runner 模块")
                        
                        should_run_tests = True
                    else:
                        self.callback.on_log("依赖安装失败，跳过测试。")
                else:
                    self.callback.on_log("跳过安装，仅生成代码。")
            
            if should_run_tests:
                if self.callback:
                    self.callback.on_log("执行测试...")
                # Ensure DeepEval is installed/ready is handled by Runner internally or Compiler pre-install
                test_results = runner.run_deepeval_tests()
                final_result.test_results = test_results
                
                # 🆕 Debug: Log test results
                if self.callback:
                    self.callback.on_log(f"🔍 [调试] 测试执行状态: {test_results.overall_status}")
                    self.callback.on_log(f"🔍 [调试] 测试结果数量: {len(test_results.test_results)}")
                    if hasattr(test_results, 'stderr') and test_results.stderr:
                        stderr_preview = test_results.stderr[:200].replace('\n', ' ')
                        self.callback.on_log(f"🔍 [调试] 错误输出: {stderr_preview}...")
                    if hasattr(test_results, 'stdout') and test_results.stdout:
                        stdout_preview = test_results.stdout[:200].replace('\n', ' ')
                        self.callback.on_log(f"🔍 [调试] 标准输出: {stdout_preview}...")
            else:
                 # Create a dummy skipped result to avoid attribution errors later
                 final_result.test_results = ExecutionResult(overall_status=ExecutionStatus.SKIPPED, test_results=[], stderr="User skipped installation")
            
            # 🆕 Phase 6: Create Iteration Report
            if self.callback:
                self.callback.on_log(f"🔍 [调试] 创建迭代报告 (迭代 {iteration})...")
            
            iteration_report = self._create_iteration_report(
                iteration=iteration,
                agent_name=meta.agent_name,
                test_results=final_result.test_results,
                graph=graph,
                rag_config=rag_config,
                tools_config=tools_config
            )
            
            # 🆕 Debug: Log report details
            if self.callback:
                self.callback.on_log(f"🔍 [调试] 报告创建完成:")
                self.callback.on_log(f"   - 总测试数: {iteration_report.total_tests}")
                self.callback.on_log(f"   - 通过: {iteration_report.passed_tests}")
                self.callback.on_log(f"   - 失败: {iteration_report.failed_tests}")
                self.callback.on_log(f"   - 测试用例数: {len(iteration_report.test_cases)}")
            
            # 🆕 Phase 6: Save Report
            report_manager.save_iteration_report(iteration_report)
            
            # 3. Judge
            # Only judge if we actually ran tests
            if should_run_tests and final_result.test_results.overall_status != ExecutionStatus.SKIPPED:
                judge_result = self.judge.analyze_result(test_results)
                final_result.judge_feedback = judge_result
                
                # 🆕 Phase 6: LLM 智能分析
                analysis = None
                if judge_result.error_type != "none":
                    from .test_analyzer import TestAnalyzer
                    
                    test_analyzer = TestAnalyzer(self.builder_client)
                    
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
                        
                        # 更新报告的 judge_feedback,添加 AI 分析
                        enhanced_feedback = (
                            f"{judge_result.feedback}\n\n"
                            f"🤖 AI 分析:\n"
                            f"  主要问题: {analysis.primary_issue}\n"
                            f"  根本原因: {analysis.root_cause}\n"
                            f"  预计成功率: {analysis.estimated_success_rate:.1%}\n"
                        )
                        
                        # 如果有修复策略,也显示
                        if analysis.fix_strategy:
                            enhanced_feedback += "\n💡 修复策略:\n"
                            for i, step in enumerate(analysis.fix_strategy[:3], 1):  # 最多显示3个
                                enhanced_feedback += (
                                    f"  {i}. [{step.priority.upper()}] {step.action}\n"
                                    f"     目标: {step.target}\n"
                                )
                        
                        iteration_report.judge_feedback = enhanced_feedback
                    except Exception as e:
                        if self.callback:
                            self.callback.on_log(f"⚠️ LLM 分析失败: {str(e)}")
                        iteration_report.judge_feedback = judge_result.feedback
                else:
                    iteration_report.judge_feedback = judge_result.feedback
                
                # Update report with judge feedback
                iteration_report.fix_target = judge_result.fix_target.value if judge_result.fix_target else None
                iteration_report.error_types = self._count_error_types(judge_result)
                
                # 🆕 Phase 6: Git Commit BEFORE user confirmation
                if self.config.enable_git:
                    commit_msg = f"Iteration {iteration}: Pass rate {iteration_report.pass_rate:.1%}"
                    git.commit(commit_msg)
                    iteration_report.git_commit_hash = git.get_current_commit()  # 修复: 正确的方法名
                    iteration_report.git_commit_message = commit_msg
                    # Re-save report with git info
                    report_manager.save_iteration_report(iteration_report)
                
                # 🆕 Phase 6: Display summary
                if self.callback:
                    summary = report_manager.generate_summary(iteration)
                    self.callback.on_log(summary)
                
                # 🆕 Phase 6: Check pass rate threshold
                if iteration_report.pass_rate >= 0.9:  # 90% pass rate
                    if self.callback:
                        self.callback.on_log("✅ 测试通过率达标 (≥90%), 停止迭代")
                    final_result.success = True
                    break
                
                # 🆕 Phase 6: User confirmation checkpoint
                if self.callback and self.config.interactive:
                    result = self.callback.on_iteration_complete(
                        iteration_report,
                        analysis=None  # Phase 2 will add LLM analysis here
                    )
                    
                    # Handle case where callback might return None
                    if result is None:
                        if self.callback:
                            self.callback.on_log("⚠️ 回调返回 None, 默认停止迭代")
                        break
                    
                    continue_iteration, user_feedback = result
                    
                    if not continue_iteration:
                        if self.callback:
                            self.callback.on_log("用户选择停止迭代")
                        break
                    
                    if user_feedback:
                        # Store user feedback for potential use in fixes
                        judge_result.feedback += f"\n\n用户反馈: {user_feedback}"
                elif self.callback:
                    # Non-interactive mode: just log and continue
                    self.callback.on_log(f"非交互模式: 自动继续迭代 (迭代 {iteration}/{self.config.max_build_retries-1})")
                # 第 544 行之后,第 545 行之前插入以下代码:

                # 4. 🆕 Phase 6: 执行修复策略
                if self.callback:
                    self.callback.on_log(f"🔧 开始执行修复策略...")
                
                # 如果有 LLM 分析结果,执行修复策略
                if analysis and analysis.fix_strategy:
                    for fix_step in analysis.fix_strategy[:3]:  # 最多执行前3个修复步骤
                        if self.callback:
                            self.callback.on_log(f"  执行步骤 {fix_step.step}: {fix_step.action}")
                        
                        try:
                            if fix_step.target == "rag_builder" and rag_config:
                                # RAG 配置优化
                                from .rag_optimizer import RAGOptimizer
                                rag_optimizer = RAGOptimizer(self.builder_client)
                                
                                new_rag_config = await rag_optimizer.optimize_config(
                                    rag_config,
                                    analysis,
                                    iteration_report
                                )
                                
                                if self.callback:
                                    self.callback.on_log(
                                        f"    ✅ RAG 优化: k_retrieval {rag_config.k_retrieval} → {new_rag_config.k_retrieval}"
                                    )
                                
                                rag_config = new_rag_config
                                # 重新编译
                                self.compiler.compile(meta, graph, rag_config, tools_config, agent_dir)
                            
                            elif fix_step.target == "tool_selector" and tools_config:
                                # Tools 优化
                                from .tool_optimizer import ToolOptimizer
                                tool_optimizer = ToolOptimizer(self.builder_client, self.tool_selector)
                                
                                new_tools_config = await tool_optimizer.optimize_tools(
                                    tools_config,
                                    analysis,
                                    meta
                                )
                                
                                if self.callback:
                                    self.callback.on_log(
                                        f"    ✅ Tools 优化: {tools_config.enabled_tools} → {new_tools_config.enabled_tools}"
                                    )
                                
                                tools_config = new_tools_config
                                # 重新编译
                                self.compiler.compile(meta, graph, rag_config, tools_config, agent_dir)
                            
                            elif fix_step.target == "graph_designer":
                                # Graph 优化 + 重新仿真
                                from .graph_optimizer import GraphOptimizer
                                graph_optimizer = GraphOptimizer(self.designer, self.simulator)
                                
                                new_graph, sim_result = await graph_optimizer.optimize_graph(
                                    graph,
                                    analysis,
                                    meta
                                )
                                
                                if self.callback:
                                    sim_status = "✅ 通过" if not sim_result.has_errors() else "⚠️ 仍有问题"
                                    self.callback.on_log(f"    ✅ Graph 优化完成,仿真结果: {sim_status}")
                                
                                graph = new_graph
                                # 重新编译
                                self.compiler.compile(meta, graph, rag_config, tools_config, agent_dir)
                            
                            elif fix_step.target == "compiler":
                                # Compiler 依赖优化
                                from .compiler_optimizer import CompilerOptimizer
                                compiler_optimizer = CompilerOptimizer(self.compiler)
                                
                                error_msg = test_results.stderr or ""
                                success = await compiler_optimizer.optimize_dependencies(
                                    agent_dir,
                                    analysis,
                                    error_msg
                                )
                                
                                if success and self.callback:
                                    self.callback.on_log(f"    ✅ Compiler 优化: 已更新依赖项")
                        
                        except Exception as e:
                            if self.callback:
                                self.callback.on_log(f"    ⚠️ 修复步骤失败: {str(e)}")
                

                # Check if should continue iterating
                if judge_result.error_type == "none" or not judge_result.should_retry:
                    final_result.success = True
                    break
            else:
                # If skipped, we consider it a success in terms of generation
                final_result.success = True
                break
                
            # 4. Fix (only if we ran tests and failed)
            if self.callback:
                self.callback.on_log(f"自动修复: {judge_result.fix_target} - {judge_result.feedback[:50]}...")
                
            if judge_result.fix_target == FixTarget.COMPILER:
                # Fix runtime errors by patching code
                feedback_str = f"{judge_result.feedback}\nSuggestions: {judge_result.suggestions}"
                await self._apply_compiler_fix(agent_dir / "agent.py", feedback_str)
                
                # Check requirements if needed
                if "importerror" in judge_result.feedback.lower():
                     # Simple heuristic: notify user or append to requirements.txt
                     # For now, relying on LLM to patch agent.py implies it might try to fix imports in code,
                     # but requirements.txt is separate.
                     # TODO: Handle requirements.txt patching.
                     pass
                     
            elif judge_result.fix_target == FixTarget.GRAPH_DESIGNER:
                # Logic error requires graph change
                # This is expensive, requires re-design
                graph = await self.designer.fix_logic(graph, feedback=judge_result.feedback)
                # Re-compile
                self.compiler.compile(meta, graph, rag_config, tools_config, agent_dir)
        
        # 🆕 Phase 6: Generate final evolution summary
        if self.callback:
            evolution_summary = report_manager.generate_evolution_summary()
            self.callback.on_log(evolution_summary)
            
        if self.callback:
            self.callback.on_step_complete("Build & Evolve", final_result)
            
        return final_result

    async def _apply_compiler_fix(self, file_path: Path, feedback: str):
        """Apply a fix to a source file using LLM."""
        if not file_path.exists():
            return
            
        current_code = file_path.read_text(encoding="utf-8")
        
        prompt = f"""# Code Repair Task

The following Python code failed to execute.

## Error & Feedback
{feedback}

## Original Code
```python
{current_code}
```

## Requirement
Fix the code errors. Ensure syntax is correct and imports are valid.
Return ONLY the full corrected code content, without markdown code blocks.
"""
        # Call LLM
        fixed_code = await self.builder_client.call(prompt)
        
        # If result is a string (expected), clean it
        if isinstance(fixed_code, str):
            fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
            file_path.write_text(fixed_code, encoding="utf-8")
    
    def _create_iteration_report(
        self,
        iteration: int,
        agent_name: str,
        test_results: ExecutionResult,
        graph: GraphStructure,
        rag_config: Optional[RAGConfig],
        tools_config: Optional[ToolsConfig]
    ) -> IterationReport:
        """创建迭代报告
        
        Args:
            iteration: 迭代编号
            agent_name: Agent名称
            test_results: 测试结果
            graph: Graph结构
            rag_config: RAG配置
            tools_config: 工具配置
            
        Returns:
            IterationReport
        """
        # 统计测试结果
        total_tests = len(test_results.test_results)
        passed_tests = sum(1 for t in test_results.test_results if t.status in [ExecutionStatus.PASS, ExecutionStatus.SUCCESS])
        failed_tests = sum(1 for t in test_results.test_results if t.status in [ExecutionStatus.FAIL, ExecutionStatus.FAILED])
        skipped_tests = sum(1 for t in test_results.test_results if t.status == ExecutionStatus.SKIPPED)
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        
        # 转换测试用例
        test_cases = []
        for t in test_results.test_results:
            test_cases.append(TestCaseReport(
                test_id=t.test_id,
                test_name=t.test_id,  # 使用 test_id 作为 test_name
                status=t.status.value.upper() if hasattr(t.status, 'value') else str(t.status).upper(),
                metrics={},  # TestResult 没有 metrics 字段
                actual_output=t.actual_output or '',
                expected_output='',  # TestResult 没有 expected_output 字段
                retrieval_context=[],  # TestResult 没有 retrieval_context 字段
                error_message=t.error_message or '',
                duration_seconds=t.duration_ms / 1000.0 if t.duration_ms else 0.0
            ))
        
        # 计算平均指标
        avg_metrics = {}
        if test_cases:
            metric_names = set()
            for tc in test_cases:
                metric_names.update(tc.metrics.keys())
            
            for metric_name in metric_names:
                values = [tc.metrics.get(metric_name, 0.0) for tc in test_cases if metric_name in tc.metrics]
                if values:
                    avg_metrics[f"avg_{metric_name}"] = sum(values) / len(values)
        
        # 创建报告
        return IterationReport(
            iteration_id=iteration,
            timestamp=datetime.now(),
            agent_name=agent_name,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            pass_rate=pass_rate,
            test_cases=test_cases,
            error_types={},  # Will be filled by judge
            fix_target=None,  # Will be filled by judge
            judge_feedback="",  # Will be filled by judge
            graph_snapshot=graph.model_dump() if graph else {},
            rag_config_snapshot=rag_config.model_dump() if rag_config else None,
            tools_config_snapshot=tools_config.model_dump() if tools_config else None,
            avg_metrics=avg_metrics
        )
    
    def _count_error_types(self, judge_result: JudgeResult) -> Dict[str, int]:
        """统计错误类型
        
        Args:
            judge_result: Judge分析结果
            
        Returns:
            错误类型计数字典
        """
        error_counts = {}
        if judge_result.error_type and judge_result.error_type != "none":
            error_counts[judge_result.error_type] = 1
        return error_counts

