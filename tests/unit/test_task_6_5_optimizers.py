"""
Phase 6 Task 6.5: Optimizers - Unit Tests

Basic tests for all four optimizers.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.schemas.rag_config import RAGConfig
from src.schemas.tools_config import ToolsConfig
from src.schemas.analysis_result import AnalysisResult, FixStep
from src.schemas.test_report import IterationReport, TestCaseReport
from src.schemas.project_meta import ProjectMeta, TaskType
from src.core.rag_optimizer import RAGOptimizer
from src.core.tool_optimizer import ToolOptimizer
from src.core.compiler_optimizer import CompilerOptimizer


class TestRAGOptimizer:
    """Test RAG optimizer"""
    
    @pytest.mark.asyncio
    async def test_optimize_low_recall(self):
        """Test RAG optimization for low recall"""
        mock_llm = MagicMock()
        optimizer = RAGOptimizer(mock_llm)
        
        current_config = RAGConfig(
            chunk_size=500,
            chunk_overlap=100,
            k_retrieval=3
        )
        
        analysis = AnalysisResult(
            primary_issue="Low recall detected",
            root_cause="Retriever k is too small",
            fix_strategy=[],
            estimated_success_rate=0.6
        )
        
        report = IterationReport(
            iteration_id=1,
            timestamp=datetime.now(),
            agent_name="Test",
            total_tests=5,
            passed_tests=2,
            failed_tests=3,
            pass_rate=0.4,
            test_cases=[],
            error_types={},
            judge_feedback="",
            graph_snapshot={},
            avg_metrics={}
        )
        
        # Optimize (should increase k_retrieval)
        new_config = await optimizer.optimize_config(current_config, analysis, report)
        
        # Assert
        assert new_config.k_retrieval > current_config.k_retrieval
        assert new_config.k_retrieval == 6  # 3 * 2


class TestToolOptimizer:
    """Test Tool optimizer"""
    
    @pytest.mark.asyncio
    async def test_optimize_tools(self):
        """Test tool optimization"""
        mock_llm = MagicMock()
        mock_selector = MagicMock()
        mock_selector.select_tools = AsyncMock(return_value=ToolsConfig(
            enabled_tools=["tavily_search", "llm_math"]
        ))
        
        optimizer = ToolOptimizer(mock_llm, mock_selector)
        
        current_config = ToolsConfig(enabled_tools=["python_repl", "file_read"])
        
        analysis = AnalysisResult(
            primary_issue="Tool execution failed",
            root_cause="python_repl tool error",
            fix_strategy=[],
            estimated_success_rate=0.5
        )
        
        meta = ProjectMeta(
            agent_name="Test",
            description="Test agent",
            user_intent_summary="Test",
            has_rag=False,
            task_type=TaskType.SEARCH
        )
        
        # Optimize
        new_config = await optimizer.optimize_tools(current_config, analysis, meta)
        
        # Assert - should have replaced failed tool
        assert "python_repl" not in new_config.enabled_tools or len(new_config.enabled_tools) > 2


class TestCompilerOptimizer:
    """Test Compiler optimizer"""
    
    @pytest.mark.asyncio
    async def test_extract_missing_packages(self):
        """Test package extraction from error message"""
        mock_compiler = MagicMock()
        optimizer = CompilerOptimizer(mock_compiler)
        
        error_msg = "ImportError: No module named 'missing_package'"
        
        packages = optimizer._extract_missing_packages(error_msg)
        
        assert "missing_package" in packages
    
    @pytest.mark.asyncio
    async def test_optimize_dependencies(self, tmp_path):
        """Test dependency optimization"""
        mock_compiler = MagicMock()
        optimizer = CompilerOptimizer(mock_compiler)
        
        # Create requirements.txt
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("langchain>=0.2.0\n")
        
        analysis = AnalysisResult(
            primary_issue="Import error",
            root_cause="Missing package",
            fix_strategy=[],
            estimated_success_rate=0.5
        )
        
        error_msg = "No module named 'new_package'"
        
        # Optimize
        result = await optimizer.optimize_dependencies(tmp_path, analysis, error_msg)
        
        # Assert
        assert result == True
        content = req_file.read_text()
        assert "new_package" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
