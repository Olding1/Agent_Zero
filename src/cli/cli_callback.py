"""
CLI Callback Implementation - Phase 6

Provides interactive user confirmation during iteration loop.
"""

from typing import List, Any, Dict, Optional
from src.core.progress_callback import ProgressCallback
from src.schemas.simulation import SimulationResult
from src.schemas.graph_structure import GraphStructure
from src.schemas.test_report import IterationReport


class CLICallback:
    """CLI进度回调实现"""
    
    def on_step_start(self, step_name: str, step_num: int, total_steps: int):
        """步骤开始"""
        print(f"\n🚀 [步骤 {step_num}/{total_steps}] {step_name}...")
    
    def on_step_complete(self, step_name: str, result: Any):
        """步骤完成"""
        print(f"✅ {step_name} 完成。")
        if hasattr(result, '__dict__'):
            # 显示结果的简要信息
            for key, value in result.__dict__.items():
                if not key.startswith('_'):
                    print(f"   {key}: {value}")
    
    def on_step_error(self, step_name: str, error: Exception):
        """步骤出错"""
        print(f"❌ {step_name} 失败: {error}")
    
    def on_clarification_needed(self, questions: List[str]):
        """需要澄清"""
        print("\n❓ 需要澄清:")
        for i, q in enumerate(questions, 1):
            print(f"   {i}. {q}")
    
    def on_blueprint_review(
        self,
        graph: GraphStructure,
        simulation_result: SimulationResult
    ) -> tuple[bool, str]:
        """蓝图评审"""
        print("\n" + "="*70)
        print("👀 蓝图评审")
        print("="*70)
        print(f"模式: {graph.pattern}")
        print(f"节点数: {len(graph.nodes)} | 边数: {len(graph.edges)}")
        
        print("\n仿真结果:")
        print(f"成功: {simulation_result.success}")
        print(f"问题数: {len(simulation_result.issues)}")
        
        if simulation_result.issues:
            print("\n⚠️ 发现的问题:")
            for issue in simulation_result.issues[:3]:
                print(f"   - {issue.severity}: {issue.message}")
        
        print("\n命令:")
        print("  [y] 批准并构建")
        print("  [n] 拒绝 (退出)")
        print("  [text] 提供反馈以优化设计 (例如: '添加一个审核节点')")
        
        choice = input("\n> ").strip().lower()
        
        if choice == 'y':
            return True, ""
        elif choice == 'n':
            return False, "用户拒绝"
        else:
            return False, choice
    
    def on_install_request(self) -> bool:
        """询问是否安装依赖"""
        print("\n📦 是否立即安装依赖并运行测试? (耗时较长)")
        print("   [y] 是, 安装并运行 (推荐)")
        print("   [n] 否, 仅生成代码")
        
        choice = input("> ").strip().lower()
        return choice == 'y'
    
    def on_iteration_complete(
        self,
        iteration_report: IterationReport,
        analysis: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        迭代完成回调 (Phase 6)
        
        显示测试结果并询问用户是否继续迭代
        """
        print("\n" + "="*70)
        print(f"📊 迭代 {iteration_report.iteration_id} 完成")
        print("="*70)
        
        # 1. 显示测试结果
        print(f"\n🧪 测试结果:")
        print(f"   通过率: {iteration_report.pass_rate:.1%}")
        print(f"   通过: {iteration_report.passed_tests}/{iteration_report.total_tests} ✅")
        print(f"   失败: {iteration_report.failed_tests}/{iteration_report.total_tests} ❌")
        
        if iteration_report.skipped_tests > 0:
            print(f"   跳过: {iteration_report.skipped_tests}/{iteration_report.total_tests} ⏭️")
        
        # 2. 显示失败的测试
        if iteration_report.failed_tests > 0:
            print(f"\n❌ 失败的测试:")
            failed_cases = [tc for tc in iteration_report.test_cases if tc.status == "FAILED"]
            
            for tc in failed_cases[:5]:  # 最多显示5个
                print(f"   - {tc.test_name}")
                if tc.error_message:
                    error_preview = tc.error_message[:80].replace('\n', ' ')
                    print(f"     原因: {error_preview}...")
            
            if len(failed_cases) > 5:
                print(f"   ... 还有 {len(failed_cases) - 5} 个失败测试")
        
        # 3. 显示错误分析
        if iteration_report.error_types:
            print(f"\n🔍 错误分析:")
            for error_type, count in iteration_report.error_types.items():
                print(f"   - {error_type}: {count}")
        
        # 4. 显示修复建议
        if iteration_report.fix_target:
            print(f"\n🎯 修复目标: {iteration_report.fix_target}")
        
        if iteration_report.judge_feedback:
            feedback_preview = iteration_report.judge_feedback[:150]
            print(f"\n💡 Judge反馈:")
            print(f"   {feedback_preview}...")
        
        # 5. 🆕 Phase 2: 显示LLM分析 (如果有)
        if analysis:
            print(f"\n🤖 AI分析:")
            if "primary_issue" in analysis:
                print(f"   主要问题: {analysis['primary_issue']}")
            
            if "fix_strategy" in analysis:
                print(f"\n💡 修复策略:")
                for i, step in enumerate(analysis['fix_strategy'][:3], 1):
                    print(f"   {i}. {step.get('action', 'N/A')}")
                    print(f"      目标: {step.get('target', 'N/A')}")
                    if 'expected_improvement' in step:
                        print(f"      预期改进: {step['expected_improvement']}")
            
            if "estimated_success_rate" in analysis:
                print(f"\n📈 预计成功率: {analysis['estimated_success_rate']:.1%}")
        
        # 6. 询问用户
        print("\n" + "="*70)
        print("命令:")
        print("  [y] 继续迭代优化")
        print("  [n] 停止迭代")
        print("  [feedback] 提供反馈意见后继续")
        
        choice = input("\n是否继续迭代优化? (y/n/feedback): ").strip().lower()
        
        if choice == 'y':
            return True, None
        elif choice == 'n':
            return False, None
        elif choice == 'feedback':
            feedback = input("请输入您的反馈意见: ").strip()
            return True, feedback
        else:
            # 默认停止
            return False, None
    
    def on_log(self, message: str):
        """普通日志"""
        print(f"   ℹ️  {message}")
