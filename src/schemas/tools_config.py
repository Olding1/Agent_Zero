"""Tools configuration schema."""

from pydantic import BaseModel, Field, ConfigDict
from typing import List


class ToolsConfig(BaseModel):
    """Tools configuration schema.
    
    Defines which tools are enabled for the agent.
    """

    enabled_tools: List[str] = Field(
        default_factory=list, description="List of enabled tool identifiers"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "enabled_tools": ["tavily_search_results_json", "llm_math_chain"]
            }
        }
    )
