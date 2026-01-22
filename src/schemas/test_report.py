"""
Test Report Schemas - Phase 6

Defines data structures for test reports and iteration history.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.schemas.execution_result import ExecutionStatus
from src.schemas.judge_result import ErrorType, FixTarget


class TestCaseReport(BaseModel):
    """单个测试用例报告"""
    test_id: str = Field(description="测试用例ID")
    test_name: str = Field(description="测试用例名称")
    status: str = Field(description="测试状态: PASSED, FAILED, SKIPPED")
    
    # 指标
    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="测试指标, 例如: {'faithfulness': 0.8, 'recall': 0.6}"
    )
    
    # 测试内容
    actual_output: str = Field(default="", description="实际输出")
    expected_output: str = Field(default="", description="期望输出")
    retrieval_context: List[str] = Field(
        default_factory=list,
        description="检索到的上下文文档"
    )
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误消息")
    
    # 性能
    duration_seconds: float = Field(default=0.0, description="执行时长(秒)")


class IterationReport(BaseModel):
    """单次迭代报告"""
    iteration_id: int = Field(description="迭代编号")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    agent_name: str = Field(description="Agent名称")
    
    # 测试结果汇总
    total_tests: int = Field(description="总测试数")
    passed_tests: int = Field(description="通过测试数")
    failed_tests: int = Field(description="失败测试数")
    skipped_tests: int = Field(default=0, description="跳过测试数")
    pass_rate: float = Field(description="通过率 (0.0-1.0)")
    
    # 详细测试用例
    test_cases: List[TestCaseReport] = Field(
        default_factory=list,
        description="所有测试用例详情"
    )
    
    # Judge分析
    error_types: Dict[str, int] = Field(
        default_factory=dict,
        description="错误类型统计, 例如: {'runtime': 2, 'logic': 1}"
    )
    fix_target: Optional[str] = Field(None, description="修复目标")
    judge_feedback: str = Field(default="", description="Judge反馈")
    
    # 配置快照
    graph_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Graph结构快照"
    )
    rag_config_snapshot: Optional[Dict[str, Any]] = Field(
        None,
        description="RAG配置快照"
    )
    tools_config_snapshot: Optional[Dict[str, Any]] = Field(
        None,
        description="工具配置快照"
    )
    
    # Git信息
    git_commit_hash: Optional[str] = Field(None, description="Git提交哈希")
    git_commit_message: Optional[str] = Field(None, description="Git提交消息")
    
    # 平均指标
    avg_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="平均指标, 例如: {'avg_faithfulness': 0.75}"
    )


class AgentEvolutionHistory(BaseModel):
    """Agent进化历史"""
    agent_name: str = Field(description="Agent名称")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    iterations: List[IterationReport] = Field(
        default_factory=list,
        description="所有迭代报告"
    )
    
    def get_pass_rate_trend(self) -> List[float]:
        """获取通过率趋势"""
        return [it.pass_rate for it in self.iterations]
    
    def get_metric_trend(self, metric_name: str) -> List[float]:
        """获取指定指标的趋势
        
        Args:
            metric_name: 指标名称, 例如 'avg_faithfulness'
            
        Returns:
            指标值列表
        """
        return [
            it.avg_metrics.get(metric_name, 0.0)
            for it in self.iterations
        ]
    
    def get_latest_iteration(self) -> Optional[IterationReport]:
        """获取最新的迭代报告"""
        return self.iterations[-1] if self.iterations else None
    
    def get_improvement_summary(self) -> Dict[str, Any]:
        """获取改进总结
        
        Returns:
            包含初始/最终通过率和改进幅度的字典
        """
        if not self.iterations:
            return {}
        
        first = self.iterations[0]
        last = self.iterations[-1]
        
        return {
            "total_iterations": len(self.iterations),
            "initial_pass_rate": first.pass_rate,
            "final_pass_rate": last.pass_rate,
            "improvement": last.pass_rate - first.pass_rate,
            "initial_passed": first.passed_tests,
            "final_passed": last.passed_tests,
        }
