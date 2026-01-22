"""
Phase 6 Integration Test

Tests the complete Phase 6 workflow with all optimizers.
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.schemas.project_meta import ProjectMeta, TaskType
from src.schemas.rag_config import RAGConfig
from src.schemas.tools_config import ToolsConfig
from src.schemas.graph_structure import GraphStructure
from src.schemas.execution_result import ExecutionResult, ExecutionStatus, TestResult
from src.schemas.judge_result import JudgeResult, ErrorType, FixTarget
from src.schemas.test_report import IterationReport, TestCaseReport
from src.schemas.analysis_result import AnalysisResult, FixStep
from src.core.judge import Judge
from src.core.test_analyzer import TestAnalyzer
from src.core.rag_optimizer import RAGOptimizer
from src.core.tool_optimizer import ToolOptimizer


class TestPhase6Integration:
    """Integration tests for Phase 6 complete workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_rag_optimization_flow(self):
        """Test complete flow: Judge → Analyzer → RAG Optimizer"""
        
        # 1. Create test results with RAG failures
        test_results = [
            TestResult(
                test_id="test_1",
                status=ExecutionStatus.FAILED,
                error_message="Contextual Recall too low: 0.3",
                actual_output="Wrong",
                duration_ms=1000
            ),
            TestResult(
                test_id="test_2",
                status=ExecutionStatus.FAILED,
                error_message="Contextual Recall too low: 0.25",
                actual_output="Wrong",
                duration_ms=1000
            ),
            TestResult(
                test_id="test_3",
                status=ExecutionStatus.FAILED,
                error_message="Contextual Recall too low: 0.2",
                actual_output="Wrong",
                duration_ms=1000
            )
        ]
        
        exec_result = ExecutionResult(
            overall_status=ExecutionStatus.FAILED,
            test_results=test_results,
            stderr=""
        )
        
        # 2. Judge Analysis
        judge = Judge()
        judge_result = judge.analyze_result(exec_result)
        
        # Assert Judge correctly identifies RAG issue
        assert judge_result.error_type == ErrorType.RAG_QUALITY
        assert judge_result.fix_target == FixTarget.RAG_BUILDER
        
        # 3. Create iteration report
        test_cases = [
            TestCaseReport(
                test_id=t.test_id,
                test_name=t.test_id,
                status="FAILED",
                metrics={"contextual_recall": 0.3},
                actual_output=t.actual_output,
                expected_output="Correct",
                retrieval_context=[],
                error_message=t.error_message,
                duration_seconds=1.0
            ) for t in test_results
        ]
        
        report = IterationReport(
            iteration_id=1,
            timestamp=datetime.now(),
            agent_name="TestAgent",
            total_tests=3,
            passed_tests=0,
            failed_tests=3,
            pass_rate=0.0,
            test_cases=test_cases,
            error_types={},
            judge_feedback="",
            graph_snapshot={},
            avg_metrics={"contextual_recall": 0.25}
        )
        
        # 4. LLM Analysis
        mock_llm = MagicMock()
        mock_llm.call = AsyncMock(return_value="""{
            "primary_issue": "Low contextual recall",
            "root_cause": "k_retrieval is too small",
            "fix_strategy": [
                {
                    "step": 1,
                    "target": "rag_builder",
                    "action": "Increase k_retrieval",
                    "parameters": {"k_retrieval": 6},
                    "expected_improvement": "Recall should improve to 0.6+",
                    "priority": "high"
                }
            ],
            "estimated_success_rate": 0.75
        }""")
        
        analyzer = TestAnalyzer(mock_llm)
        config = {
            "graph": {},
            "rag": {"k_retrieval": 3},
            "tools": None
        }
        
        analysis = await analyzer.analyze_test_report(report, config)
        
        # Assert analysis is correct
        assert "recall" in analysis.primary_issue.lower()
        assert len(analysis.fix_strategy) == 1
        assert analysis.fix_strategy[0].target == "rag_builder"
        
        # 5. RAG Optimization
        current_rag = RAGConfig(k_retrieval=3)
        rag_optimizer = RAGOptimizer(mock_llm)
        
        new_rag = await rag_optimizer.optimize_config(current_rag, analysis, report)
        
        # Assert optimization worked
        assert new_rag.k_retrieval > current_rag.k_retrieval
        
        print(f"✅ Complete flow test passed!")
        print(f"   Judge: {judge_result.error_type} → {judge_result.fix_target}")
        print(f"   Analysis: {analysis.primary_issue}")
        print(f"   Optimization: k_retrieval {current_rag.k_retrieval} → {new_rag.k_retrieval}")
    
    @pytest.mark.asyncio
    async def test_judge_error_classification_coverage(self):
        """Test that Judge covers all error types"""
        judge = Judge()
        
        # Test RAG_QUALITY
        rag_quality_result = ExecutionResult(
            overall_status=ExecutionStatus.FAILED,
            test_results=[
                TestResult(
                    test_id=f"test_{i}",
                    status=ExecutionStatus.FAILED,
                    error_message="Contextual Recall low",
                    actual_output="",
                    duration_ms=100
                ) for i in range(3)
            ],
            stderr=""
        )
        
        result = judge.analyze_result(rag_quality_result)
        assert result.error_type == ErrorType.RAG_QUALITY
        assert result.fix_target == FixTarget.RAG_BUILDER
        
        print("✅ Error classification coverage test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
