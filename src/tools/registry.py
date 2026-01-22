"""Tool registry for managing and discovering tools."""

from typing import Dict, List, Optional, Callable, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool


class ToolMetadata(BaseModel):
    """Metadata for a registered tool."""
    
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    category: str = Field(default="general", description="Tool category")
    tags: List[str] = Field(default_factory=list, description="Tool tags for search")
    requires_api_key: bool = Field(default=False, description="Whether tool requires API key")


class ToolRegistry:
    """Registry for managing and discovering tools.
    
    The ToolRegistry provides:
    1. Tool registration and storage
    2. Tool discovery via semantic search
    3. Tool metadata management
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
    
    def register(
        self,
        tool: BaseTool,
        category: str = "general",
        tags: Optional[List[str]] = None,
        requires_api_key: bool = False,
    ) -> None:
        """Register a tool in the registry.
        
        Args:
            tool: LangChain BaseTool instance
            category: Tool category (e.g., 'search', 'math', 'file')
            tags: List of tags for semantic search
            requires_api_key: Whether tool requires API key
        """
        metadata = ToolMetadata(
            name=tool.name,
            description=tool.description,
            category=category,
            tags=tags or [],
            requires_api_key=requires_api_key,
        )
        
        self._tools[tool.name] = tool
        self._metadata[tool.name] = metadata
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            BaseTool instance or None if not found
        """
        return self._tools.get(name)
    
    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get tool metadata by name.
        
        Args:
            name: Tool name
            
        Returns:
            ToolMetadata or None if not found
        """
        return self._metadata.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """List all registered tool names, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of tool names
        """
        if category is None:
            return list(self._tools.keys())
        
        return [
            name for name, meta in self._metadata.items()
            if meta.category == category
        ]
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[str]:
        """Search for tools using semantic matching.
        
        Args:
            query: Search query
            top_k: Number of results to return
            category: Optional category filter
            
        Returns:
            List of matching tool names, ranked by relevance
        """
        # Simple keyword-based search (can be enhanced with embeddings)
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score each tool
        scores: List[tuple[str, float]] = []
        
        for name, metadata in self._metadata.items():
            # Skip if category filter doesn't match
            if category and metadata.category != category:
                continue
            
            score = 0.0
            
            # Exact name match
            if query_lower == name.lower():
                score += 10.0
            
            # Name contains query
            if query_lower in name.lower():
                score += 5.0
            
            # Description match
            desc_lower = metadata.description.lower()
            desc_words = set(desc_lower.split())
            
            # Count matching words
            matching_words = query_words & desc_words
            score += len(matching_words) * 2.0
            
            # Tag match
            for tag in metadata.tags:
                if query_lower in tag.lower():
                    score += 3.0
            
            if score > 0:
                scores.append((name, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        return [name for name, _ in scores[:top_k]]
    
    def get_tools_by_names(self, names: List[str]) -> List[BaseTool]:
        """Get multiple tools by their names.
        
        Args:
            names: List of tool names
            
        Returns:
            List of BaseTool instances (skips missing tools)
        """
        tools = []
        for name in names:
            tool = self.get_tool(name)
            if tool:
                tools.append(tool)
        return tools
    
    @property
    def tool_count(self) -> int:
        """Get total number of registered tools."""
        return len(self._tools)
    
    def get_categories(self) -> List[str]:
        """Get list of all categories."""
        categories = set(meta.category for meta in self._metadata.values())
        return sorted(list(categories))


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """Get the global tool registry instance.
    
    Returns:
        Global ToolRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(
    tool: BaseTool,
    category: str = "general",
    tags: Optional[List[str]] = None,
    requires_api_key: bool = False,
) -> None:
    """Register a tool in the global registry.
    
    Args:
        tool: LangChain BaseTool instance
        category: Tool category
        tags: List of tags for search
        requires_api_key: Whether tool requires API key
    """
    registry = get_global_registry()
    registry.register(tool, category, tags, requires_api_key)
