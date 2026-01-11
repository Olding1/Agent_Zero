"""Project metadata schema."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class TaskType(str, Enum):
    """Type of task the agent will perform."""

    CHAT = "chat"
    SEARCH = "search"
    ANALYSIS = "analysis"
    RAG = "rag"
    CUSTOM = "custom"


class ProjectMeta(BaseModel):
    """PM node output - project metadata.
    
    This schema defines the core information about an agent project,
    including its purpose, capabilities, and requirements.
    """

    agent_name: str = Field(
        ..., description="Agent name", min_length=1, max_length=50
    )
    description: str = Field(..., description="Agent functionality description")
    has_rag: bool = Field(default=False, description="Whether RAG is needed")
    task_type: TaskType = Field(default=TaskType.CHAT, description="Task type")
    language: str = Field(default="zh-CN", description="Primary language")
    user_intent_summary: str = Field(..., description="User intent summary")
    file_paths: Optional[List[str]] = Field(
        default=None, description="User uploaded file paths"
    )
    clarification_needed: bool = Field(
        default=False, description="Whether further clarification is needed"
    )
    clarification_questions: Optional[List[str]] = Field(
        default=None, description="List of clarification questions"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "agent_name": "StockBot",
                "description": "Query and analyze stock information",
                "has_rag": False,
                "task_type": "search",
                "language": "zh-CN",
                "user_intent_summary": "User wants to build a stock query assistant",
            }
        }
