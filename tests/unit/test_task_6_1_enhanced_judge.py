"""
Phase 6 Task 6.1: Enhanced Judge - Unit Tests

Tests for RAG and Tools error classification.
"""

import pytest
from src.schemas.execution_result import ExecutionResult, ExecutionStatus, TestResult
from src.schemas.judge_result import JudgeResult, ErrorType, FixTarget
from src.core.judge import Judge


class TestEnhancedJudge:
    """Test enhanced Judge with RAG/Tools error classification"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.judge = Judge()
    
    def test_classify_rag_quality_error(self):
        """Test RAG quality error classification (low recall/faithfulness)"""
        # Create test results with RAG quality issues
        test_results = [
            TestResult(
                test_id="test_1",
                status=ExecutionStatus.FAILED,
                error_message="Contextual Recall score too low: 0.3",
                actual_output="Wrong answer",
                duration_ms=1000
            ),
            TestResult(
                test_id="test_2",
                status=ExecutionStatus.FAILED,
                error_message="Faithfulness score below threshold: 0.4",
                actual_output="Hallucinated content",
                duration_ms=1000
            ),
            TestResult(
                test_id="test_3",
                status=ExecutionStatus.FAILED,
                error_message="Low contextual recall detected",
                actual_output="Incomplete answer",
                duration_ms=1000
            )
        ]
        
        exec_result = ExecutionResult(
            overall_status=ExecutionStatus.FAILED,
            test_results=test_results,
            stderr=""
        )
        
        # Analyze
        judge_result = self.judge.analyze_result(exec_result)
        
        # Assert
        assert judge_result.error_type == ErrorType.RAG_QUALITY
        assert judge_result.fix_target == FixTarget.RAG_BUILDER
    
    def test_classify_rag_config_error(self):
        """Test RAG config error classification (empty context)"""
        # Create test results with RAG config issues
        test_results = [
            TestResult(
                test_id="test_1",
                status=ExecutionStatus.FAILED,
                error_message="Retrieval context is empty",
                actual_output="No context",
                duration_ms=1000
            ),
            TestResult(
                test_id="test_2",
                status=ExecutionStatus.FAILED,
                error_message="Empty context returned from retrieval",
                actual_output="No docs found",
                duration_ms=1000
            ),
            TestResult(
                test_id="test_3",
                status=ExecutionStatus.FAILED,
                error_message="Context is empty after retrieval",
                actual_output="Missing context",
                duration_ms=1000
            )
        ]
        
        exec_result = ExecutionResult(
            overall_status=ExecutionStatus.FAILED,
            test_results=test_results,
            stderr=""
        )
        
        # Analyze
        judge_result = self.judge.analyze_result(exec_result)
        
        # Assert
        assert judge_result.error_type == ErrorType.RAG_CONFIG
        assert judge_result.fix_target == FixTarget.RAG_BUILDER
    
    def test_classify_runtime_error(self):
        """Test runtime error classification (still works)"""
        test_results = [
            TestResult(
                test_id="test_1",
                status=ExecutionStatus.FAILED,
                error_message="ImportError: No module named 'missing_package'",
                actual_output="",
                duration_ms=100
            )
        ]
        
        exec_result = ExecutionResult(
            overall_status=ExecutionStatus.FAILED,
            test_results=test_results,
            stderr="ImportError: No module named 'missing_package'"
        )
        
        # Analyze
        judge_result = self.judge.analyze_result(exec_result)
        
        # Assert
        assert judge_result.error_type == ErrorType.RUNTIME
        assert judge_result.fix_target == FixTarget.COMPILER
    
    def test_no_error_classification(self):
        """Test successful execution"""
        test_results = [
            TestResult(
                test_id="test_1",
                status=ExecutionStatus.PASS,
                error_message=None,
                actual_output="Correct answer",
                duration_ms=1000
            )
        ]
        
        exec_result = ExecutionResult(
            overall_status=ExecutionStatus.PASS,
            test_results=test_results,
            stderr=""
        )
        
        # Analyze
        judge_result = self.judge.analyze_result(exec_result)
        
        # Assert
        assert judge_result.error_type == ErrorType.NONE
        assert judge_result.fix_target == FixTarget.NONE
    
    def test_rag_error_with_few_failures(self):
        """Test that RAG errors need 3+ failures to be classified"""
        # Only 2 RAG failures - should not be classified as RAG error
        test_results = [
            TestResult(
                test_id="test_1",
                status=ExecutionStatus.FAILED,
                error_message="Contextual Recall too low",
                actual_output="Wrong",
                duration_ms=1000
            ),
            TestResult(
                test_id="test_2",
                status=ExecutionStatus.FAILED,
                error_message="Faithfulness low",
                actual_output="Wrong",
                duration_ms=1000
            ),
            TestResult(
                test_id="test_3",
                status=ExecutionStatus.PASS,
                error_message=None,
                actual_output="Correct",
                duration_ms=1000
            )
        ]
        
        exec_result = ExecutionResult(
            overall_status=ExecutionStatus.FAILED,
            test_results=test_results,
            stderr=""
        )
        
        # Analyze
        judge_result = self.judge.analyze_result(exec_result)
        
        # Should fall back to LOGIC error (not RAG specific)
        assert judge_result.error_type == ErrorType.LOGIC
        assert judge_result.fix_target == FixTarget.GRAPH_DESIGNER


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
