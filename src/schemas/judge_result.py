from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class ErrorType(str, Enum):
    """错误类型"""
    RUNTIME = "runtime"  # 运行时错误 (语法错误, 导入错误等)
    LOGIC = "logic"  # 逻辑错误 (RAG 检索失败, 工具调用错误等)
    TIMEOUT = "timeout"  # 超时
    API = "api"  # API 调用失败
    NONE = "none"  # 无错误
    
    # 🆕 Phase 6: RAG 相关错误
    RAG_QUALITY = "rag_quality"  # RAG 检索质量问题 (Recall 低, Faithfulness 低)
    RAG_CONFIG = "rag_config"  # RAG 配置问题 (chunk_size, retriever_k 不合适)
    
    # 🆕 Phase 6: 工具相关错误
    TOOL_ERROR = "tool_error"  # 工具调用错误
    TOOL_CONFIG = "tool_config"  # 工具配置问题 (选择了不合适的工具)


class FixTarget(str, Enum):
    """修复目标"""
    COMPILER = "compiler"  # 需要 Compiler 修复 (代码生成问题)
    GRAPH_DESIGNER = "graph_designer"  # 需要 Graph Designer 修复 (图结构问题)
    MANUAL = "manual"  # 需要人工修复
    NONE = "none"  # 无需修复
    
    # 🆕 Phase 6: 新增修复目标
    RAG_BUILDER = "rag_builder"  # 需要 RAG Builder 优化配置
    TOOL_SELECTOR = "tool_selector"  # 需要 Tool Selector 重新选择工具
    HYBRID = "hybrid"  # 需要多个组件协同修复


class JudgeResult(BaseModel):
    """Judge 分析结果"""
    error_type: ErrorType = Field(description="错误类型")
    fix_target: FixTarget = Field(description="修复目标")
    feedback: str = Field(description="反馈信息")
    suggestions: List[str] = Field(default_factory=list, description="修复建议")
    should_retry: bool = Field(default=False, description="是否应该重试")
