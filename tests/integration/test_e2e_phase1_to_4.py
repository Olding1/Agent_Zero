"""
Phase 1-4 端到端集成测试

测试目标:
验证从用户需求到最终交付的完整流程,覆盖所有 4 个 Phase

测试场景:
用户需求: "创建一个能够回答项目文档问题的 RAG Agent"
  ↓
Phase 1: 基础设施 (Compiler, EnvManager)
  ↓
Phase 2: 数据流和工具 (Tool Registry, RAG Builder)
  ↓
Phase 3: 智能规划 (PM, Graph Designer)
  ↓
Phase 4: 闭环与进化 (Test Generator, Runner, Judge, Git)
  ↓
最终交付: 可执行的 Agent + 测试 + 版本管理

为什么这么测试:
- 模拟真实用户的完整使用流程
- 验证所有 Phase 的集成是否正确
- 确保端到端流程能够正常工作
- 发现跨 Phase 的集成问题

测试什么功能:
Phase 1:
  - Compiler 能否生成可执行代码
  - EnvManager 能否管理虚拟环境

Phase 2:
  - RAGBuilder 能否构建 RAG 系统
  - Tool Registry 能否管理工具

Phase 3:
  - PM 能否分析需求
  - Graph Designer 能否设计图结构

Phase 4:
  - TestGenerator 能否生成测试
  - Runner 能否执行测试
  - Judge 能否分析结果
  - Git 能否管理版本

覆盖度:
- Phase 1: Compiler ✓, EnvManager ✓
- Phase 2: RAGBuilder ✓, ToolSelector ✓
- Phase 3: PM ✓, GraphDesigner ✓
- Phase 4: TestGenerator ✓, Runner ✓, Judge ✓, Git ✓
"""

import asyncio
import tempfile
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core import (
    PM, GraphDesigner, Compiler, RAGBuilder, ToolSelector,
    TestGenerator, Runner, Judge,
    DeepEvalTestConfig, ErrorType, FixTarget
)
from src.utils.git_utils import GitUtils, create_version_tag, create_commit_message
from src.schemas import ProjectMeta, TaskType, RAGConfig, ToolsConfig
from src.llm.builder_client import BuilderClient


class Phase1to4IntegrationTest:
    """Phase 1-4 端到端集成测试"""
    
    def __init__(self):
        self.test_dir = None
        self.agent_dir = None
        self.results = {}
        self.project_meta = None
        self.graph = None
        self.rag_config = None
        self.tools_config = None
    
    async def run_all_tests(self):
        """运行所有端到端测试"""
        print("=" * 80)
        print("Phase 1-4 端到端集成测试")
        print("=" * 80)
        print()
        
        print("📋 用户需求: 创建一个能够回答项目文档问题的 RAG Agent")
        print()
        
        try:
            # 创建临时测试目录
            self.test_dir = Path(tempfile.mkdtemp(prefix="e2e_test_"))
            print(f"📁 测试目录: {self.test_dir}")
            print()
            
            # Phase 3: PM 分析需求
            await self.phase3_step1_pm_analysis()
            
            # Phase 3: Graph Designer 设计图结构
            await self.phase3_step2_graph_design()
            
            # Phase 2: RAG Builder 构建 RAG 配置
            await self.phase2_rag_builder()
            
            # Phase 2: Tool Selector 选择工具
            await self.phase2_tool_selector()
            
            # Phase 1: Compiler 生成代码
            await self.phase1_compiler()
            
            # Phase 1: EnvManager 管理环境 (模拟)
            self.phase1_env_manager()
            
            # Phase 4: Test Generator 生成测试
            await self.phase4_step1_test_generator()
            
            # Phase 4: Git 版本管理
            self.phase4_step2_git_management()
            
            # Phase 4: Runner 和 Judge (模拟)
            self.phase4_step3_runner_judge()
            
            # 验证最终交付物
            self.verify_final_deliverables()
            
            # 打印测试总结
            self.print_summary()
            
        finally:
            # 保留测试目录供检查
            if self.test_dir and self.test_dir.exists():
                print(f"\n🗑️  测试目录保留在: {self.test_dir}")
                print("   (如需清理,请手动删除)")
    
    async def phase3_step1_pm_analysis(self):
        """Phase 3 Step 1: PM 分析需求"""
        print("=" * 80)
        print("Phase 3 - Step 1: PM 分析需求")
        print("=" * 80)
        
        # 模拟用户输入
        user_input = "创建一个能够回答项目文档问题的 RAG Agent"
        
        # 创建 mock BuilderClient
        class MockBuilderClient:
            async def call(self, prompt: str, schema=None):
                # 返回模拟的 ProjectMeta
                return ProjectMeta(
                    agent_name="project_qa_agent",
                    description="一个能够回答项目文档问题的 RAG Agent",
                    has_rag=True,
                    task_type=TaskType.RAG,
                    language="zh-CN",
                    user_intent_summary="用户想要创建一个 RAG Agent 来回答项目文档问题",
                    file_paths=["README.md", "docs/guide.md"],
                    clarification_needed=False
                )
        
        # PM 分析
        pm = PM(MockBuilderClient())
        self.project_meta = await pm.analyze_requirements(
            user_input,
            file_paths=[Path("README.md"), Path("docs/guide.md")]
        )
        
        # 验证
        assert self.project_meta is not None, "PM 分析失败"
        assert self.project_meta.has_rag is True, "PM 未识别 RAG 需求"
        assert self.project_meta.task_type == TaskType.RAG, "PM 任务类型错误"
        
        print(f"  ✅ Agent 名称: {self.project_meta.agent_name}")
        print(f"  ✅ 任务类型: {self.project_meta.task_type}")
        print(f"  ✅ 需要 RAG: {self.project_meta.has_rag}")
        print(f"  ✅ 文件数量: {len(self.project_meta.file_paths or [])}")
        
        self.results['phase3_pm'] = "✅ PASS"
        print("\n✅ Phase 3 - PM 分析完成")
        print()
    
    async def phase3_step2_graph_design(self):
        """Phase 3 Step 2: Graph Designer 设计图结构"""
        print("=" * 80)
        print("Phase 3 - Step 2: Graph Designer 设计图结构")
        print("=" * 80)
        
        # 创建 mock BuilderClient
        class MockBuilderClient:
            async def call(self, prompt: str, schema=None):
                # 返回模拟的 GraphStructure
                from src.schemas.graph_structure import GraphStructure, Node, Edge, StateField
                
                return GraphStructure(
                    pattern="sequential",
                    state_schema=StateField(
                        name="messages",
                        type="List[BaseMessage]",
                        description="对话消息列表"
                    ),
                    nodes=[
                        Node(
                            id="rag_retrieval",
                            type="rag",
                            description="从文档中检索相关内容"
                        ),
                        Node(
                            id="llm_response",
                            type="llm",
                            description="基于检索内容生成回答"
                        )
                    ],
                    edges=[
                        Edge(source="rag_retrieval", target="llm_response")
                    ],
                    entry_point="rag_retrieval"
                )
        
        # Graph Designer 设计
        designer = GraphDesigner(MockBuilderClient())
        self.graph = await designer.design_graph(self.project_meta)
        
        # 验证
        assert self.graph is not None, "Graph 设计失败"
        assert len(self.graph.nodes) >= 2, "Graph 节点数量不足"
        assert any(node.type == "rag" for node in self.graph.nodes), "Graph 缺少 RAG 节点"
        assert any(node.type == "llm" for node in self.graph.nodes), "Graph 缺少 LLM 节点"
        
        print(f"  ✅ 图模式: {self.graph.pattern}")
        print(f"  ✅ 节点数量: {len(self.graph.nodes)}")
        print(f"  ✅ 边数量: {len(self.graph.edges)}")
        print(f"  ✅ 入口点: {self.graph.entry_point}")
        
        for node in self.graph.nodes:
            print(f"     - {node.id} ({node.type})")
        
        self.results['phase3_graph'] = "✅ PASS"
        print("\n✅ Phase 3 - Graph 设计完成")
        print()
    
    async def phase2_rag_builder(self):
        """Phase 2: RAG Builder 构建 RAG 配置"""
        print("=" * 80)
        print("Phase 2 - Step 1: RAG Builder 构建配置")
        print("=" * 80)
        
        # 创建测试文档
        docs_dir = self.test_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        readme = docs_dir / "README.md"
        readme.write_text("""# 项目文档

这是一个测试项目。

## 功能
- 功能 A
- 功能 B
""", encoding='utf-8')
        
        # RAG Builder 构建配置
        rag_builder = RAGBuilder()
        self.rag_config = rag_builder.build_config(
            file_paths=[str(readme)],
            vector_store="chroma",
            embedding_provider="openai",
            chunk_size=500,
            chunk_overlap=50
        )
        
        # 验证
        assert self.rag_config is not None, "RAG 配置构建失败"
        assert self.rag_config.vector_store == "chroma", "Vector store 配置错误"
        assert self.rag_config.embedding_provider == "openai", "Embedding provider 配置错误"
        
        print(f"  ✅ Vector Store: {self.rag_config.vector_store}")
        print(f"  ✅ Embedding Provider: {self.rag_config.embedding_provider}")
        print(f"  ✅ Chunk Size: {self.rag_config.chunk_size}")
        print(f"  ✅ 文档数量: {len(self.rag_config.file_paths)}")
        
        self.results['phase2_rag'] = "✅ PASS"
        print("\n✅ Phase 2 - RAG 配置完成")
        print()
    
    async def phase2_tool_selector(self):
        """Phase 2: Tool Selector 选择工具"""
        print("=" * 80)
        print("Phase 2 - Step 2: Tool Selector 选择工具")
        print("=" * 80)
        
        # Tool Selector 选择工具
        tool_selector = ToolSelector()
        
        # 对于 RAG 任务,通常不需要额外工具
        selected_tools = tool_selector.select_tools(
            task_type=TaskType.RAG,
            user_intent="回答文档问题"
        )
        
        self.tools_config = ToolsConfig(
            enabled_tools=selected_tools
        )
        
        print(f"  ✅ 选择的工具数量: {len(selected_tools)}")
        if selected_tools:
            for tool in selected_tools:
                print(f"     - {tool}")
        else:
            print(f"     (RAG 任务不需要额外工具)")
        
        self.results['phase2_tools'] = "✅ PASS"
        print("\n✅ Phase 2 - 工具选择完成")
        print()
    
    async def phase1_compiler(self):
        """Phase 1: Compiler 生成代码"""
        print("=" * 80)
        print("Phase 1 - Step 1: Compiler 生成代码")
        print("=" * 80)
        
        # Compiler 生成代码
        template_dir = project_root / "src" / "templates"
        compiler = Compiler(template_dir)
        
        self.agent_dir = self.test_dir / "generated_agent"
        result = compiler.compile(
            self.project_meta,
            self.graph,
            self.rag_config,
            self.tools_config,
            self.agent_dir
        )
        
        # 验证
        assert result.success, f"编译失败: {result.error_message}"
        assert self.agent_dir.exists(), "Agent 目录不存在"
        
        print(f"  ✅ 编译成功")
        print(f"  ✅ 生成文件数量: {len(result.generated_files)}")
        
        for file in result.generated_files:
            print(f"     - {file}")
        
        # 验证关键文件
        assert (self.agent_dir / "agent.py").exists(), "缺少 agent.py"
        assert (self.agent_dir / "requirements.txt").exists(), "缺少 requirements.txt"
        assert (self.agent_dir / ".env.template").exists(), "缺少 .env.template"
        
        # Phase 4 优化验证
        assert (self.agent_dir / "pip.conf").exists(), "缺少 pip.conf (Phase 4)"
        assert (self.agent_dir / "install.sh").exists(), "缺少 install.sh (Phase 4)"
        
        self.results['phase1_compiler'] = "✅ PASS"
        print("\n✅ Phase 1 - 代码生成完成")
        print()
    
    def phase1_env_manager(self):
        """Phase 1: EnvManager 管理环境 (模拟)"""
        print("=" * 80)
        print("Phase 1 - Step 2: EnvManager 管理环境 (模拟)")
        print("=" * 80)
        
        # 检查 requirements.txt
        requirements_file = self.agent_dir / "requirements.txt"
        requirements = requirements_file.read_text()
        
        # 验证包含必要的依赖
        assert "langchain" in requirements, "缺少 langchain"
        assert "langgraph" in requirements, "缺少 langgraph"
        assert "chromadb" in requirements, "缺少 chromadb (RAG)"
        assert "deepeval" in requirements, "缺少 deepeval (Phase 4)"
        
        print(f"  ✅ requirements.txt 包含所有必要依赖")
        print(f"  ℹ️  (实际环境创建需要运行 install.sh)")
        
        self.results['phase1_env'] = "✅ PASS"
        print("\n✅ Phase 1 - 环境配置完成")
        print()
    
    async def phase4_step1_test_generator(self):
        """Phase 4 Step 1: Test Generator 生成测试"""
        print("=" * 80)
        print("Phase 4 - Step 1: Test Generator 生成测试")
        print("=" * 80)
        
        # 创建 mock BuilderClient
        class MockBuilderClient:
            async def generate(self, prompt: str) -> str:
                return '''```json
[
  {
    "question": "项目有哪些功能?",
    "expected_answer": "项目有功能 A 和功能 B"
  },
  {
    "question": "这是什么项目?",
    "expected_answer": "这是一个测试项目"
  }
]
```'''
        
        # Test Generator 生成测试
        test_gen = TestGenerator(MockBuilderClient())
        
        config = DeepEvalTestConfig(
            num_rag_tests=2,
            num_logic_tests=1,
            use_local_llm=True
        )
        
        test_code = await test_gen.generate_deepeval_tests(
            self.project_meta,
            self.rag_config,
            config
        )
        
        # 保存测试文件
        tests_dir = self.agent_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        test_file = tests_dir / "test_deepeval.py"
        test_file.write_text(test_code, encoding='utf-8')
        
        # 验证
        assert test_file.exists(), "测试文件未生成"
        assert len(test_code) > 0, "测试代码为空"
        assert "deepeval" in test_code, "缺少 deepeval 导入"
        
        print(f"  ✅ 测试文件已生成: {test_file.name}")
        print(f"  ✅ 测试代码长度: {len(test_code)} 字符")
        
        self.results['phase4_test_gen'] = "✅ PASS"
        print("\n✅ Phase 4 - 测试生成完成")
        print()
    
    def phase4_step2_git_management(self):
        """Phase 4 Step 2: Git 版本管理"""
        print("=" * 80)
        print("Phase 4 - Step 2: Git 版本管理")
        print("=" * 80)
        
        # Git 初始化
        git = GitUtils(self.agent_dir)
        git.init_repo()
        
        # 提交初始版本
        git.commit(create_commit_message(1, True, "Initial generated agent"))
        git.tag(create_version_tag(1), "Version 1.0.1 - Initial release")
        
        # 验证
        assert (self.agent_dir / ".git").exists(), "Git 仓库未初始化"
        
        history = git.get_history(max_count=5)
        assert len(history) > 0, "Git 历史为空"
        
        print(f"  ✅ Git 仓库已初始化")
        print(f"  ✅ 初始提交已创建")
        print(f"  ✅ 标签已创建: v1.0.1")
        
        self.results['phase4_git'] = "✅ PASS"
        print("\n✅ Phase 4 - Git 版本管理完成")
        print()
    
    def phase4_step3_runner_judge(self):
        """Phase 4 Step 3: Runner 和 Judge (模拟)"""
        print("=" * 80)
        print("Phase 4 - Step 3: Runner 和 Judge (模拟)")
        print("=" * 80)
        
        # 创建 Runner
        runner = Runner(self.agent_dir)
        
        # 检查配置
        python_exe = runner._find_python_executable()
        print(f"  ✅ Python: {python_exe}")
        
        # 模拟测试结果
        from src.schemas.execution_result import ExecutionResult, ExecutionStatus, TestResult
        
        mock_result = ExecutionResult(
            overall_status=ExecutionStatus.PASS,
            test_results=[
                TestResult(
                    test_id="test_rag_fact_1",
                    status=ExecutionStatus.PASS,
                    duration_ms=1500
                ),
                TestResult(
                    test_id="test_rag_fact_2",
                    status=ExecutionStatus.PASS,
                    duration_ms=1800
                )
            ]
        )
        
        # Judge 分析
        judge = Judge()
        judge_result = judge.analyze_result(mock_result)
        
        assert judge_result.error_type == ErrorType.NONE, "Judge 分析错误"
        
        print(f"  ✅ 模拟测试结果: PASS")
        print(f"  ✅ Judge 分析: {judge_result.error_type}")
        print(f"  ✅ 修复目标: {judge_result.fix_target}")
        
        self.results['phase4_runner_judge'] = "✅ PASS"
        print("\n✅ Phase 4 - Runner/Judge 完成")
        print()
    
    def verify_final_deliverables(self):
        """验证最终交付物"""
        print("=" * 80)
        print("验证最终交付物")
        print("=" * 80)
        
        deliverables = {
            "可执行 Agent": self.agent_dir / "agent.py",
            "依赖配置": self.agent_dir / "requirements.txt",
            "环境模板": self.agent_dir / ".env.template",
            "安装脚本 (Linux)": self.agent_dir / "install.sh",
            "安装脚本 (Windows)": self.agent_dir / "install.bat",
            "镜像源配置": self.agent_dir / "pip.conf",
            "DeepEval 测试": self.agent_dir / "tests" / "test_deepeval.py",
            "Git 仓库": self.agent_dir / ".git",
            "图结构配置": self.agent_dir / "graph.json"
        }
        
        all_present = True
        for name, path in deliverables.items():
            if path.exists():
                print(f"  ✅ {name}")
            else:
                print(f"  ❌ {name} (缺失)")
                all_present = False
        
        assert all_present, "部分交付物缺失"
        
        self.results['deliverables'] = "✅ PASS"
        print("\n✅ 所有交付物齐全")
        print()
    
    def print_summary(self):
        """打印测试总结"""
        print("=" * 80)
        print("端到端测试总结")
        print("=" * 80)
        print()
        
        phases = {
            "Phase 3 - PM": ['phase3_pm'],
            "Phase 3 - Graph Designer": ['phase3_graph'],
            "Phase 2 - RAG Builder": ['phase2_rag'],
            "Phase 2 - Tool Selector": ['phase2_tools'],
            "Phase 1 - Compiler": ['phase1_compiler'],
            "Phase 1 - EnvManager": ['phase1_env'],
            "Phase 4 - Test Generator": ['phase4_test_gen'],
            "Phase 4 - Git": ['phase4_git'],
            "Phase 4 - Runner/Judge": ['phase4_runner_judge'],
            "最终交付物": ['deliverables']
        }
        
        for phase_name, test_keys in phases.items():
            results = [self.results.get(key, "❌ FAIL") for key in test_keys]
            status = "✅" if all("PASS" in r for r in results) else "❌"
            print(f"{status} {phase_name}")
        
        print()
        
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if "PASS" in r)
        
        print(f"总计: {passed}/{total} 测试通过")
        print()
        
        if passed == total:
            print("🎉 Phase 1-4 端到端集成测试全部通过!")
            print()
            print("✨ 从用户需求到最终交付的完整流程验证成功!")
        else:
            print("❌ 部分测试失败,请检查日志")
        
        print()
        print(f"📁 测试目录: {self.test_dir}")
        print(f"📁 生成的 Agent: {self.agent_dir}")


async def main():
    """主函数"""
    test = Phase1to4IntegrationTest()
    await test.run_all_tests()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  Phase 1-4 端到端集成测试                                    ║
║                                                                              ║
║  测试目标: 验证从用户需求到最终交付的完整流程                                 ║
║  测试范围: Phase 1, 2, 3, 4 的完整集成                                       ║
║  测试方式: 模拟真实用户使用场景                                              ║
║                                                                              ║
║  用户需求: 创建一个能够回答项目文档问题的 RAG Agent                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    asyncio.run(main())
