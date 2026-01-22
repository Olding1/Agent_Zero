from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .project_meta import ProjectMeta
from .graph_structure import GraphStructure
from .rag_config import RAGConfig
from .tools_config import ToolsConfig
from .simulation import SimulationResult
from .execution_result import ExecutionResult
from .judge_result import JudgeResult

class AgentResult(BaseModel):
    """Agent 生成结果"""
    
    # 基础信息
    agent_name: str = Field(..., description="Agent 名称")
    agent_dir: Path = Field(..., description="Agent 目录路径")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 过程数据
    project_meta: ProjectMeta = Field(..., description="项目元数据")
    graph: Optional[GraphStructure] = Field(default=None, description="图结构")
    rag_config: Optional[RAGConfig] = Field(default=None, description="RAG 配置")
    tools_config: Optional[ToolsConfig] = Field(default=None, description="工具配置")
    
    # 仿真结果
    simulation_result: Optional[SimulationResult] = Field(default=None, description="最终的仿真结果")
    
    # 最终状态
    success: bool = Field(default=False, description="是否完全成功")
    generated_files: List[str] = Field(default_factory=list, description="生成的文件列表")
    
    # 测试与评价
    test_results: Optional[ExecutionResult] = Field(default=None, description="最终测试执行结果")
    judge_feedback: Optional[JudgeResult] = Field(default=None, description="最终 Judge 反馈")
    
    # 版本信息
    git_version: Optional[str] = Field(default=None, description="Git 版本标签")
    
    # 统计信息
    total_time: float = Field(default=0.0, description="总耗时 (秒)")
    steps_completed: int = Field(default=0, description="完成的步骤数")
    iteration_count: int = Field(default=0, description="自动迭代修正次数")
