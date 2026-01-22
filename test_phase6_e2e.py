"""
Phase 6 End-to-End Test

测试完整的迭代循环:
1. 创建一个简单的 RAG Agent
2. 运行测试并生成报告
3. 验证用户交互
4. 检查 Git 提交
5. 验证进化总结
"""

import asyncio
from pathlib import Path
from src.core.agent_factory import AgentFactory
from src.cli.cli_callback import CLICallback
from src.config.factory_config import AgentFactoryConfig
from src.llm.builder_client import BuilderClient


async def test_phase6_iteration():
    """测试 Phase 6 迭代功能"""
    
    print("="*70)
    print("🧪 Phase 6 端到端测试")
    print("="*70)
    
    # 1. 配置
    config = AgentFactoryConfig(
        builder_provider="deepseek",
        builder_model="deepseek-chat",
        builder_api_key="your-api-key-here",  # 替换为实际的 API Key
        builder_base_url="https://api.deepseek.com",
        output_base_dir=Path("./test_agents"),
        interactive=True,  # 启用交互式确认
        enable_git=True,   # 启用 Git
        max_build_retries=3  # 最多3次迭代
    )
    
    # 2. 创建 Factory
    builder_client = BuilderClient(
        provider=config.builder_provider,
        model=config.builder_model,
        api_key=config.builder_api_key,
        base_url=config.builder_base_url
    )
    
    factory = AgentFactory(
        builder_client=builder_client,
        config=config,
        callback=CLICallback()  # 使用 CLI 回调
    )
    
    # 3. 创建一个简单的 RAG Agent
    user_input = """
    创建一个文档问答 Agent，名称为 TestPhase6Agent。
    
    功能：
    - 回答关于 Python 编程的问题
    - 使用 RAG 检索相关文档
    
    数据源：
    - 使用 Python 官方文档
    """
    
    print(f"\n📝 用户输入:\n{user_input}\n")
    
    # 4. 执行创建
    try:
        result = await factory.create_agent(user_input)
        
        print("\n" + "="*70)
        print("✅ Agent 创建完成!")
        print("="*70)
        print(f"Agent 目录: {result.agent_dir}")
        print(f"迭代次数: {result.iteration_count}")
        print(f"成功: {result.success}")
        
        # 5. 检查报告目录
        reports_dir = result.agent_dir / ".reports"
        if reports_dir.exists():
            print(f"\n📊 报告目录: {reports_dir}")
            report_files = list(reports_dir.glob("*.json"))
            print(f"报告文件数: {len(report_files)}")
            for f in report_files:
                print(f"  - {f.name}")
        
        # 6. 检查 Git 历史
        git_dir = result.agent_dir / ".git"
        if git_dir.exists():
            print(f"\n📦 Git 仓库已初始化")
            # 可以使用 GitUtils 查看提交历史
        
        return result
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_report_manager():
    """测试 ReportManager 功能"""
    from src.core.report_manager import ReportManager
    
    print("\n" + "="*70)
    print("🧪 测试 ReportManager")
    print("="*70)
    
    # 假设 Agent 已创建
    agent_dir = Path("./test_agents/TestPhase6Agent")
    
    if not agent_dir.exists():
        print("⚠️ Agent 目录不存在，请先运行 test_phase6_iteration()")
        return
    
    report_manager = ReportManager(agent_dir)
    
    # 加载历史
    history = report_manager.load_history()
    
    print(f"\n📈 进化历史:")
    print(f"Agent 名称: {history.agent_name}")
    print(f"迭代次数: {len(history.iterations)}")
    
    for it in history.iterations:
        print(f"\n迭代 {it.iteration_id}:")
        print(f"  通过率: {it.pass_rate:.1%}")
        print(f"  通过: {it.passed_tests}/{it.total_tests}")
        print(f"  Git 提交: {it.git_commit_hash[:8] if it.git_commit_hash else 'N/A'}")
    
    # 显示改进总结
    improvement = history.get_improvement_summary()
    if improvement:
        print(f"\n📊 改进总结:")
        print(f"  初始通过率: {improvement['initial_pass_rate']:.1%}")
        print(f"  最终通过率: {improvement['final_pass_rate']:.1%}")
        print(f"  改进幅度: {improvement['improvement']:+.1%}")


if __name__ == "__main__":
    print("""
    Phase 6 测试选项:
    
    1. 完整端到端测试 (需要 API Key)
       - 创建 Agent
       - 运行测试
       - 用户交互
       - 查看报告
    
    2. 仅测试 ReportManager (需要已存在的 Agent)
       - 加载历史
       - 显示进化总结
    
    请选择: 1 或 2
    """)
    
    choice = input("选择 (1/2): ").strip()
    
    if choice == "1":
        print("\n⚠️ 请先在代码中设置 API Key!")
        print("修改 test_phase6_iteration() 中的 builder_api_key\n")
        
        confirm = input("已设置 API Key? (y/n): ").strip().lower()
        if confirm == 'y':
            asyncio.run(test_phase6_iteration())
        else:
            print("请设置 API Key 后重新运行")
    
    elif choice == "2":
        asyncio.run(test_report_manager())
    
    else:
        print("无效选择")
