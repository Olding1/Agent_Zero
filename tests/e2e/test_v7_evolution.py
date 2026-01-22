
import pytest
import asyncio
from pathlib import Path
from src.core.rag_optimizer import RAGOptimizer
from src.schemas.rag_config import RAGConfig
from src.schemas.analysis_result import AnalysisResult, FixStep
from src.schemas.test_report import IterationReport, TestCaseReport

@pytest.mark.asyncio
async def test_v7_evolution_loop():
    """
    E2E Test for Agent Zero v7.0 Architectural Evolution.
    """
    print("\n🚀 [E2E] Starting v7.0 Evolution Test...")
    
    # 1. Setup Initial Configuration (Basic Vector Search)
    current_config = RAGConfig(
        k_retrieval=5,
        enable_hybrid_search=False,
        reranker_enabled=False
    )
    print(f"📝 Initial Config: k={current_config.k_retrieval}, Hybrid={current_config.enable_hybrid_search}")
    
    # 2. Simulate Analysis Result (Low Recall Issue)
    mock_analysis = AnalysisResult(
        primary_issue="Low Recall: Relevant documents were missed by the retriever.",
        root_cause="Vector search failed to capture keyword matches.",
        # FixStep objects required
        fix_strategy=[
            FixStep(
                step=1,
                target="rag_builder",
                action="Increase retrieval k",
                expected_improvement="Higher recall",
                priority="high"
            ),
            FixStep(
                step=2,
                target="rag_builder",
                action="Enable hybrid search",
                expected_improvement="Better keyword matching",
                priority="medium"
            )
        ],
        estimated_success_rate=0.8
    )
    
    # Simulate a Test Report (supporting data)
    mock_report = IterationReport(
        iteration_id=1,
        agent_name="test_agent",
        total_tests=1,
        passed_tests=0,
        failed_tests=1,
        pass_rate=0.0,
        test_cases=[
            TestCaseReport(
                test_id="test_1",
                test_name="test_law_query", 
                status="FAILED",
                metrics={"contextual_recall": 0.0, "faithfulness": 1.0}
            )
        ],
        summary="Recall is critically low."
    )
    
    # 3. Run Optimizer (The Brain)
    # We pass None for llm_client to force heuristic mode (deterministic/fast testing)
    optimizer = RAGOptimizer(llm_client=None)
    
    print("🧠 Running RAG Optimizer...")
    optimized_config = await optimizer.optimize_config(
        current_config=current_config,
        analysis=mock_analysis,
        test_report=mock_report
    )
    
    # 4. Verify Evolution
    print(f"✨ New Config: k={optimized_config.k_retrieval}, Hybrid={optimized_config.enable_hybrid_search}")
    
    # Check if architecture evolved
    assert optimized_config.k_retrieval > current_config.k_retrieval, "Should increase k_retrieval"
    
    # The heuristic rules state: if recall is low and k is insufficient or suggestion is heavy, 
    # check if the optimizer proposed hybrid search.
    # Note: Our updated optimizer logic in Phase 3 enables hybrid search if k >= 10 and recall is low.
    # Let's adjust our expectation or input to trigger that.
    # The current input k=5 might just result in k=10.
    
    # Let's try a second iteration to force Hybrid Search
    if not optimized_config.enable_hybrid_search:
        print("🔄 First iteration just increased k. Simulating second iteration...")
        current_config_2 = optimized_config # k=10
        # Re-run
        optimized_config_2 = await optimizer.optimize_config(
            current_config=current_config_2,
            analysis=mock_analysis,
            test_report=mock_report
        )
        print(f"✨ Iteration 2 Config: k={optimized_config_2.k_retrieval}, Hybrid={optimized_config_2.enable_hybrid_search}")
        
        assert optimized_config_2.enable_hybrid_search is True, "Should enable Hybrid Search on 2nd iteration/high k"
        assert optimized_config_2.k_retrieval == 15, "Should set k=15 for Hybrid Search"
        
    print("✅ E2E Evolution Test Passed: Architecture successfully evolved!")

if __name__ == "__main__":
    asyncio.run(test_v7_evolution_loop())
