"""
Phase 6 Task 6.3: Analysis Result Schema

Defines data structures for LLM-based test analysis results.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class FixStep(BaseModel):
    """单个修复步骤"""
    step: int = Field(description="步骤序号")
    target: str = Field(description="修复目标: rag_builder, graph_designer, tool_selector, compiler")
    action: str = Field(description="具体的修复动作描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="修复参数")
    expected_improvement: str = Field(description="预期改进效果")
    priority: str = Field(default="medium", description="优先级: high, medium, low")


class AnalysisResult(BaseModel):
    """LLM 分析结果"""
    primary_issue: str = Field(description="主要问题描述")
    root_cause: str = Field(description="根本原因分析")
    fix_strategy: List[FixStep] = Field(
        default_factory=list,
        description="修复策略列表,按优先级排序"
    )
    estimated_success_rate: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="预计成功率 (0.0-1.0)"
    )
    user_feedback: Optional[str] = Field(None, description="用户反馈")
