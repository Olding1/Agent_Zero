"""
Report Manager - Phase 6

Manages test reports and iteration history.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from src.schemas.test_report import (
    TestCaseReport,
    IterationReport,
    AgentEvolutionHistory
)


class ReportManager:
    """测试报告管理器"""
    
    def __init__(self, agent_dir: Path):
        """初始化报告管理器
        
        Args:
            agent_dir: Agent目录路径
        """
        self.agent_dir = Path(agent_dir)
        self.reports_dir = self.agent_dir / ".reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # 历史文件
        self.history_file = self.reports_dir / "history.json"
    
    def save_iteration_report(self, report: IterationReport) -> Path:
        """保存迭代报告
        
        Args:
            report: 迭代报告
            
        Returns:
            报告文件路径
        """
        # 生成文件名
        timestamp_str = report.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"iteration_{report.iteration_id}_{timestamp_str}.json"
        filepath = self.reports_dir / filename
        
        # 保存报告
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(
                report.model_dump(mode='json'),
                f,
                indent=2,
                ensure_ascii=False,
                default=str  # 处理datetime等特殊类型
            )
        
        # 更新历史
        self._update_history(report)
        
        return filepath
    
    def load_iteration_report(self, iteration_id: int) -> Optional[IterationReport]:
        """加载指定迭代的报告
        
        Args:
            iteration_id: 迭代编号
            
        Returns:
            迭代报告,如果不存在返回None
        """
        # 查找匹配的文件
        pattern = f"iteration_{iteration_id}_*.json"
        matching_files = list(self.reports_dir.glob(pattern))
        
        if not matching_files:
            return None
        
        # 取最新的文件
        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return IterationReport.model_validate(data)
    
    def load_history(self) -> AgentEvolutionHistory:
        """加载完整历史
        
        Returns:
            Agent进化历史
        """
        if not self.history_file.exists():
            # 如果历史文件不存在,从报告文件重建
            return self._rebuild_history()
        
        with open(self.history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return AgentEvolutionHistory.model_validate(data)
    
    def _update_history(self, report: IterationReport):
        """更新历史文件
        
        Args:
            report: 新的迭代报告
        """
        # 加载现有历史
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            history = AgentEvolutionHistory.model_validate(data)
        else:
            history = AgentEvolutionHistory(
                agent_name=report.agent_name,
                created_at=datetime.now(),
                iterations=[]
            )
        
        # 检查是否已存在该迭代
        existing_idx = None
        for i, it in enumerate(history.iterations):
            if it.iteration_id == report.iteration_id:
                existing_idx = i
                break
        
        if existing_idx is not None:
            # 更新现有迭代
            history.iterations[existing_idx] = report
        else:
            # 添加新迭代
            history.iterations.append(report)
        
        # 保存历史
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(
                history.model_dump(mode='json'),
                f,
                indent=2,
                ensure_ascii=False,
                default=str
            )
    
    def _rebuild_history(self) -> AgentEvolutionHistory:
        """从报告文件重建历史
        
        Returns:
            重建的历史
        """
        # 获取所有报告文件
        report_files = sorted(self.reports_dir.glob("iteration_*.json"))
        
        if not report_files:
            return AgentEvolutionHistory(
                agent_name=self.agent_dir.name,
                created_at=datetime.now(),
                iterations=[]
            )
        
        # 加载所有报告
        iterations = []
        for filepath in report_files:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            iterations.append(IterationReport.model_validate(data))
        
        # 按迭代ID排序
        iterations.sort(key=lambda x: x.iteration_id)
        
        history = AgentEvolutionHistory(
            agent_name=iterations[0].agent_name if iterations else self.agent_dir.name,
            created_at=iterations[0].timestamp if iterations else datetime.now(),
            iterations=iterations
        )
        
        # 保存重建的历史
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(
                history.model_dump(mode='json'),
                f,
                indent=2,
                ensure_ascii=False,
                default=str
            )
        
        return history
    
    def generate_summary(self, iteration_id: int) -> str:
        """生成迭代总结
        
        Args:
            iteration_id: 迭代编号
            
        Returns:
            格式化的总结文本
        """
        report = self.load_iteration_report(iteration_id)
        if not report:
            return f"❌ 未找到迭代 {iteration_id} 的报告"
        
        # 格式化错误类型统计
        error_types_str = ""
        if report.error_types:
            for error_type, count in report.error_types.items():
                error_types_str += f"     - {error_type}: {count}\n"
        else:
            error_types_str = "     无错误\n"
        
        # 格式化失败的测试
        failed_tests_str = ""
        if report.failed_tests > 0:
            failed_cases = [tc for tc in report.test_cases if tc.status == "FAILED"]
            for tc in failed_cases[:5]:  # 最多显示5个
                failed_tests_str += f"     - {tc.test_name}\n"
                if tc.error_message:
                    error_preview = tc.error_message[:80].replace('\n', ' ')
                    failed_tests_str += f"       错误: {error_preview}...\n"
            
            if len(failed_cases) > 5:
                failed_tests_str += f"     ... 还有 {len(failed_cases) - 5} 个失败测试\n"
        
        # 生成总结
        summary = f"""
{'='*60}
📊 迭代 {iteration_id} 总结
{'='*60}

🧪 测试结果:
   - 总测试数: {report.total_tests}
   - 通过: {report.passed_tests} ✅
   - 失败: {report.failed_tests} ❌
   - 跳过: {report.skipped_tests} ⏭️
   - 通过率: {report.pass_rate:.1%}

🔍 错误分析:
{error_types_str}
🎯 修复目标: {report.fix_target or '无'}

💡 Judge反馈:
   {report.judge_feedback[:200] if report.judge_feedback else '无'}...

"""
        
        if failed_tests_str:
            summary += f"""❌ 失败的测试:
{failed_tests_str}
"""
        
        if report.git_commit_hash:
            summary += f"""📦 Git提交: {report.git_commit_hash[:8]}
   消息: {report.git_commit_message}

"""
        
        summary += "=" * 60
        
        return summary
    
    def generate_evolution_summary(self) -> str:
        """生成进化总结
        
        Returns:
            格式化的进化总结文本
        """
        history = self.load_history()
        
        if not history.iterations:
            return "📊 暂无迭代历史"
        
        improvement = history.get_improvement_summary()
        
        summary = f"""
{'='*60}
📈 Agent 进化总结: {history.agent_name}
{'='*60}

📊 总体统计:
   - 总迭代次数: {improvement['total_iterations']}
   - 初始通过率: {improvement['initial_pass_rate']:.1%}
   - 最终通过率: {improvement['final_pass_rate']:.1%}
   - 改进幅度: {improvement['improvement']:+.1%}
   - 初始通过: {improvement['initial_passed']} 个测试
   - 最终通过: {improvement['final_passed']} 个测试

📉 通过率趋势:
"""
        
        # 显示每次迭代的通过率
        for it in history.iterations:
            bar_length = int(it.pass_rate * 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            summary += f"   迭代 {it.iteration_id}: {bar} {it.pass_rate:.1%}\n"
        
        summary += "\n" + "=" * 60
        
        return summary
