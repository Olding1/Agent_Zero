"""
Phase 6 Task 6.5: Tool Optimizer

Optimizes tool selection based on test analysis results.
"""

from typing import List, Optional
from ..llm.builder_client import BuilderClient
from ..schemas.tools_config import ToolsConfig
from ..schemas.analysis_result import AnalysisResult
from ..schemas.project_meta import ProjectMeta
from .tool_selector import ToolSelector


class ToolOptimizer:
    """工具配置优化器
    
    重新选择更合适的工具
    """
    
    def __init__(self, llm_client: BuilderClient, tool_selector: ToolSelector):
        """初始化优化器
        
        Args:
            llm_client: Builder LLM 客户端
            tool_selector: 工具选择器
        """
        self.llm = llm_client
        self.tool_selector = tool_selector
    
    async def optimize_tools(
        self,
        current_config: ToolsConfig,
        analysis: AnalysisResult,
        project_meta: ProjectMeta
    ) -> ToolsConfig:
        """优化工具选择
        
        策略:
        1. 分析失败原因是否与工具相关
        2. 重新运行 ToolSelector 选择更合适的工具
        3. 保留有效的工具,替换无效的工具
        
        Args:
            current_config: 当前工具配置
            analysis: 分析结果
            project_meta: 项目元数据
            
        Returns:
            优化后的工具配置
        """
        # 1. 检查是否需要优化工具
        if "tool" not in analysis.primary_issue.lower():
            return current_config  # 不是工具问题,不优化
        
        # 2. 提取失败的工具调用
        failed_tools = self._extract_failed_tools(analysis)
        
        # 3. 重新选择工具
        new_config = await self.tool_selector.select_tools(
            project_meta,
            max_tools=5
        )
        
        # 4. 合并: 保留成功的工具,替换失败的工具
        optimized_tools = []
        for tool in current_config.enabled_tools:
            if tool not in failed_tools:
                optimized_tools.append(tool)  # 保留成功的工具
        
        # 添加新选择的工具
        for tool in new_config.enabled_tools:
            if tool not in optimized_tools:
                optimized_tools.append(tool)
        
        print(f"🔧 工具优化: {current_config.enabled_tools} → {optimized_tools[:5]}")
        
        return ToolsConfig(enabled_tools=optimized_tools[:5])
    
    def _extract_failed_tools(self, analysis: AnalysisResult) -> List[str]:
        """从分析结果中提取失败的工具名称
        
        Args:
            analysis: 分析结果
            
        Returns:
            失败的工具列表
        """
        failed_tools = []
        # 从 root_cause 和 primary_issue 中提取工具名
        text = f"{analysis.primary_issue} {analysis.root_cause}".lower()
        
        # 常见工具名称
        common_tools = ["tavily_search", "python_repl", "llm_math", "file_read", "file_write"]
        for tool in common_tools:
            if tool in text:
                failed_tools.append(tool)
        
        return failed_tools
