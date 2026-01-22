"""
Phase 6 Task 6.3: Test Analyzer

LLM-based intelligent test analyzer for generating fix strategies.
"""

import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..llm.builder_client import BuilderClient
from ..schemas.test_report import IterationReport, TestCaseReport
from ..schemas.analysis_result import AnalysisResult, FixStep


class TestAnalyzer:
    """基于 LLM 的测试分析器
    
    分析测试报告,生成智能修复策略
    """
    
    def __init__(self, llm_client: BuilderClient):
        """初始化分析器
        
        Args:
            llm_client: Builder LLM 客户端
        """
        self.llm = llm_client
    
    async def analyze_test_report(
        self,
        report: IterationReport,
        current_config: Dict[str, Any]
    ) -> AnalysisResult:
        """分析测试报告
        
        简化版: 直接分析所有失败用例,不分批
        
        Args:
            report: 迭代报告
            current_config: 当前配置 (graph, rag, tools)
            
        Returns:
            分析结果
        """
        # 1. 提取失败的测试 (兼容 FAIL 和 FAILED)
        failed_cases = [
            tc for tc in report.test_cases 
            if tc.status.upper() in ["FAIL", "FAILED", "ERROR"]
        ]
        
        if not failed_cases:
            return self._create_success_analysis(report)
        
        # 2. 构建分析 Prompt
        prompt = self._create_analysis_prompt(failed_cases, current_config, report)
        
        # 3. 调用 LLM
        try:
            response = await self.llm.call(prompt)
            
            # 4. 解析结果
            return self._parse_analysis_response(response)
        except Exception as e:
            # LLM 调用失败,返回默认分析
            return AnalysisResult(
                primary_issue=f"LLM 分析失败: {str(e)}",
                root_cause="无法调用 LLM 进行智能分析",
                fix_strategy=[],
                estimated_success_rate=0.0
            )
    
    def _create_analysis_prompt(
        self,
        failed_cases: List[TestCaseReport],
        config: Dict[str, Any],
        report: IterationReport
    ) -> str:
        """创建分析 Prompt
        
        Args:
            failed_cases: 失败的测试用例
            config: 当前配置
            report: 迭代报告
            
        Returns:
            Prompt 字符串
        """
        # 格式化失败用例
        cases_text = ""
        for i, tc in enumerate(failed_cases, 1):
            error_preview = (tc.error_message[:200] if tc.error_message else "无")
            cases_text += f"""
测试 {i}: {tc.test_name}
- 状态: {tc.status}
- 错误: {error_preview}
- 指标: {tc.metrics}
"""
        
        return f"""# 测试失败分析任务

## 当前配置
```json
{json.dumps(config, indent=2, ensure_ascii=False)}
```

## 测试统计
- 总测试数: {report.total_tests}
- 通过: {report.passed_tests}
- 失败: {report.failed_tests}
- 通过率: {report.pass_rate:.1%}

## 失败的测试用例
{cases_text}

## 任务要求
请分析这些测试失败的根本原因,并给出修复建议:

1. **错误类型判断**:
   - rag_quality: RAG 检索质量不足 (Recall 低, Faithfulness 低)
   - rag_config: RAG 配置问题 (chunk_size, retriever_k 不合适)
   - logic: Graph 逻辑问题 (节点缺失, 路由错误)
   - tool_config: 工具配置问题

2. **修复建议**:
   - 需要修改哪些配置参数?
   - 需要调整 Graph 结构吗?
   - 优先级如何排序?

3. **预期效果**:
   - 每个修复预计带来多少改进?
   - 整体成功率估计?

请以 JSON 格式返回:
{{
  "primary_issue": "主要问题描述",
  "root_cause": "详细的根因分析",
  "fix_strategy": [
    {{
      "step": 1,
      "target": "rag_builder|graph_designer|tool_selector|compiler",
      "action": "具体的修复动作",
      "parameters": {{"key": "value"}},
      "expected_improvement": "预期改进效果",
      "priority": "high|medium|low"
    }}
  ],
  "estimated_success_rate": 0.75
}}
"""
    
    def _parse_analysis_response(self, response: str) -> AnalysisResult:
        """解析 LLM 响应
        
        Args:
            response: LLM 响应文本
            
        Returns:
            解析后的分析结果
        """
        # 提取 JSON (处理 markdown 代码块)
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析
            json_str = response
        
        try:
            data = json.loads(json_str)
            return AnalysisResult.model_validate(data)
        except Exception as e:
            # 回退: 返回默认分析
            return AnalysisResult(
                primary_issue="LLM 响应解析失败",
                root_cause=f"无法解析 LLM 响应: {str(e)}\n\n原始响应:\n{response[:500]}",
                fix_strategy=[],
                estimated_success_rate=0.0
            )
    
    def _create_success_analysis(self, report: IterationReport) -> AnalysisResult:
        """创建成功分析结果
        
        Args:
            report: 迭代报告
            
        Returns:
            成功的分析结果
        """
        return AnalysisResult(
            primary_issue="所有测试通过",
            root_cause="Agent 运行正常,无需修复",
            fix_strategy=[],
            estimated_success_rate=1.0
        )
