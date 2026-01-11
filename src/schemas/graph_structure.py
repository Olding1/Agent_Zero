"""Graph structure schema for LangGraph topology."""

from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Optional, Literal


class NodeDef(BaseModel):
    """Graph node definition.
    
    Represents a single node in the LangGraph topology.
    """

    id: str = Field(..., description="Unique node identifier")
    type: Literal["llm", "tool", "rag", "conditional", "custom"] = Field(
        ..., description="Node type"
    )
    config: Optional[Dict] = Field(default=None, description="Node configuration")


class EdgeDef(BaseModel):
    """Regular edge definition.
    
    Represents a direct connection between two nodes.
    """

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")


class ConditionalEdgeDef(BaseModel):
    """Conditional edge definition.
    
    Represents a conditional branch in the graph flow.
    """

    source: str = Field(..., description="Source node ID")
    condition: str = Field(..., description="Condition function name")
    branches: Dict[str, str] = Field(
        ..., description="Branch mapping {condition_value: target_node}"
    )


class GraphStructure(BaseModel):
    """Complete graph structure definition.
    
    Defines the entire LangGraph topology including nodes, edges,
    and conditional branches.
    """

    nodes: List[NodeDef] = Field(..., min_length=1, description="Node list")
    edges: List[EdgeDef] = Field(default_factory=list, description="Regular edge list")
    conditional_edges: List[ConditionalEdgeDef] = Field(
        default_factory=list, description="Conditional edge list"
    )
    entry_point: str = Field(default="agent", description="Entry node ID")

    @model_validator(mode="after")
    def validate_graph(self) -> "GraphStructure":
        """Validate graph integrity.
        
        Ensures all edge references point to valid nodes.
        """
        node_ids = {node.id for node in self.nodes}

        # Validate regular edges
        for edge in self.edges:
            if edge.source not in node_ids:
                raise ValueError(f"Edge source '{edge.source}' not found in nodes")
            if edge.target not in node_ids and edge.target != "END":
                raise ValueError(f"Edge target '{edge.target}' not found in nodes")

        # Validate conditional edges
        for cond_edge in self.conditional_edges:
            if cond_edge.source not in node_ids:
                raise ValueError(
                    f"Conditional edge source '{cond_edge.source}' not found in nodes"
                )
            for branch_target in cond_edge.branches.values():
                if branch_target not in node_ids and branch_target != "END":
                    raise ValueError(
                        f"Conditional edge target '{branch_target}' not found in nodes"
                    )

        # Validate entry point
        if self.entry_point not in node_ids:
            raise ValueError(f"Entry point '{self.entry_point}' not found in nodes")

        return self

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "nodes": [
                    {"id": "agent", "type": "llm"},
                    {"id": "action", "type": "tool"},
                ],
                "edges": [{"source": "action", "target": "agent"}],
                "conditional_edges": [
                    {
                        "source": "agent",
                        "condition": "should_continue",
                        "branches": {"continue": "action", "end": "END"},
                    }
                ],
                "entry_point": "agent",
            }
        }
