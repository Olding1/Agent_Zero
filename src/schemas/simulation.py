"""
仿真结果模型

定义了沙盘推演的结果结构。
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from datetime import datetime


class SimulationStepType(str, Enum):
    """仿真步骤类型"""
    ENTER_NODE = "enter_node"          # 进入节点
    EXIT_NODE = "exit_node"            # 退出节点
    STATE_UPDATE = "state_update"      # 状态更新
    CONDITION_CHECK = "condition_check"  # 条件检查
    EDGE_TRAVERSE = "edge_traverse"    # 边遍历


class SimulationStep(BaseModel):
    """A single step in the simulation trace.
    
    Attributes:
        step_number: Step number (can be fractional like 1.5 for exit nodes)
        step_type: Type of step
        node_id: Node ID if applicable
        description: Human-readable description
        state_snapshot: State at this step
    """
    
    step_number: float = Field(..., description="Step number (supports fractional steps)")
    
    step_type: SimulationStepType = Field(
        ..., 
        description="Type of simulation step"
    )
    
    node_id: Optional[str] = Field(
        None, 
        description="Node ID if applicable"
    )
    
    description: str = Field(
        ..., 
        description="Human-readable description of this step"
    )
    
    state_snapshot: Optional[Dict[str, Any]] = Field(
        None, 
        description="State snapshot at this step"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "step_number": 1,
                "step_type": "enter_node",
                "node_id": "generator",
                "description": "进入 generator 节点，准备生成初始内容",
                "state_snapshot": {
                    "messages": [],
                    "draft": "",
                    "iteration_count": 0
                }
            }
        }
    )


class SimulationIssue(BaseModel):
    """仿真发现的问题"""
    
    issue_type: Literal[
        "infinite_loop",      # 无限循环
        "unreachable_node",   # 不可达节点
        "missing_edge",       # 缺失边
        "invalid_condition",  # 无效条件
        "state_not_updated"   # 状态未更新
    ] = Field(
        ..., 
        description="问题类型"
    )
    
    severity: Literal["error", "warning"] = Field(
        ..., 
        description="严重程度"
    )
    
    description: str = Field(
        ..., 
        description="问题描述"
    )
    
    affected_nodes: List[str] = Field(
        default_factory=list, 
        description="受影响的节点列表"
    )
    
    suggestion: Optional[str] = Field(
        None, 
        description="修复建议"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "issue_type": "infinite_loop",
                "severity": "error",
                "description": "检测到无限循环：generator -> critic -> generator 循环超过5次",
                "affected_nodes": ["generator", "critic"],
                "suggestion": "在状态中添加 iteration_count 并设置最大迭代次数"
            }
        }
    )


class SimulationResult(BaseModel):
    """仿真结果"""
    
    success: bool = Field(
        ..., 
        description="仿真是否成功完成"
    )
    
    total_steps: int = Field(
        ..., 
        description="总步骤数"
    )
    
    steps: List[SimulationStep] = Field(
        default_factory=list, 
        description="详细步骤列表"
    )
    
    issues: List[SimulationIssue] = Field(
        default_factory=list, 
        description="发现的问题列表"
    )
    
    final_state: Optional[Dict[str, Any]] = Field(
        None, 
        description="最终状态"
    )
    
    execution_trace: str = Field(
        ..., 
        description="可读的执行轨迹文本"
    )
    
    mermaid_trace: Optional[str] = Field(
        None, 
        description="Mermaid 格式的轨迹图"
    )
    
    simulated_at: datetime = Field(
        default_factory=datetime.now, 
        description="仿真时间"
    )
    
    def has_errors(self) -> bool:
        """是否有错误级别的问题"""
        return any(issue.severity == "error" for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """是否有警告级别的问题"""
        return any(issue.severity == "warning" for issue in self.issues)
    
    def get_issues_by_type(self, issue_type: str) -> List[SimulationIssue]:
        """获取指定类型的问题"""
        return [issue for issue in self.issues if issue.issue_type == issue_type]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "total_steps": 8,
                "steps": [],
                "issues": [],
                "final_state": {"is_finished": True},
                "execution_trace": "Step 1: Enter generator...\nStep 2: Exit generator...",
                "mermaid_trace": "graph LR\n  A[generator] --> B[critic]",
                "simulated_at": "2026-01-14T13:50:00"
            }
        }
    )
