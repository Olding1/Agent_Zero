"""
设计模式配置模型

定义了 Agent 可使用的设计模式类型和配置。
"""

from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import Optional


class PatternType(str, Enum):
    """设计模式类型"""
    SEQUENTIAL = "sequential"      # A -> B -> C 顺序执行
    REFLECTION = "reflection"      # Generate <-> Critique 生成-批评循环
    SUPERVISOR = "supervisor"      # Manager -> [Workers] -> Manager 主管调度
    PLAN_EXECUTE = "plan_execute"  # Planner -> Executor -> Replanner 规划-执行
    CUSTOM = "custom"              # 自定义模式


class PatternConfig(BaseModel):
    """设计模式配置"""
    
    pattern_type: PatternType = Field(
        ..., 
        description="模式类型"
    )
    
    max_iterations: int = Field(
        default=3, 
        ge=1, 
        le=10, 
        description="最大循环次数，防止死循环"
    )
    
    termination_condition: Optional[str] = Field(
        None, 
        description="终止条件表达式，如 'is_finished == True'"
    )
    
    description: str = Field(
        default="", 
        description="模式说明"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pattern_type": "reflection",
                "max_iterations": 3,
                "termination_condition": "is_finished == True or iteration_count >= max_iterations",
                "description": "生成-批评循环模式，适用于需要迭代改进的任务"
            }
        },
        use_enum_values=True
    )
