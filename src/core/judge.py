"""
Judge - DeepEval 结果分析器

负责:
1. 分析 DeepEval 测试结果
2. 分类错误类型 (RUNTIME, LOGIC, TIMEOUT, API)
3. 生成修复建议
4. 确定修复目标 (Compiler 或 Graph Designer)
"""

from typing import Optional, List, Dict, Any
from src.schemas.execution_result import ExecutionResult, ExecutionStatus
from src.schemas.judge_result import JudgeResult, ErrorType, FixTarget


class Judge:
    """DeepEval 结果分析器
    
    分析测试结果,提供修复建议
    """
    
    def __init__(self):
        """初始化 Judge"""
        pass
    
    def analyze_result(
        self,
        execution_result: ExecutionResult
    ) -> JudgeResult:
        """分析执行结果
        
        Args:
            execution_result: 执行结果
        
        Returns:
            JudgeResult 包含分析和建议
        """
        # 1. 检查执行状态
        if execution_result.overall_status == ExecutionStatus.PASS:
            return JudgeResult(
                error_type=ErrorType.NONE,
                fix_target=FixTarget.NONE,
                feedback="✅ 所有测试通过!",
                suggestions=[],
                should_retry=False
            )
        
        # 2. 分类错误
        error_type = self._classify_error(execution_result)
        
        # 3. 确定修复目标
        fix_target = self._determine_fix_target(error_type, execution_result)
        
        # 4. 生成反馈和建议
        feedback, suggestions = self._generate_feedback(
            error_type,
            execution_result
        )
        
        # 5. 判断是否应该重试
        should_retry = error_type in [ErrorType.TIMEOUT, ErrorType.API]
        
        return JudgeResult(
            error_type=error_type,
            fix_target=fix_target,
            feedback=feedback,
            suggestions=suggestions,
            should_retry=should_retry
        )
    
    def _classify_error(self, result: ExecutionResult) -> ErrorType:
        """分类错误类型
        
        Args:
            result: 执行结果
        
        Returns:
            ErrorType
        """
        # 🆕 Phase 6: 先尝试 RAG 错误分类
        rag_error = self._classify_rag_error(result)
        if rag_error:
            return rag_error
        
        # 超时
        if result.overall_status == ExecutionStatus.TIMEOUT:
            return ErrorType.TIMEOUT
        
        # 检查错误信息 (使用 stderr 和 test_results)
        error_msg = (result.stderr or "").lower()
        
        # 从 test_results 中提取错误信息
        test_errors = ""
        if result.test_results:
            for test in result.test_results:
                if hasattr(test, 'error_message') and test.error_message:
                    test_errors += test.error_message.lower() + " "
        
        combined = error_msg + test_errors
        
        # API 错误
        if any(keyword in combined for keyword in [
            "api key", "rate limit", "connection error",
            "timeout", "network", "http error"
        ]):
            return ErrorType.API
        
        # 运行时错误
        if any(keyword in combined for keyword in [
            "syntaxerror", "importerror", "modulenotfounderror",
            "nameerror", "attributeerror", "typeerror"
        ]):
            return ErrorType.RUNTIME
        
        # DeepEval 特定错误
        if "faithfulness" in combined or "contextualrecall" in combined:
            return ErrorType.LOGIC
        
        # 默认为逻辑错误
        return ErrorType.LOGIC
    
    def _classify_rag_error(self, result: ExecutionResult) -> Optional[ErrorType]:
        """🆕 Phase 6: 识别 RAG 相关错误
        
        启发式规则:
        - 如果多个测试都失败在 "contextual_recall" → RAG_QUALITY
        - 如果错误信息包含 "retrieval context is empty" → RAG_CONFIG
        - 如果 "faithfulness" 失败 → RAG_QUALITY
        
        Args:
            result: 执行结果
            
        Returns:
            RAG 错误类型或 None
        """
        rag_failures = []
        
        for test in result.test_results:
            if test.status in [ExecutionStatus.FAIL, ExecutionStatus.FAILED]:
                error_msg = (test.error_message or "").lower()
                
                # 检测 RAG 相关失败
                if "contextual recall" in error_msg or "contextualrecall" in error_msg:
                    rag_failures.append("low_recall")
                elif "faithfulness" in error_msg:
                    rag_failures.append("low_faithfulness")
                elif "empty" in error_msg and "context" in error_msg:
                    rag_failures.append("empty_context")
                elif "retrieval" in error_msg:
                    rag_failures.append("retrieval_issue")
        
        # 如果有 3+ 个 RAG 相关失败
        if len(rag_failures) >= 3:
            if "empty_context" in rag_failures:
                return ErrorType.RAG_CONFIG  # 配置问题
            else:
                return ErrorType.RAG_QUALITY  # 质量问题
        
        return None
    
    def _determine_fix_target(
        self,
        error_type: ErrorType,
        result: ExecutionResult
    ) -> FixTarget:
        """确定修复目标
        
        Args:
            error_type: 错误类型
            result: 执行结果
        
        Returns:
            FixTarget
        """
        if error_type == ErrorType.RUNTIME:
            # 运行时错误 -> Compiler 修复
            return FixTarget.COMPILER
        
        # 🆕 Phase 6: RAG 错误 -> RAG Builder 优化
        elif error_type in [ErrorType.RAG_QUALITY, ErrorType.RAG_CONFIG]:
            return FixTarget.RAG_BUILDER
        
        # 🆕 Phase 6: 工具错误 -> Tool Selector 优化
        elif error_type in [ErrorType.TOOL_ERROR, ErrorType.TOOL_CONFIG]:
            return FixTarget.TOOL_SELECTOR
        
        elif error_type == ErrorType.LOGIC:
            # 逻辑错误 -> Graph Designer 修复
            return FixTarget.GRAPH_DESIGNER
        
        elif error_type in [ErrorType.TIMEOUT, ErrorType.API]:
            # 超时或 API 错误 -> 人工处理
            return FixTarget.MANUAL
        
        return FixTarget.NONE
    
    def _generate_feedback(
        self,
        error_type: ErrorType,
        result: ExecutionResult
    ) -> tuple[str, List[str]]:
        """生成反馈和建议
        
        Args:
            error_type: 错误类型
            result: 执行结果
        
        Returns:
            (feedback, suggestions)
        """
        if error_type == ErrorType.RUNTIME:
            return self._feedback_runtime(result)
        elif error_type == ErrorType.LOGIC:
            return self._feedback_logic(result)
        elif error_type == ErrorType.TIMEOUT:
            return self._feedback_timeout(result)
        elif error_type == ErrorType.API:
            return self._feedback_api(result)
        else:
            return ("未知错误", [])
    
    def _feedback_runtime(self, result: ExecutionResult) -> tuple[str, List[str]]:
        """运行时错误反馈"""
        error_msg = result.stderr or ""
        
        feedback = f"❌ 运行时错误: 代码生成有问题\n\n{error_msg[:500]}"
        
        suggestions = [
            "检查生成的 agent.py 是否有语法错误",
            "检查导入语句是否正确",
            "检查 requirements.txt 中的依赖是否完整",
            "建议: 让 Compiler 重新生成代码"
        ]
        
        # 具体错误类型的建议
        if "importerror" in error_msg.lower():
            suggestions.insert(0, "缺少依赖包,检查 requirements.txt")
        elif "syntaxerror" in error_msg.lower():
            suggestions.insert(0, "代码有语法错误,检查模板生成逻辑")
        
        return feedback, suggestions
    
    def _feedback_logic(self, result: ExecutionResult) -> tuple[str, List[str]]:
        """逻辑错误反馈"""
        # 提取失败的测试
        failed_tests = [
            test for test in result.test_results
            if test.status == ExecutionStatus.FAIL
        ]
        
        feedback = f"❌ 逻辑错误: {len(failed_tests)} 个测试失败"
        
        suggestions = []
        
        # 分析失败的测试
        for test in failed_tests[:3]:  # 只分析前3个
            test_id = test.test_id
            error = test.error_message or ""
            
            if 'faithfulness' in test_id.lower() or 'faithfulness' in error.lower():
                suggestions.append("Faithfulness 失败: LLM 输出与检索文档不一致,检查 RAG 提示词")
            elif 'recall' in test_id.lower() or 'recall' in error.lower():
                suggestions.append("Recall 失败: 检索到的文档不包含答案,检查检索策略")
            elif 'tool' in test_id.lower():
                suggestions.append("工具调用失败: 检查工具选择和调用逻辑")
        
        if not suggestions:
            suggestions = [
                "检查 Graph 结构是否合理",
                "检查节点之间的连接是否正确",
                "检查条件边的逻辑是否正确",
                "建议: 让 Graph Designer 重新设计图结构"
            ]
        
        return feedback, suggestions
    
    def _feedback_timeout(self, result: ExecutionResult) -> tuple[str, List[str]]:
        """超时反馈"""
        # 计算总执行时间
        total_duration = sum(test.duration_ms for test in result.test_results) / 1000.0
        
        feedback = f"⏱️ 测试执行超时 ({total_duration:.1f}秒)"
        
        suggestions = [
            "检查是否有死循环或无限递归",
            "检查 LLM 调用是否卡住",
            "考虑增加超时时间",
            "检查网络连接是否正常"
        ]
        
        return feedback, suggestions
    
    def _feedback_api(self, result: ExecutionResult) -> tuple[str, List[str]]:
        """API 错误反馈"""
        error_msg = result.stderr or ""
        
        feedback = f"🌐 API 调用失败\n\n{error_msg[:300]}"
        
        suggestions = []
        
        if "api key" in error_msg.lower():
            suggestions.append("检查 .env 文件中的 API Key 是否正确")
        if "rate limit" in error_msg.lower():
            suggestions.append("API 调用频率超限,等待后重试")
        if "connection" in error_msg.lower() or "network" in error_msg.lower():
            suggestions.append("网络连接问题,检查网络或代理设置")
        
        if not suggestions:
            suggestions = [
                "检查 API 配置是否正确",
                "检查网络连接",
                "稍后重试"
            ]
        
        return feedback, suggestions
    
    def generate_fix_prompt(
        self,
        judge_result: JudgeResult,
        original_context: Dict[str, Any]
    ) -> Optional[str]:
        """生成修复 Prompt (给 Compiler 或 Graph Designer)
        
        Args:
            judge_result: Judge 分析结果
            original_context: 原始上下文 (ProjectMeta, GraphStructure 等)
        
        Returns:
            修复 Prompt 或 None
        """
        if judge_result.fix_target == FixTarget.NONE:
            return None
        
        if judge_result.fix_target == FixTarget.COMPILER:
            return self._generate_compiler_fix_prompt(judge_result, original_context)
        elif judge_result.fix_target == FixTarget.GRAPH_DESIGNER:
            return self._generate_graph_designer_fix_prompt(judge_result, original_context)
        else:
            return None
    
    def _generate_compiler_fix_prompt(
        self,
        judge_result: JudgeResult,
        context: Dict[str, Any]
    ) -> str:
        """生成 Compiler 修复 Prompt"""
        return f"""# Compiler 修复任务

## 问题
{judge_result.feedback}

## 建议
{chr(10).join(f"- {s}" for s in judge_result.suggestions)}

## 要求
请修复代码生成逻辑,确保生成的 agent.py 能够正常运行。

## 原始配置
{context}

请重新生成正确的代码。
"""
    
    def _generate_graph_designer_fix_prompt(
        self,
        judge_result: JudgeResult,
        context: Dict[str, Any]
    ) -> str:
        """生成 Graph Designer 修复 Prompt"""
        return f"""# Graph Designer 修复任务

## 问题
{judge_result.feedback}

## 建议
{chr(10).join(f"- {s}" for s in judge_result.suggestions)}

## 要求
请重新设计 Agent 的图结构,修复逻辑问题。

## 原始配置
{context}

请生成改进的 GraphStructure。
"""
