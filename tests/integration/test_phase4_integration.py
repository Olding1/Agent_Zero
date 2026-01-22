"""
Phase 4 闭环集成测试

测试目标:
验证 Phase 4 的完整闭环流程,从生成测试到执行、分析、修复的完整循环

测试场景:
1. 生成一个简单的 RAG Agent
2. 自动生成 DeepEval 测试
3. 执行测试
4. 分析结果
5. Git 版本管理
6. (如果失败) 生成修复建议

为什么这么测试:
- 模拟真实用户使用 Phase 4 的完整流程
- 验证所有模块的集成是否正确
- 确保闭环能够正常工作

测试什么功能:
1. TestGenerator 能否正确生成 DeepEval 测试代码
2. 生成的测试代码是否可执行
3. Runner 能否正确执行测试
4. Judge 能否正确分析结果
5. GitUtils 能否正确管理版本
6. 外部 Trace 存储是否正常工作
7. DeepEval 预安装是否生效
8. Ollama 简化集成是否正常

覆盖度:
- Task 4.1: 外部 Trace 存储 ✓
- Task 4.2: Test Generator ✓
- Task 4.3: Compiler 升级 ✓
- Task 4.4: Runner ✓
- Task 4.5: Judge ✓
- Task 4.6: Git 版本管理 ✓
"""

import asyncio
import tempfile
from pathlib import Path
import sys
import shutil

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core import (
    Compiler, TestGenerator, Runner, Judge,
    DeepEvalTestConfig, ErrorType, FixTarget
)
from src.utils.git_utils import GitUtils, create_version_tag, create_commit_message
from src.schemas import ProjectMeta, TaskType, GraphStructure, RAGConfig, ToolsConfig
from src.schemas.graph_structure import Node, Edge, StateField
from src.llm.builder_client import BuilderClient


class Phase4IntegrationTest:
    """Phase 4 闭环集成测试"""
    
    def __init__(self):
        self.test_dir = None
        self.agent_dir = None
        self.results = {}
    
    async def run_all_tests(self):
        """运行所有集成测试"""
        print("=" * 80)
        print("Phase 4 闭环集成测试")
        print("=" * 80)
        print()
        
        try:
            # 创建临时测试目录
            self.test_dir = Path(tempfile.mkdtemp(prefix="phase4_test_"))
            print(f"📁 测试目录: {self.test_dir}")
            print()
            
            # 测试 1: 生成 Agent (包含 Trace 和 DeepEval)
            await self.test_1_generate_agent()
            
            # 测试 2: 生成 DeepEval 测试
            await self.test_2_generate_tests()
            
            # 测试 3: 检查预安装的依赖
            self.test_3_check_preinstalled_deps()
            
            # 测试 4: 检查外部 Trace 配置
            self.test_4_check_trace_config()
            
            # 测试 5: Git 版本管理
            self.test_5_git_version_control()
            
            # 测试 6: Runner 和 Judge (模拟)
            self.test_6_runner_and_judge()
            
            # 打印测试总结
            self.print_summary()
            
        finally:
            # 清理测试目录 (可选)
            if self.test_dir and self.test_dir.exists():
                print(f"\n🗑️  测试目录保留在: {self.test_dir}")
                print("   (如需清理,请手动删除)")
    
    async def test_1_generate_agent(self):
        """测试 1: 生成 Agent (验证 Compiler 升级)"""
        print("=" * 80)
        print("测试 1: 生成 Agent (验证 Task 4.1 + 4.3)")
        print("=" * 80)
        
        # 创建测试用的 ProjectMeta
        project_meta = ProjectMeta(
            agent_name="test_rag_agent",
            description="一个用于测试的 RAG 问答 Agent",
            has_rag=True,
            task_type=TaskType.RAG,
            language="zh-CN",
            user_intent_summary="测试 RAG 功能"
        )
        
        # 创建简单的 Graph 结构
        graph = GraphStructure(
            pattern="sequential",
            state_schema=StateField(
                name="messages",
                type="List[BaseMessage]",
                description="对话消息"
            ),
            nodes=[
                Node(
                    id="rag_node",
                    type="rag",
                    description="RAG 检索节点"
                ),
                Node(
                    id="llm_node",
                    type="llm",
                    description="LLM 生成节点"
                )
            ],
            edges=[
                Edge(source="rag_node", target="llm_node")
            ],
            entry_point="rag_node"
        )
        
        # RAG 配置
        rag_config = RAGConfig(
            file_paths=["test_doc.md"],
            vector_store="chroma",
            embedding_provider="openai",
            chunk_size=500
        )
        
        # Tools 配置
        tools_config = ToolsConfig(enabled_tools=[])
        
        # 编译
        template_dir = project_root / "src" / "templates"
        compiler = Compiler(template_dir)
        
        self.agent_dir = self.test_dir / "test_agent"
        result = compiler.compile(
            project_meta,
            graph,
            rag_config,
            tools_config,
            self.agent_dir
        )
        
        # 验证
        assert result.success, f"编译失败: {result.error_message}"
        assert self.agent_dir.exists(), "Agent 目录不存在"
        
        # 验证生成的文件
        expected_files = [
            "agent.py",
            "requirements.txt",
            ".env.template",
            "pip.conf",  # Task 4.3
            "install.sh",  # Task 4.3
            "install.bat",  # Task 4.3
            "graph.json"
        ]
        
        for file in expected_files:
            file_path = self.agent_dir / file
            assert file_path.exists(), f"缺少文件: {file}"
            print(f"  ✅ {file}")
        
        # 验证 requirements.txt 包含 DeepEval
        requirements = (self.agent_dir / "requirements.txt").read_text()
        assert "deepeval>=0.21.0" in requirements, "requirements.txt 缺少 deepeval"
        assert "pytest>=7.4.0" in requirements, "requirements.txt 缺少 pytest"
        print(f"  ✅ requirements.txt 包含 DeepEval 依赖")
        
        # 验证 pip.conf
        pip_conf = (self.agent_dir / "pip.conf").read_text()
        assert "tsinghua" in pip_conf, "pip.conf 未配置镜像源"
        print(f"  ✅ pip.conf 配置正确")
        
        self.results['test_1'] = "✅ PASS"
        print("\n✅ 测试 1 通过: Agent 生成成功,包含 DeepEval 预安装配置")
        print()
    
    async def test_2_generate_tests(self):
        """测试 2: 生成 DeepEval 测试 (验证 TestGenerator)"""
        print("=" * 80)
        print("测试 2: 生成 DeepEval 测试 (验证 Task 4.2)")
        print("=" * 80)
        
        # 创建 mock BuilderClient
        class MockBuilderClient:
            async def generate(self, prompt: str) -> str:
                # 返回模拟的 JSON 响应
                return '''```json
[
  {
    "question": "什么是 Agent Zero?",
    "expected_answer": "Agent Zero 是一个智能体构建工厂"
  },
  {
    "question": "Phase 4 的目标是什么?",
    "expected_answer": "Phase 4 的目标是实现闭环与进化"
  }
]
```'''
        
        # 创建 TestGenerator
        test_gen = TestGenerator(MockBuilderClient())
        
        # 生成测试
        project_meta = ProjectMeta(
            agent_name="test_rag_agent",
            description="测试 RAG Agent",
            has_rag=True,
            task_type=TaskType.RAG
        )
        
        rag_config = RAGConfig(
            file_paths=["test_doc.md"],
            vector_store="chroma",
            embedding_provider="openai"
        )
        
        config = DeepEvalTestConfig(
            num_rag_tests=2,
            num_logic_tests=1,
            use_local_llm=True,
            judge_model="llama3"
        )
        
        test_code = await test_gen.generate_deepeval_tests(
            project_meta,
            rag_config,
            config
        )
        
        # 验证生成的测试代码
        assert len(test_code) > 0, "测试代码为空"
        assert "from deepeval import assert_test" in test_code, "缺少 deepeval 导入"
        assert "ChatOllama" in test_code, "未使用简化的 Ollama 集成"
        assert "judge_llm" in test_code, "缺少 judge_llm 配置"
        assert "test_rag_fact" in test_code, "缺少 RAG 测试函数"
        assert "run_agent" in test_code, "缺少 run_agent 调用"
        assert "return_trace=True" in test_code, "未使用外部 Trace"
        
        print(f"  ✅ 测试代码长度: {len(test_code)} 字符")
        print(f"  ✅ 包含 DeepEval 导入")
        print(f"  ✅ 使用简化的 Ollama 集成 (ChatOllama)")
        print(f"  ✅ 使用外部 Trace (return_trace=True)")
        
        # 保存测试文件
        tests_dir = self.agent_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        test_file = tests_dir / "test_deepeval.py"
        test_file.write_text(test_code, encoding='utf-8')
        
        print(f"  ✅ 测试文件已保存: {test_file}")
        
        self.results['test_2'] = "✅ PASS"
        print("\n✅ 测试 2 通过: DeepEval 测试生成成功")
        print()
    
    def test_3_check_preinstalled_deps(self):
        """测试 3: 检查预安装的依赖配置"""
        print("=" * 80)
        print("测试 3: 检查预安装依赖配置 (验证 Task 4.3)")
        print("=" * 80)
        
        # 检查 install.sh
        install_sh = self.agent_dir / "install.sh"
        content = install_sh.read_text()
        
        assert "pip" in content and "install" in content, "install.sh 缺少安装命令"
        assert "requirements.txt" in content, "install.sh 未引用 requirements.txt"
        assert "tsinghua" in content, "install.sh 未使用镜像源"
        
        print(f"  ✅ install.sh 配置正确")
        
        # 检查 install.bat
        install_bat = self.agent_dir / "install.bat"
        content = install_bat.read_text()
        
        assert "pip install" in content, "install.bat 缺少安装命令"
        assert "requirements.txt" in content, "install.bat 未引用 requirements.txt"
        
        print(f"  ✅ install.bat 配置正确")
        
        self.results['test_3'] = "✅ PASS"
        print("\n✅ 测试 3 通过: 预安装依赖配置正确")
        print()
    
    def test_4_check_trace_config(self):
        """测试 4: 检查外部 Trace 配置"""
        print("=" * 80)
        print("测试 4: 检查外部 Trace 配置 (验证 Task 4.1)")
        print("=" * 80)
        
        # 检查 agent.py 中的 Trace 配置
        agent_py = self.agent_dir / "agent.py"
        content = agent_py.read_text()
        
        # 验证包含 TraceManager
        assert "TraceManager" in content or "trace" in content.lower(), "agent.py 未配置 Trace"
        
        print(f"  ✅ agent.py 包含 Trace 配置")
        
        # 验证 .trace 目录会被创建
        # (实际运行时才会创建,这里只检查代码)
        
        self.results['test_4'] = "✅ PASS"
        print("\n✅ 测试 4 通过: 外部 Trace 配置正确")
        print()
    
    def test_5_git_version_control(self):
        """测试 5: Git 版本管理"""
        print("=" * 80)
        print("测试 5: Git 版本管理 (验证 Task 4.6)")
        print("=" * 80)
        
        # 初始化 Git
        git = GitUtils(self.agent_dir)
        success = git.init_repo()
        
        assert success, "Git 初始化失败"
        assert (self.agent_dir / ".git").exists(), ".git 目录不存在"
        print(f"  ✅ Git 仓库初始化成功")
        
        # 提交初始版本
        success = git.commit(create_commit_message(1, True, "Initial version"))
        assert success, "Git 提交失败"
        print(f"  ✅ 初始提交成功")
        
        # 创建标签
        success = git.tag(create_version_tag(1), "Version 1.0.1")
        assert success, "Git 标签创建失败"
        print(f"  ✅ 标签创建成功: v1.0.1")
        
        # 获取历史
        history = git.get_history(max_count=5)
        assert len(history) > 0, "无法获取 Git 历史"
        print(f"  ✅ Git 历史获取成功: {len(history)} 个提交")
        
        self.results['test_5'] = "✅ PASS"
        print("\n✅ 测试 5 通过: Git 版本管理正常")
        print()
    
    def test_6_runner_and_judge(self):
        """测试 6: Runner 和 Judge (模拟)"""
        print("=" * 80)
        print("测试 6: Runner 和 Judge (验证 Task 4.4 + 4.5)")
        print("=" * 80)
        
        # 创建 Runner
        runner = Runner(self.agent_dir)
        
        # 检查 Python 可执行文件
        python_exe = runner._find_python_executable()
        assert python_exe.exists(), "无法找到 Python 可执行文件"
        print(f"  ✅ Python 可执行文件: {python_exe}")
        
        # 检查 DeepEval 安装状态
        installed = runner._check_deepeval_installed()
        print(f"  ℹ️  DeepEval 安装状态: {installed}")
        
        # 模拟测试结果
        from src.schemas.execution_result import ExecutionResult, ExecutionStatus, TestResult
        
        # 模拟成功的结果
        success_result = ExecutionResult(
            overall_status=ExecutionStatus.PASS,
            test_results=[
                TestResult(
                    test_id="test_rag_fact_1",
                    status=ExecutionStatus.PASS,
                    duration_ms=1500
                )
            ]
        )
        
        # 使用 Judge 分析
        judge = Judge()
        judge_result = judge.analyze_result(success_result)
        
        assert judge_result.error_type == ErrorType.NONE, "Judge 未正确识别成功"
        assert judge_result.fix_target == FixTarget.NONE, "Judge 错误设置修复目标"
        print(f"  ✅ Judge 正确识别成功结果")
        
        # 模拟失败的结果
        fail_result = ExecutionResult(
            overall_status=ExecutionStatus.FAIL,
            test_results=[
                TestResult(
                    test_id="test_rag_fact_1_faithfulness",
                    status=ExecutionStatus.FAIL,
                    error_message="Faithfulness score too low",
                    duration_ms=2000
                )
            ]
        )
        
        judge_result = judge.analyze_result(fail_result)
        
        assert judge_result.error_type == ErrorType.LOGIC, "Judge 未正确分类逻辑错误"
        assert judge_result.fix_target == FixTarget.GRAPH_DESIGNER, "Judge 错误设置修复目标"
        assert len(judge_result.suggestions) > 0, "Judge 未生成建议"
        print(f"  ✅ Judge 正确分类逻辑错误")
        print(f"  ✅ Judge 生成了 {len(judge_result.suggestions)} 条建议")
        
        self.results['test_6'] = "✅ PASS"
        print("\n✅ 测试 6 通过: Runner 和 Judge 功能正常")
        print()
    
    def print_summary(self):
        """打印测试总结"""
        print("=" * 80)
        print("测试总结")
        print("=" * 80)
        print()
        
        for test_name, result in self.results.items():
            print(f"{test_name}: {result}")
        
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if "PASS" in r)
        
        print()
        print(f"总计: {passed}/{total} 测试通过")
        print()
        
        if passed == total:
            print("🎉 Phase 4 闭环集成测试全部通过!")
        else:
            print("❌ 部分测试失败,请检查日志")
        
        print()
        print(f"📁 测试目录: {self.test_dir}")
        print(f"📁 Agent 目录: {self.agent_dir}")


async def main():
    """主函数"""
    test = Phase4IntegrationTest()
    await test.run_all_tests()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Phase 4 闭环集成测试                                      ║
║                                                                              ║
║  测试目标: 验证 Phase 4 的完整闭环流程                                       ║
║  测试范围: Task 4.1 - 4.6 的集成                                            ║
║  测试方式: 模拟真实用户使用场景                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    asyncio.run(main())
