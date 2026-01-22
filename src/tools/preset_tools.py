"""Preset tools for Agent Zero.

This module contains commonly used tools that can be registered
in the tool registry.
"""

from typing import Optional, Type
from langchain_core.tools import BaseTool
from langchain_community.tools import TavilySearchResults
from pydantic import BaseModel, Field


# ============================================================================
# Search Tools
# ============================================================================

def create_tavily_search_tool(api_key: Optional[str] = None) -> BaseTool:
    """Create Tavily search tool.
    
    Args:
        api_key: Optional Tavily API key (if not in env)
        
    Returns:
        TavilySearchResults tool
    """
    kwargs = {"max_results": 5}
    if api_key:
        kwargs["api_key"] = api_key
    
    return TavilySearchResults(**kwargs)


# ============================================================================
# Math Tools
# ============================================================================

class CalculatorInput(BaseModel):
    """Input for calculator tool."""
    expression: str = Field(description="Mathematical expression to evaluate")


class CalculatorTool(BaseTool):
    """Simple calculator tool for basic math operations."""
    
    name: str = "calculator"
    description: str = "Useful for performing basic mathematical calculations. Input should be a valid Python mathematical expression."
    args_schema: Type[BaseModel] = CalculatorInput
    
    def _run(self, expression: str) -> str:
        """Execute the calculator.
        
        Args:
            expression: Mathematical expression
            
        Returns:
            Result as string
        """
        try:
            # Safe evaluation using limited namespace
            # Only allow basic math operations
            allowed_names = {
                'abs': abs,
                'round': round,
                'min': min,
                'max': max,
                'sum': sum,
                'pow': pow,
            }
            
            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return str(result)
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self, expression: str) -> str:
        """Async version."""
        return self._run(expression)


# ============================================================================
# File Tools
# ============================================================================

class FileReadInput(BaseModel):
    """Input for file read tool."""
    file_path: str = Field(description="Path to the file to read")


class FileReadTool(BaseTool):
    """Tool for reading file contents."""
    
    name: str = "file_read"
    description: str = "Read the contents of a text file. Input should be the file path."
    args_schema: Type[BaseModel] = FileReadInput
    
    def _run(self, file_path: str) -> str:
        """Read file contents.
        
        Args:
            file_path: Path to file
            
        Returns:
            File contents or error message
        """
        try:
            from pathlib import Path
            path = Path(file_path)
            
            if not path.exists():
                return f"Error: File not found: {file_path}"
            
            if not path.is_file():
                return f"Error: Not a file: {file_path}"
            
            content = path.read_text(encoding='utf-8')
            return content
            
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    async def _arun(self, file_path: str) -> str:
        """Async version."""
        return self._run(file_path)


class FileWriteInput(BaseModel):
    """Input for file write tool."""
    file_path: str = Field(description="Path to the file to write")
    content: str = Field(description="Content to write to the file")


class FileWriteTool(BaseTool):
    """Tool for writing content to a file."""
    
    name: str = "file_write"
    description: str = "Write content to a text file. Input should be file path and content."
    args_schema: Type[BaseModel] = FileWriteInput
    
    def _run(self, file_path: str, content: str) -> str:
        """Write content to file.
        
        Args:
            file_path: Path to file
            content: Content to write
            
        Returns:
            Success message or error
        """
        try:
            from pathlib import Path
            path = Path(file_path)
            
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            path.write_text(content, encoding='utf-8')
            
            return f"Successfully wrote {len(content)} characters to {file_path}"
            
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    async def _arun(self, file_path: str, content: str) -> str:
        """Async version."""
        return self._run(file_path, content)


# ============================================================================
# Python REPL Tool
# ============================================================================

class PythonREPLInput(BaseModel):
    """Input for Python REPL tool."""
    code: str = Field(description="Python code to execute")


class PythonREPLTool(BaseTool):
    """Tool for executing Python code in a safe environment."""
    
    name: str = "python_repl"
    description: str = "Execute Python code and return the result. Use for data processing, calculations, or simple scripts."
    args_schema: Type[BaseModel] = PythonREPLInput
    
    def _run(self, code: str) -> str:
        """Execute Python code.
        
        Args:
            code: Python code to execute
            
        Returns:
            Execution result or error
        """
        try:
            # Create a restricted namespace
            namespace = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'tuple': tuple,
                    'abs': abs,
                    'min': min,
                    'max': max,
                    'sum': sum,
                    'sorted': sorted,
                    'enumerate': enumerate,
                    'zip': zip,
                }
            }
            
            # Capture stdout
            from io import StringIO
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                # Execute code
                exec(code, namespace)
                
                # Get output
                output = sys.stdout.getvalue()
                
                return output if output else "Code executed successfully (no output)"
                
            finally:
                sys.stdout = old_stdout
                
        except Exception as e:
            return f"Error executing code: {str(e)}"
    
    async def _arun(self, code: str) -> str:
        """Async version."""
        return self._run(code)


# ============================================================================
# Tool Factory Functions
# ============================================================================

def get_preset_tools() -> dict[str, BaseTool]:
    """Get all preset tools.
    
    Returns:
        Dictionary mapping tool names to tool instances
    """
    tools = {
        "calculator": CalculatorTool(),
        "file_read": FileReadTool(),
        "file_write": FileWriteTool(),
        "python_repl": PythonREPLTool(),
    }
    
    # Add Tavily search if available
    try:
        tools["tavily_search"] = create_tavily_search_tool()
    except Exception:
        # Tavily not configured, skip
        pass
    
    return tools


def register_preset_tools(registry) -> None:
    """Register all preset tools in a registry.
    
    Args:
        registry: ToolRegistry instance
    """
    from .registry import register_tool
    
    # Calculator
    register_tool(
        CalculatorTool(),
        category="math",
        tags=["calculator", "math", "arithmetic", "compute"],
        requires_api_key=False,
    )
    
    # File tools
    register_tool(
        FileReadTool(),
        category="file",
        tags=["file", "read", "text", "content"],
        requires_api_key=False,
    )
    
    register_tool(
        FileWriteTool(),
        category="file",
        tags=["file", "write", "save", "create"],
        requires_api_key=False,
    )
    
    # Python REPL
    register_tool(
        PythonREPLTool(),
        category="code",
        tags=["python", "code", "execute", "script", "programming"],
        requires_api_key=False,
    )
    
    # Tavily search (if available)
    try:
        register_tool(
            create_tavily_search_tool(),
            category="search",
            tags=["search", "web", "internet", "query", "information"],
            requires_api_key=True,
        )
    except Exception:
        # Tavily not configured, skip
        pass
