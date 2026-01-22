from typing import Protocol, List, Any, Dict, Optional
from ..schemas.simulation import SimulationResult
from ..schemas.graph_structure import GraphStructure
from ..schemas.test_report import IterationReport  # 🆕 Phase 6

class ProgressCallback(Protocol):
    """进度回调接口"""
    
    def on_step_start(self, step_name: str, step_num: int, total_steps: int):
        """步骤开始"""
        ...
        
    def on_step_complete(self, step_name: str, result: Any):
        """步骤完成"""
        ...
        
    def on_step_error(self, step_name: str, error: Exception):
        """步骤出错"""
        ...
        
    def on_clarification_needed(self, questions: List[str]):
        """需要澄清"""
        ...
        
    def on_blueprint_review(self, graph: GraphStructure, simulation_result: SimulationResult) -> tuple[bool, str]:
        """
        蓝图评审
        
        Returns:
            (approved, feedback): 
            - approved: True=批准, False=修改/驳回
            - feedback: 修改意见
        """
        ...
    
    def on_install_request(self) -> bool:
        """询问是否安装依赖"""
        ...
    
    def on_iteration_complete(
        self,
        iteration_report: IterationReport,
        analysis: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        迭代完成回调 (Phase 6)
        
        Args:
            iteration_report: 迭代报告
            analysis: LLM分析结果 (可选,Phase 2实现)
            
        Returns:
            (continue, user_feedback):
            - continue: True=继续迭代, False=停止
            - user_feedback: 用户额外的反馈意见
        """
        ...
        
    def on_log(self, message: str):
        """普通日志"""
        ...

