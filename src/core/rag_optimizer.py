"""
Phase 6 Task 6.5: RAG Optimizer

Optimizes RAG configuration based on test analysis results.
"""

import json
from typing import Optional, Dict, Any
from pathlib import Path

from ..llm.builder_client import BuilderClient
from ..schemas.rag_config import RAGConfig
from ..schemas.analysis_result import AnalysisResult
from ..schemas.test_report import IterationReport


class RAGOptimizer:
    """RAG 配置优化器
    
    结合启发式规则和 LLM 智能建议优化 RAG 配置
    """
    
    def __init__(self, llm_client: BuilderClient):
        """初始化优化器
        
        Args:
            llm_client: Builder LLM 客户端
        """
        self.llm = llm_client
    
    async def optimize_config(
        self,
        current_config: RAGConfig,
        analysis: AnalysisResult,
        test_report: IterationReport
    ) -> RAGConfig:
        """优化 RAG 配置
        
        策略:
        1. 先应用启发式规则 (快速)
        2. 再使用 LLM 微调 (智能)
        
        Args:
            current_config: 当前 RAG 配置
            analysis: LLM 分析结果
            test_report: 测试报告
            
        Returns:
            优化后的 RAG 配置
        """
        new_config = current_config.model_copy()
        
        # 1. 启发式规则
        if "recall" in analysis.primary_issue.lower():
            # Recall 低 → 增加检索文档数 或 启用混合检索
            current_k = current_config.k_retrieval
            
            if current_k >= 10 and not current_config.enable_hybrid_search:
                # k 已经很大了，但 recall 还是低 -> 架构升级: 混合检索
                new_config.enable_hybrid_search = True
                new_config.k_retrieval = 15 # 混合检索通常可以召回更多
                print(f"⚡ [Optimizer] 架构升级: 激活混合检索 (Hybrid Search)")
            else:
                # 简单增加 k
                new_config.k_retrieval = min(current_k * 2, 30)
                print(f"📊 启发式调整: k_retrieval {current_k} → {new_config.k_retrieval}")
        
        if "precision" in analysis.primary_issue.lower() or "faithfulness" in analysis.primary_issue.lower():
            # Precision/Faithfulness 低 → 启用重排序 (Rerank)
            if not current_config.reranker_enabled:
                # 架构升级: 重排序
                new_config.reranker_enabled = True
                new_config.reranker_provider = "flashrank" # 默认使用轻量级
                new_config.k_retrieval = max(current_config.k_retrieval, 10) # Rerank 需要较大的候选集
                print(f"⚡ [Optimizer] 架构升级: 激活重排序 (Flashrank)")
            else:
                # 已经有 Rerank 了，可能需要更小的 chunk 或更精准的 k
                new_config.chunk_size = max(current_config.chunk_size - 200, 400)
                print(f"📊 启发式调整: chunk_size → {new_config.chunk_size}")

        if "chunk" in analysis.primary_issue.lower():
             # Chunk 大小问题
             pass # 让 LLM 处理，或者简单的启发式
        
        # 2. LLM 微调 (可选)
        if self.llm:
            try:
                llm_config = await self._llm_optimize(
                    current_config,
                    new_config,
                    analysis,
                    test_report
                )
                # 合并 LLM 建议
                if llm_config:
                    new_config = llm_config
            except Exception as e:
                print(f"⚠️ LLM 优化失败,使用启发式结果: {str(e)}")
        
        return new_config
    
    async def _llm_optimize(
        self,
        current_config: RAGConfig,
        heuristic_config: RAGConfig,
        analysis: AnalysisResult,
        test_report: IterationReport
    ) -> Optional[RAGConfig]:
        """使用 LLM 优化配置
        
        Args:
            current_config: 当前配置
            heuristic_config: 启发式调整后的配置
            analysis: 分析结果
            test_report: 测试报告
            
        Returns:
            优化后的配置或 None
        """
        # 计算平均指标
        avg_recall = self._calc_avg_metric(test_report, "contextual_recall")
        avg_faithfulness = self._calc_avg_metric(test_report, "faithfulness")
        
        prompt = f"""# RAG 配置优化任务

## 当前配置
- chunk_size: {current_config.chunk_size}
- chunk_overlap: {current_config.chunk_overlap}
- k_retrieval: {current_config.k_retrieval}
- retriever_type: {current_config.retriever_type}

## 启发式调整后的配置
- chunk_size: {heuristic_config.chunk_size}
- chunk_overlap: {heuristic_config.chunk_overlap}
- k_retrieval: {heuristic_config.k_retrieval}

## 问题分析
- 主要问题: {analysis.primary_issue}
- 根本原因: {analysis.root_cause}

## 测试指标
- 通过率: {test_report.pass_rate:.1%}
- 平均 Contextual Recall: {avg_recall:.2f}
- 平均 Faithfulness: {avg_faithfulness:.2f}

## 最佳实践约束 (Best Practices):

1. **Chunk Size**: 
   - 除非文档结构非常特殊，否则**不要超过 600**。
   - 推荐范围：**300 - 500**。
   - 原因：小切片能提高语义密度，减少噪音。

2. **Retrieval K**:
   - 如果 chunk_size 较小 (<500)，可以大胆增加 K 值 (20-40)。
   - 如果 chunk_size 较大 (>800)，必须减小 K 值 (<10)。

3. **如果 Recall 低**:
   - 优先减小 chunk_size (切碎一点)，同时增加 K。
   - 不要盲目增大 chunk_size。

## 极端情况处理指南 (Emergency Protocol):

1. **如果 Contextual Recall 依然为 0.0**:
   - 检查 `k_retrieval`: 如果已经 > 30，**停止增加 K 值**（噪音太大）。
   - **强烈建议**: 将 `chunk_size` 调整到 1000 以上（保留完整语义）或者 300 以下（精准匹配）。
   - **必须**: 在 `reasoning` 中指出："可能需要 Graph Designer 增强 query_rewriter 的 Prompt，或者检查源文档解析是否丢失数据"。

2. **如果 Faithfulness 为 0.0**:
   - 必须启用 `reranker_enabled`。
   - 减小 `chunk_size`。

## 任务
请给出最优的 RAG 配置参数。考虑:
1. 如果 Recall 低,增加 k_retrieval
2. 如果 Faithfulness 低,可能需要调整 chunk_size
3. chunk_overlap 通常是 chunk_size 的 10-20%

返回 JSON:
{{
  "chunk_size": 800,
  "chunk_overlap": 200,
  "k_retrieval": 6,
  "reasoning": "为什么选择这些参数"
}}
"""
        
        try:
            response = await self.llm.call(prompt)
            
            # 解析响应
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
            
            data = json.loads(json_str)
            
            # 更新配置
            optimized = heuristic_config.model_copy()
            optimized.chunk_size = data.get("chunk_size", optimized.chunk_size)
            optimized.chunk_overlap = data.get("chunk_overlap", optimized.chunk_overlap)
            optimized.k_retrieval = data.get("k_retrieval", optimized.k_retrieval)
            
            print(f"🤖 LLM 优化建议: {data.get('reasoning', 'N/A')}")
            
            return optimized
        except Exception as e:
            print(f"⚠️ LLM 优化解析失败: {str(e)}")
            return heuristic_config
    
    def _calc_avg_metric(self, report: IterationReport, metric_name: str) -> float:
        """计算平均指标
        
        Args:
            report: 测试报告
            metric_name: 指标名称
            
        Returns:
            平均值
        """
        values = []
        for tc in report.test_cases:
            if metric_name in tc.metrics:
                values.append(tc.metrics[metric_name])
        
        return sum(values) / len(values) if values else 0.0
