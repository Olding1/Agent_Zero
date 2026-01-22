import asyncio
import sys
from typing import List, Tuple
from pathlib import Path

from ..core.agent_factory import AgentFactory
from ..core.progress_callback import ProgressCallback
from ..schemas.graph_structure import GraphStructure
from ..schemas.simulation import SimulationResult

class CLIProgressCallback(ProgressCallback):
    """CLI 进度回调实现"""
    
    def on_step_start(self, step_name: str, step_num: int, total_steps: int):
        print(f"\n🚀 [步骤 {step_num}/{total_steps}] {step_name}...")
        
    def on_step_complete(self, step_name: str, result: any):
        print(f"✅ {step_name} 完成。")
        
        # 打印详细信息
        if hasattr(result, 'project_meta'): # AgentResult
             print(f"   📋 构建结果:")
             print(f"      - Agent名称: {result.agent_name}")
             print(f"      - 构建状态: {'成功' if result.success else '失败'}")
             if result.test_results:
                 print(f"      - 测试通过: {result.test_results.overall_status}")
             
        elif hasattr(result, 'task_type'): # ProjectMeta
            print(f"   📋 需求分析结果:")
            print(f"      - Agent名称: {result.agent_name}")
            print(f"      - 任务类型: {result.task_type}")
            print(f"      - RAG需求: {'是' if result.has_rag else '否'}")
            print(f"      - 用户意图: {result.user_intent_summary[:60]}...")
            
        elif isinstance(result, dict) and 'rag' in result: # Resource Config summary
            print(f"   🔧 资源配置:")
            print(f"      - RAG: {'启用' if result['rag'] else '禁用'}")
            print(f"      - 启用工具数: {result['tools']}")
        
    def on_step_error(self, step_name: str, error: Exception):
        print(f"❌ {step_name} 失败: {str(error)}")
        
    def on_clarification_needed(self, questions: List[str]):
        print("\n❓ 需要澄清:")
        for i, q in enumerate(questions, 1):
            print(f"   {i}. {q}")
        
    def on_blueprint_review(self, graph: GraphStructure, simulation_result: SimulationResult) -> Tuple[bool, str]:
        """
        蓝图评审
        Retruns: (approved, feedback)
        """
        print("\n👀 蓝图评审")
        print("="*30)
        print(f"模式: {graph.pattern.pattern_type}")
        print(f"节点数: {len(graph.nodes)} | 边数: {len(graph.edges)}")
        print("\n仿真结果:")
        print(f"成功: {simulation_result.success}")
        print(f"问题数: {len(simulation_result.issues)}")
        for issue in simulation_result.issues:
            print(f"  - [{issue.severity}] {issue.issue_type}: {issue.description}")

        print("\n命令:")
        print("  [y] 批准并构建")
        print("  [n] 拒绝 (退出)")
        print("  [text] 提供反馈以优化设计 (例如: '添加一个审核节点')")
        
        while True:
            choice = input("\n> ").strip()
            if not choice:
                continue
                
            if choice.lower() == 'y':
                return True, ""
            elif choice.lower() == 'n':
                return False, ""
            else:
                return False, choice

    def on_install_request(self) -> bool:
        print("\n📦 是否立即安装依赖并运行测试? (耗时较长)")
        print("   [y] 是, 安装并运行 (推荐)")
        print("   [n] 否, 仅生成代码")
        while True:
            choice = input("> ").strip().lower()
            if choice == 'y': return True
            if choice == 'n': return False
    
    def on_log(self, message: str):
        print(f"   ℹ️  {message}")


async def run_interactive_factory():
    """Run the Agent Factory in interactive mode."""
    print("\n🏭 Agent 工厂 - 交互模式")
    print("===================================\n")
    
    description = input("请输入您想构建的 Agent 描述:\n> ")
    if not description.strip():
        print("描述为空，正在退出。")
        return
        
    callback = CLIProgressCallback()
    factory = AgentFactory(callback=callback)
    
    # Optional: Ask for file paths
    files_input = input("\n是否有参考文件/文档? (逗号分隔路径，或留空):\n> ")
    file_paths = []
    if files_input.strip():
        import shlex
        # Use shlex to handle quotes correctly
        # Split by comma first to allow "file1", "file 2"
        # But if no comma, shlex handles space separation respecting quotes
        if ',' in files_input:
             raw_paths = [p.strip() for p in files_input.split(',')]
        else:
             try:
                 # Ensure paths with backslashes on Windows are handled by escaping them or using raw string logic
                 # shlex.split might consume backslashes. 
                 # Safer approach for Windows paths: simple split if no quotes, or use regex for spaces outside quotes.
                 # Actually, let's just use CSV-style parsing which is safer for file lists
                 import csv
                 reader = csv.reader([files_input], skipinitialspace=True)
                 raw_paths = list(reader)[0]
             except Exception:
                  # Fallback to simple split
                  raw_paths = files_input.split()

        # Clean up quotes and empty strings
        raw_paths = [p.strip().strip('"').strip("'") for p in raw_paths if p.strip()]
        file_paths = [str(Path(p).absolute()) for p in raw_paths]
    
    print("\n开始构建... (这可能需要几分钟)")
    
    try:
        result = await factory.create_agent(
            user_input=description,
            file_paths=file_paths if file_paths else None
        )
        
        print("\n===================================")
        if result.success:
            print(f"🎉 Agent 构建成功!")
            print(f"📂 位置: {result.agent_dir}")
            print(f"⏱️  耗时: {result.total_time:.1f}s")
            print(f"🔄 迭代次数: {result.iteration_count}")
        else:
            print(f"⚠️  Agent 已创建但存在问题。")
            if result.judge_feedback:
                print(f"裁判反馈: {result.judge_feedback.feedback}")
    except Exception as e:
        print(f"\n❌ 严重错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_interactive_factory())
