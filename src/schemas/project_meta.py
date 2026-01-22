"""Project metadata schema."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from enum import Enum


class TaskType(str, Enum):
    """Type of task the agent will perform."""

    CHAT = "chat"
    SEARCH = "search"
    ANALYSIS = "analysis"
    RAG = "rag"
    CUSTOM = "custom"


class ExecutionStep(BaseModel):
    """Execution plan step.
    
    Represents a single step in the hierarchical task breakdown.
    """
    
    step: int = Field(..., description="Step number")
    role: str = Field(..., description="Role name (Architect/Coder/Tester/etc)")
    goal: str = Field(..., description="Step goal")
    expected_output: Optional[str] = Field(None, description="Expected output")


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
    
    # New fields for PM dual-brain mode
    status: Literal["clarifying", "ready"] = Field(
        default="ready", description="PM analysis status"
    )
    complexity_score: int = Field(
        default=1, ge=1, le=10, description="Task complexity score (1-10)"
    )
    execution_plan: Optional[List[ExecutionStep]] = Field(
        default=None, description="Hierarchical task breakdown"
    )

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "agent_name": "StockBot",
                "description": "Query and analyze stock information",
                "has_rag": False,
                "task_type": "search",
                "language": "zh-CN",
                "user_intent_summary": "User wants to build a stock query assistant",
            }
        }
    )
