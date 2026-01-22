"""
Phase 6 Task 6.3: Test Analyzer - Unit Tests

Tests for LLM-based test analyzer.
"""

import pytest
from datetime import datetime
from src.schemas.test_report import IterationReport, TestCaseReport
from src.schemas.analysis_result import AnalysisResult, FixStep
from src.core.test_analyzer import TestAnalyzer
from unittest.mock import AsyncMock, MagicMock


class TestTestAnalyzer:
    """Test LLM-based test analyzer"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Mock LLM client
        self.mock_llm = MagicMock()
        self.analyzer = TestAnalyzer(self.mock_llm)
    
    @pytest.mark.asyncio
    async def test_analyze_rag_failure(self):
        """Test analysis of RAG-related failures"""
        # Create test report with RAG failures
        test_cases = [
            TestCaseReport(
                test_id="test_1",
                test_name="Test RAG Recall",
                status="FAILED",
                metrics={"contextual_recall": 0.3},
                actual_output="Wrong answer",
                expected_output="Correct answer",
                retrieval_context=[],
                error_message="Contextual Recall too low: 0.3",
                duration_seconds=1.0
            ),
            TestCaseReport(
                test_id="test_2",
                test_name="Test RAG Faithfulness",
                status="FAILED",
                metrics={"faithfulness": 0.4},
                actual_output="Hallucinated",
                expected_output="Factual",
                retrieval_context=[],
                error_message="Faithfulness score below threshold",
                duration_seconds=1.0
            )
        ]
        
        report = IterationReport(
            iteration_id=1,
            timestamp=datetime.now(),
            agent_name="TestAgent",
            total_tests=2,
            passed_tests=0,
            failed_tests=2,
            pass_rate=0.0,
            test_cases=test_cases,
            error_types={},
            judge_feedback="",
            graph_snapshot={},
            avg_metrics={}
        )
        
        # Mock LLM response
        mock_response = """{
            "primary_issue": "RAG 检索质量不足",
            "root_cause": "Contextual Recall 和 Faithfulness 分数都很低",
            "fix_strategy": [
                {
                    "step": 1,
                    "target": "rag_builder",
                    "action": "增加检索文档数 retriever_k",
                    "parameters": {"retriever_k": 6},
                    "expected_improvement": "Recall 提升至 0.6+",
                    "priority": "high"
                }
            ],
            "estimated_success_rate": 0.75
        }"""
        
        self.mock_llm.call = AsyncMock(return_value=mock_response)
        
        # Analyze
        config = {"graph": {}, "rag": {"retriever_k": 3}, "tools": None}
        result = await self.analyzer.analyze_test_report(report, config)
        
        # Assert
        assert result.primary_issue == "RAG 检索质量不足"
        assert result.estimated_success_rate == 0.75
        assert len(result.fix_strategy) == 1
        assert result.fix_strategy[0].target == "rag_builder"
        assert result.fix_strategy[0].priority == "high"
    
    @pytest.mark.asyncio
    async def test_analyze_success(self):
        """Test analysis when all tests pass"""
        # Create successful test report
        test_cases = [
            TestCaseReport(
                test_id="test_1",
                test_name="Test Success",
                status="PASSED",
                metrics={},
                actual_output="Correct",
                expected_output="Correct",
                retrieval_context=[],
                error_message=None,
                duration_seconds=1.0
            )
        ]
        
        report = IterationReport(
            iteration_id=1,
            timestamp=datetime.now(),
            agent_name="TestAgent",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            pass_rate=1.0,
            test_cases=test_cases,
            error_types={},
            judge_feedback="",
            graph_snapshot={},
            avg_metrics={}
        )
        
        # Analyze (should not call LLM)
        config = {"graph": {}, "rag": None, "tools": None}
        result = await self.analyzer.analyze_test_report(report, config)
        
        # Assert
        assert result.primary_issue == "所有测试通过"
        assert result.estimated_success_rate == 1.0
        assert len(result.fix_strategy) == 0
    
    @pytest.mark.asyncio
    async def test_parse_llm_response_with_markdown(self):
        """Test parsing LLM response with markdown code blocks"""
        # Mock response with markdown
        mock_response = """Here's the analysis:
        
```json
{
    "primary_issue": "Logic error",
    "root_cause": "Graph routing issue",
    "fix_strategy": [],
    "estimated_success_rate": 0.5
}
```
"""
        
        # Parse
        result = self.analyzer._parse_analysis_response(mock_response)
        
        # Assert
        assert result.primary_issue == "Logic error"
        assert result.root_cause == "Graph routing issue"
        assert result.estimated_success_rate == 0.5
    
    @pytest.mark.asyncio
    async def test_parse_invalid_response(self):
        """Test handling of invalid LLM response"""
        # Invalid JSON
        mock_response = "This is not valid JSON"
        
        # Parse (should return error result)
        result = self.analyzer._parse_analysis_response(mock_response)
        
        # Assert
        assert "解析失败" in result.primary_issue
        assert result.estimated_success_rate == 0.0
    
    def test_create_analysis_prompt(self):
        """Test prompt generation"""
        # Create test cases
        failed_cases = [
            TestCaseReport(
                test_id="test_1",
                test_name="Test Failure",
                status="FAILED",
                metrics={},
                actual_output="Wrong",
                expected_output="Right",
                retrieval_context=[],
                error_message="Test failed",
                duration_seconds=1.0
            )
        ]
        
        report = IterationReport(
            iteration_id=1,
            timestamp=datetime.now(),
            agent_name="TestAgent",
            total_tests=1,
            passed_tests=0,
            failed_tests=1,
            pass_rate=0.0,
            test_cases=failed_cases,
            error_types={},
            judge_feedback="",
            graph_snapshot={},
            avg_metrics={}
        )
        
        config = {"graph": {}, "rag": None, "tools": None}
        
        # Generate prompt
        prompt = self.analyzer._create_analysis_prompt(failed_cases, config, report)
        
        # Assert
        assert "测试失败分析任务" in prompt
        assert "Test Failure" in prompt
        assert "通过率: 0.0%" in prompt
        assert "JSON 格式返回" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
