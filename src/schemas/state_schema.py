"""
状态定义模型

定义了 LangGraph Agent 的状态结构。
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any
from enum import Enum


class StateFieldType(str, Enum):
    """状态字段类型"""
    STRING = "str"
    INT = "int"
    BOOL = "bool"
    FLOAT = "float"
    LIST_MESSAGE = "List[BaseMessage]"
    LIST_STR = "List[str]"
    DICT = "Dict[str, Any]"
    OPTIONAL_STR = "Optional[str]"
    OPTIONAL_INT = "Optional[int]"
    OPTIONAL_FLOAT = "Optional[float]"
    OPTIONAL_DICT = "Optional[Dict[str, Any]]"
    ANY = "Any"


class StateField(BaseModel):
    """状态字段定义"""
    
    name: str = Field(
        ..., 
        description="字段名称，如 'messages', 'retry_count'"
    )
    
    type: StateFieldType = Field(
        ..., 
        description="字段类型"
    )
    
    description: Optional[str] = Field(
        None, 
        description="字段说明"
    )
    
    default: Optional[Any] = Field(
        None, 
        description="默认值"
    )
    
    reducer: Optional[str] = Field(
        None, 
        description="归约函数名称，如 'add_messages' 用于消息累积"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "messages",
                "type": "List[BaseMessage]",
                "description": "对话历史",
                "reducer": "add_messages"
            }
        }
    )


class StateSchema(BaseModel):
    """完整状态定义"""
    
    fields: List[StateField] = Field(
        ..., 
        min_length=1,
        description="状态字段列表，至少包含一个字段"
    )
    
    def get_field(self, name: str) -> Optional[StateField]:
        """根据名称获取字段"""
        for field in self.fields:
            if field.name == name:
                return field
        return None
    
    def has_field(self, name: str) -> bool:
        """检查是否存在指定字段"""
        return self.get_field(name) is not None
    
model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fields": [
                    {
                        "name": "messages",
                        "type": "List[BaseMessage]",
                        "description": "对话历史",
                        "reducer": "add_messages"
                    },
                    {
                        "name": "draft",
                        "type": "str",
                        "description": "当前草稿内容",
                        "default": ""
                    },
                    {
                        "name": "iteration_count",
                        "type": "int",
                        "description": "迭代次数",
                        "default": 0
                    },
                    {
                        "name": "is_finished",
                        "type": "bool",
                        "description": "是否完成",
                        "default": False
                    }
                ]
            }
        }
    )
