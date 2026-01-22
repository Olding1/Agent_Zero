"""Unit tests for Tool Registry."""

import pytest
from src.tools.registry import ToolRegistry, ToolMetadata
from src.tools.preset_tools import CalculatorTool, FileReadTool


@pytest.fixture
def registry():
    """Create a fresh tool registry."""
    return ToolRegistry()


@pytest.fixture
def calculator_tool():
    """Create a calculator tool."""
    return CalculatorTool()


@pytest.fixture
def file_read_tool():
    """Create a file read tool."""
    return FileReadTool()


def test_register_tool(registry, calculator_tool):
    """Test registering a tool."""
    registry.register(
        calculator_tool,
        category="math",
        tags=["calculator", "math"],
    )
    
    assert registry.tool_count == 1
    assert "calculator" in registry.list_tools()


def test_get_tool(registry, calculator_tool):
    """Test getting a registered tool."""
    registry.register(calculator_tool, category="math")
    
    tool = registry.get_tool("calculator")
    assert tool is not None
    assert tool.name == "calculator"


def test_get_metadata(registry, calculator_tool):
    """Test getting tool metadata."""
    registry.register(
        calculator_tool,
        category="math",
        tags=["calculator", "math"],
    )
    
    metadata = registry.get_metadata("calculator")
    assert metadata is not None
    assert metadata.name == "calculator"
    assert metadata.category == "math"
    assert "calculator" in metadata.tags


def test_list_tools_by_category(registry, calculator_tool, file_read_tool):
    """Test listing tools by category."""
    registry.register(calculator_tool, category="math")
    registry.register(file_read_tool, category="file")
    
    math_tools = registry.list_tools(category="math")
    assert len(math_tools) == 1
    assert "calculator" in math_tools
    
    file_tools = registry.list_tools(category="file")
    assert len(file_tools) == 1
    assert "file_read" in file_tools


def test_search_exact_name(registry, calculator_tool):
    """Test searching by exact tool name."""
    registry.register(calculator_tool, category="math")
    
    results = registry.search("calculator")
    assert len(results) > 0
    assert "calculator" in results


def test_search_by_description(registry, calculator_tool):
    """Test searching by description keywords."""
    registry.register(
        calculator_tool,
        category="math",
        tags=["math", "arithmetic"],
    )
    
    results = registry.search("mathematical")
    assert len(results) > 0
    assert "calculator" in results


def test_search_by_tags(registry, calculator_tool):
    """Test searching by tags."""
    registry.register(
        calculator_tool,
        category="math",
        tags=["calculator", "arithmetic", "compute"],
    )
    
    results = registry.search("arithmetic")
    assert len(results) > 0
    assert "calculator" in results


def test_search_top_k(registry, calculator_tool, file_read_tool):
    """Test top_k parameter in search."""
    registry.register(calculator_tool, category="math")
    registry.register(file_read_tool, category="file")
    
    results = registry.search("tool", top_k=1)
    assert len(results) <= 1


def test_get_tools_by_names(registry, calculator_tool, file_read_tool):
    """Test getting multiple tools by names."""
    registry.register(calculator_tool, category="math")
    registry.register(file_read_tool, category="file")
    
    tools = registry.get_tools_by_names(["calculator", "file_read"])
    assert len(tools) == 2
    
    tool_names = [t.name for t in tools]
    assert "calculator" in tool_names
    assert "file_read" in tool_names


def test_get_categories(registry, calculator_tool, file_read_tool):
    """Test getting all categories."""
    registry.register(calculator_tool, category="math")
    registry.register(file_read_tool, category="file")
    
    categories = registry.get_categories()
    assert "math" in categories
    assert "file" in categories


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
