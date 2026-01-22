# Phase 6 Completion Implementation Plan

## 🎯 Overview

Complete the missing P1 and P2 features for Phase 6 Runtime Evolution:
- **Task 6.1**: Enhanced Judge with RAG/Tools error classification
- **Task 6.3**: LLM-based intelligent test analyzer
- **Task 6.5**: RAG and Tools configuration optimizers

**Current Status**: 25% complete (only P0 tasks done)
**Target**: 100% complete with full intelligent iteration loop

---

## 📋 Implementation Phases

### Phase 1: Enhanced Judge (Task 6.1) - 2-3 hours

#### Step 1.1: Extend Error Types and Fix Targets
**File**: `src/schemas/judge_result.py`

**Changes**:
```python
class ErrorType(str, Enum):
    NONE = "none"
    RUNTIME = "runtime"
    LOGIC = "logic"
    TIMEOUT = "timeout"
    API = "api"
    # 🆕 New error types
    RAG_QUALITY = "rag_quality"    # Low recall/precision
    RAG_CONFIG = "rag_config"      # Wrong chunk_size/k
    TOOL_ERROR = "tool_error"      # Tool execution failed
    TOOL_CONFIG = "tool_config"    # Wrong tool selected

class FixTarget(str, Enum):
    MANUAL = "manual"
    COMPILER = "compiler"
    GRAPH_DESIGNER = "graph_designer"
    # 🆕 New fix targets
    RAG_BUILDER = "rag_builder"
    TOOL_SELECTOR = "tool_selector"
    HYBRID = "hybrid"              # Multiple components
```

#### Step 1.2: Add RAG Error Classification
**File**: `src/core/judge.py`

**New Method**:
```python
def _classify_rag_error(self, result: ExecutionResult) -> Optional[ErrorType]:
    """Classify RAG-related errors
    
    Heuristics:
    - If avg Contextual Recall < 0.5 → RAG_QUALITY
    - If multiple tests fail with empty context → RAG_CONFIG
    - If Faithfulness < 0.5 → RAG_QUALITY (wrong docs)
    """
    rag_failures = []
    for test in result.test_results:
        if test.status == ExecutionStatus.FAILED:
            # Check error message for RAG indicators
            if test.error_message:
                if "retrieval context is empty" in test.error_message.lower():
                    rag_failures.append("empty_context")
                elif "contextual recall" in test.error_message.lower():
                    rag_failures.append("low_recall")
                elif "faithfulness" in test.error_message.lower():
                    rag_failures.append("low_faithfulness")
    
    if len(rag_failures) >= 3:  # Multiple RAG failures
        if "empty_context" in rag_failures:
            return ErrorType.RAG_CONFIG  # Configuration issue
        else:
            return ErrorType.RAG_QUALITY  # Quality issue
    
    return None
```

#### Step 1.3: Update analyze_result Logic
**File**: `src/core/judge.py`

**Modify**:
```python
def analyze_result(self, result: ExecutionResult) -> JudgeResult:
    """Enhanced analysis with RAG/Tools classification"""
    
    # 1. Try RAG classification first
    rag_error = self._classify_rag_error(result)
    if rag_error:
        return JudgeResult(
            error_type=rag_error,
            fix_target=FixTarget.RAG_BUILDER,
            feedback=self._generate_rag_feedback(result)
        )
    
    # 2. Existing logic for other errors
    # ...
```

---

### Phase 2: LLM Test Analyzer (Task 6.3) - 4-5 hours

#### Step 2.1: Create Analysis Result Schema
**File**: `src/schemas/analysis_result.py` (NEW)

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class FixStep(BaseModel):
    """Single fix step in strategy"""
    step: int
    target: str  # "rag_builder", "graph_designer", etc.
    action: str  # Description of fix action
    parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_improvement: str
    priority: str = "medium"  # high/medium/low

class AnalysisResult(BaseModel):
    """LLM analysis result"""
    primary_issue: str
    root_cause: str
    fix_strategy: List[FixStep]
    estimated_success_rate: float
    user_feedback: Optional[str] = None
```

#### Step 2.2: Implement Test Analyzer
**File**: `src/core/test_analyzer.py` (NEW)

**Core Structure**:
```python
class TestAnalyzer:
    """LLM-based test analyzer"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def analyze_test_report(
        self,
        report: IterationReport,
        current_config: Dict[str, Any]
    ) -> AnalysisResult:
        """Main analysis method"""
        
        # 1. Get failed test cases
        failed_cases = [tc for tc in report.test_cases 
                       if tc.status == "FAILED"]
        
        if not failed_cases:
            return self._create_success_analysis(report)
        
        # 2. Batch analysis (max 3 per batch)
        batch_analyses = []
        for batch in self._batch_test_cases(failed_cases, batch_size=3):
            analysis = await self._analyze_batch(batch, current_config)
            batch_analyses.append(analysis)
        
        # 3. Aggregate results
        final_analysis = await self._aggregate_analyses(
            batch_analyses, current_config
        )
        
        return final_analysis
    
    def _batch_test_cases(self, cases: List, batch_size: int):
        """Split cases into batches"""
        for i in range(0, len(cases), batch_size):
            yield cases[i:i + batch_size]
    
    async def _analyze_batch(self, test_cases, config):
        """Analyze single batch with LLM"""
        
        prompt = self._create_batch_analysis_prompt(test_cases, config)
        response = await self.llm.call(prompt)
        return self._parse_llm_response(response)
    
    async def _aggregate_analyses(self, batch_analyses, config):
        """Aggregate multiple batch analyses"""
        
        prompt = self._create_aggregation_prompt(batch_analyses, config)
        response = await self.llm.call(prompt)
        return AnalysisResult.model_validate_json(response)
```

#### Step 2.3: Design Analysis Prompts
**File**: `src/core/test_analyzer.py`

**Batch Analysis Prompt**:
```python
def _create_batch_analysis_prompt(self, test_cases, config):
    """Create prompt for analyzing a batch of test cases"""
    
    cases_text = "\n\n".join([
        f"Test: {tc.test_name}\n"
        f"Error: {tc.error_message}\n"
        f"Metrics: {tc.metrics}"
        for tc in test_cases
    ])
    
    return f"""# Test Failure Analysis

## Current Configuration
```json
{json.dumps(config, indent=2)}
```

## Failed Test Cases
{cases_text}

## Task
Analyze these test failures and identify:

1. **Error Type**: 
   - rag_quality (retrieval not finding relevant docs)
   - rag_config (wrong parameters like k, chunk_size)
   - logic (graph routing issues)
   - tool_config (wrong tools selected)

2. **Root Cause**: What is the fundamental problem?

3. **Fix Suggestions**: Specific actions to fix the issue

Return JSON:
{{
  "error_type": "rag_quality|rag_config|logic|tool_config",
  "root_cause": "detailed explanation",
  "fix_suggestions": [
    {{
      "target": "rag_builder|graph_designer|tool_selector",
      "action": "specific fix action",
      "parameters": {{"key": "value"}},
      "priority": "high|medium|low"
    }}
  ]
}}
"""
```

**Aggregation Prompt**:
```python
def _create_aggregation_prompt(self, batch_analyses, config):
    """Create prompt for aggregating batch analyses"""
    
    return f"""# Test Analysis Aggregation

## Batch Analyses
```json
{json.dumps(batch_analyses, indent=2)}
```

## Current Configuration
```json
{json.dumps(config, indent=2)}
```

## Task
Aggregate these analyses into a final fix strategy:

1. **Primary Issue**: What is the main problem?
2. **Fix Strategy**: Ordered list of fixes (most impactful first)
3. **Success Estimate**: Likelihood of improvement (0.0-1.0)

Return JSON:
{{
  "primary_issue": "main problem description",
  "root_cause": "fundamental cause",
  "fix_strategy": [
    {{
      "step": 1,
      "target": "rag_builder|graph_designer|tool_selector",
      "action": "what to do",
      "parameters": {{"key": "value"}},
      "expected_improvement": "what will improve",
      "priority": "high"
    }}
  ],
  "estimated_success_rate": 0.75
}}
"""
```

#### Step 2.4: Integrate into AgentFactory
**File**: `src/core/agent_factory.py`

**In `_build_and_evolve_loop`**:
```python
# After Judge analysis
judge_result = self.judge.analyze_result(test_results)

# 🆕 Add LLM analysis
test_analyzer = TestAnalyzer(self.builder_client)
current_config = {
    "graph": graph.model_dump(),
    "rag": rag_config.model_dump() if rag_config else None,
    "tools": tools_config.model_dump() if tools_config else None
}

analysis = await test_analyzer.analyze_test_report(
    iteration_report, current_config
)

# Update iteration report with analysis
iteration_report.judge_feedback = (
    f"{judge_result.feedback}\n\n"
    f"🤖 AI分析: {analysis.primary_issue}\n"
    f"📈 预计成功率: {analysis.estimated_success_rate:.1%}"
)
```

---

### Phase 3: Configuration Optimizers (Task 6.5) - 3-4 hours

#### Step 3.1: Implement RAG Optimizer
**File**: `src/core/rag_optimizer.py` (NEW)

```python
class RAGOptimizer:
    """RAG configuration optimizer"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def optimize_config(
        self,
        current_config: RAGConfig,
        analysis: AnalysisResult,
        test_report: IterationReport
    ) -> RAGConfig:
        """Optimize RAG configuration based on analysis"""
        
        # 1. Apply heuristic rules first
        new_config = current_config.model_copy()
        
        if "recall" in analysis.primary_issue.lower():
            # Low recall → increase k
            new_config.retriever_k = min(current_config.retriever_k * 2, 20)
            print(f"📊 Increasing retriever_k: {current_config.retriever_k} → {new_config.retriever_k}")
        
        if "precision" in analysis.primary_issue.lower():
            # Low precision → enable reranker or reduce k
            new_config.retriever_k = max(current_config.retriever_k // 2, 3)
        
        if "chunk" in analysis.primary_issue.lower():
            # Chunk size issues
            new_config.chunk_size = 1000  # Adjust based on analysis
        
        # 2. Use LLM for fine-tuning
        avg_recall = self._calc_avg_recall(test_report)
        avg_faithfulness = self._calc_avg_faithfulness(test_report)
        
        prompt = f"""# RAG Configuration Optimization

## Current Config
```json
{current_config.model_dump_json(indent=2)}
```

## Problem Analysis
{analysis.primary_issue}

## Test Metrics
- Average Contextual Recall: {avg_recall:.2f}
- Average Faithfulness: {avg_faithfulness:.2f}

## Task
Suggest optimal RAG parameters. Return JSON:
{{
  "chunk_size": 800,
  "chunk_overlap": 200,
  "retriever_k": 6,
  "retriever_type": "similarity|mmr|hybrid",
  "reasoning": "why these values"
}}
"""
        
        response = await self.llm.call(prompt)
        llm_config = json.loads(response)
        
        # 3. Merge heuristic + LLM suggestions
        new_config.chunk_size = llm_config.get("chunk_size", new_config.chunk_size)
        new_config.chunk_overlap = llm_config.get("chunk_overlap", new_config.chunk_overlap)
        new_config.retriever_k = llm_config.get("retriever_k", new_config.retriever_k)
        
        return new_config
    
    def _calc_avg_recall(self, report: IterationReport) -> float:
        """Calculate average contextual recall"""
        recalls = []
        for tc in report.test_cases:
            if "contextual_recall" in tc.metrics:
                recalls.append(tc.metrics["contextual_recall"])
        return sum(recalls) / len(recalls) if recalls else 0.0
    
    def _calc_avg_faithfulness(self, report: IterationReport) -> float:
        """Calculate average faithfulness"""
        scores = []
        for tc in report.test_cases:
            if "faithfulness" in tc.metrics:
                scores.append(tc.metrics["faithfulness"])
        return sum(scores) / len(scores) if scores else 0.0
```

#### Step 3.2: Integrate Optimizers into Loop
**File**: `src/core/agent_factory.py`

**In `_build_and_evolve_loop`**:
```python
# Initialize optimizers
rag_optimizer = RAGOptimizer(self.builder_client) if rag_config else None

# After analysis
for fix_step in analysis.fix_strategy:
    if fix_step.target == "rag_builder" and rag_optimizer:
        self.callback.on_log(f"🔧 Optimizing RAG configuration...")
        
        # Optimize config
        new_rag_config = await rag_optimizer.optimize_config(
            rag_config, analysis, iteration_report
        )
        
        # Show changes
        self.callback.on_log(
            f"   k: {rag_config.retriever_k} → {new_rag_config.retriever_k}\n"
            f"   chunk_size: {rag_config.chunk_size} → {new_rag_config.chunk_size}"
        )
        
        # Apply changes
        rag_config = new_rag_config
        
        # Re-compile
        self.compiler.compile(meta, graph, rag_config, tools_config, agent_dir)
        self.callback.on_log("✅ Re-compiled with new RAG config")
```

---

## 📁 File Structure

```
src/
├── schemas/
│   ├── judge_result.py         # 🔧 Modified (add error types)
│   └── analysis_result.py      # 🆕 New
├── core/
│   ├── judge.py                # 🔧 Modified (add RAG classification)
│   ├── test_analyzer.py        # 🆕 New
│   ├── rag_optimizer.py        # 🆕 New
│   └── agent_factory.py        # 🔧 Modified (integrate all)
```

---

## 🔄 Complete Iteration Flow

```
1. Run Tests
2. Create Iteration Report
3. Judge Analysis (Enhanced)
   ├─ Classify RAG errors
   ├─ Classify Tool errors
   └─ Determine fix target
4. LLM Analysis (New!)
   ├─ Batch analyze failed tests
   ├─ Aggregate results
   └─ Generate fix strategy
5. Display Results to User
   ├─ Test summary
   ├─ AI analysis
   └─ Fix strategy
6. User Confirmation
7. Execute Fix Strategy (New!)
   ├─ RAG optimization
   ├─ Tool optimization
   └─ Graph fixes
8. Re-compile
9. Git Commit
10. Loop back to step 1
```

---

## 🎯 Success Criteria

- ✅ Judge can classify RAG/Tools errors
- ✅ LLM analyzer generates actionable fix strategies
- ✅ RAG optimizer adjusts parameters based on metrics
- ✅ Full iteration loop with automatic fixes
- ✅ Pass rate improves over iterations

---

## ⏱️ Estimated Timeline

- **Phase 1** (Enhanced Judge): 2-3 hours
- **Phase 2** (LLM Analyzer): 4-5 hours
- **Phase 3** (Optimizers): 3-4 hours
- **Testing & Integration**: 2-3 hours

**Total**: 11-15 hours (1.5-2 days)

---

## 🚀 Next Steps

1. Review this plan
2. Start with Phase 1 (Enhanced Judge)
3. Test each phase before moving to next
4. Integrate all phases into complete loop
