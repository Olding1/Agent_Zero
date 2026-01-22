"""Unit tests for preset tools."""

import pytest
import tempfile
from pathlib import Path

from src.tools.preset_tools import (
    CalculatorTool,
    FileReadTool,
    FileWriteTool,
    PythonREPLTool,
)


# ============================================================================
# Calculator Tool Tests
# ============================================================================

def test_calculator_basic_math():
    """Test basic mathematical operations."""
    calc = CalculatorTool()
    
    assert calc._run("2 + 2") == "4"
    assert calc._run("10 - 3") == "7"
    assert calc._run("5 * 6") == "30"
    assert calc._run("20 / 4") == "5.0"


def test_calculator_complex_expression():
    """Test complex mathematical expressions."""
    calc = CalculatorTool()
    
    result = calc._run("(10 + 5) * 2 - 3")
    assert result == "27"


def test_calculator_functions():
    """Test built-in math functions."""
    calc = CalculatorTool()
    
    assert calc._run("abs(-5)") == "5"
    assert calc._run("max(1, 5, 3)") == "5"
    assert calc._run("min(1, 5, 3)") == "1"


def test_calculator_error_handling():
    """Test calculator error handling."""
    calc = CalculatorTool()
    
    result = calc._run("1 / 0")
    assert "Error" in result


# ============================================================================
# File Read Tool Tests
# ============================================================================

def test_file_read_success(tmp_path):
    """Test reading a file successfully."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_content = "Hello, World!"
    test_file.write_text(test_content, encoding='utf-8')
    
    # Read file
    tool = FileReadTool()
    result = tool._run(str(test_file))
    
    assert result == test_content


def test_file_read_not_found():
    """Test reading non-existent file."""
    tool = FileReadTool()
    result = tool._run("nonexistent.txt")
    
    assert "Error" in result
    assert "not found" in result.lower()


def test_file_read_directory(tmp_path):
    """Test reading a directory (should fail)."""
    tool = FileReadTool()
    result = tool._run(str(tmp_path))
    
    assert "Error" in result


# ============================================================================
# File Write Tool Tests
# ============================================================================

def test_file_write_success(tmp_path):
    """Test writing to a file successfully."""
    test_file = tmp_path / "output.txt"
    test_content = "Test content"
    
    tool = FileWriteTool()
    result = tool._run(str(test_file), test_content)
    
    assert "Successfully" in result
    assert test_file.exists()
    assert test_file.read_text(encoding='utf-8') == test_content


def test_file_write_creates_directories(tmp_path):
    """Test that write creates parent directories."""
    test_file = tmp_path / "subdir" / "output.txt"
    test_content = "Test content"
    
    tool = FileWriteTool()
    result = tool._run(str(test_file), test_content)
    
    assert "Successfully" in result
    assert test_file.exists()


# ============================================================================
# Python REPL Tool Tests
# ============================================================================

def test_python_repl_simple_print():
    """Test executing simple print statement."""
    tool = PythonREPLTool()
    result = tool._run("print('Hello, World!')")
    
    assert "Hello, World!" in result


def test_python_repl_calculation():
    """Test executing calculations."""
    tool = PythonREPLTool()
    result = tool._run("print(2 + 2)")
    
    assert "4" in result


def test_python_repl_list_operations():
    """Test list operations."""
    tool = PythonREPLTool()
    code = """
numbers = [1, 2, 3, 4, 5]
print(sum(numbers))
"""
    result = tool._run(code)
    
    assert "15" in result


def test_python_repl_error_handling():
    """Test error handling in REPL."""
    tool = PythonREPLTool()
    result = tool._run("print(undefined_variable)")
    
    assert "Error" in result


def test_python_repl_no_output():
    """Test code with no output."""
    tool = PythonREPLTool()
    result = tool._run("x = 5")
    
    assert "executed successfully" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
