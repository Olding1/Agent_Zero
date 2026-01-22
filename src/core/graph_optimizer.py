"""
Phase 6 Task 6.5: Graph Optimizer

Optimizes graph structure and re-validates with simulation.
"""

from typing import Tuple, Optional
from ..schemas.graph_structure import GraphStructure
from ..schemas.analysis_result import AnalysisResult
from ..schemas.project_meta import ProjectMeta
from ..schemas.simulation import SimulationResult
from .graph_designer import GraphDesigner
from .simulator import Simulator


class GraphOptimizer:
    """Graph 结构优化器
    
    修复 Graph 逻辑并重新仿真验证
    """
    
    def __init__(self, graph_designer: GraphDesigner, simulator: Simulator):
        """初始化优化器
        
        Args:
            graph_designer: Graph 设计器
            simulator: 仿真器
        """
        self.designer = graph_designer
        self.simulator = simulator
    
    async def optimize_graph(
        self,
        current_graph: GraphStructure,
        analysis: AnalysisResult,
        project_meta: ProjectMeta
    ) -> Tuple[GraphStructure, SimulationResult]:
        """优化 Graph 结构
        
        策略:
        1. 使用 GraphDesigner.fix_logic() 修复图结构
        2. **重新运行 Simulator 验证修复**
        3. 如果仍有问题,最多重试 2 次
        
        Args:
            current_graph: 当前 Graph 结构
            analysis: 分析结果
            project_meta: 项目元数据
            
        Returns:
            (优化后的 Graph, 仿真结果)
        """
        feedback = f"{analysis.primary_issue}\n{analysis.root_cause}"
        
        for attempt in range(3):  # 最多 3 次尝试
            print(f"🔧 Graph 优化尝试 {attempt + 1}/3...")
            
            # 1. 修复 Graph
            optimized_graph = await self.designer.fix_logic(
                current_graph,
                feedback=feedback
            )
            
            # 2. 🔑 重新仿真验证
            # 创建合适的样本输入
            if project_meta.has_rag:
                sample_input = "测试 RAG 检索功能"
            elif project_meta.task_type == "search":
                sample_input = "搜索测试"
            else:
                sample_input = "测试输入"
            
            sim_result = await self.simulator.simulate(
                optimized_graph,
                sample_input
            )
            
            # 3. 检查仿真结果
            if not sim_result.has_errors():
                # 仿真通过,返回优化后的 Graph
                print(f"✅ Graph 优化成功,仿真通过")
                return optimized_graph, sim_result
            else:
                # 仿真仍有问题,更新 feedback 继续尝试
                issues_desc = [i.description for i in sim_result.issues[:3]]
                feedback = f"Previous fix failed. Issues: {issues_desc}"
                current_graph = optimized_graph  # 使用修复后的作为基础
                print(f"⚠️ 仿真仍有问题: {issues_desc}")
        
        # 3 次尝试后仍失败,返回最后一次的结果
        print(f"⚠️ Graph 优化未完全成功,返回最后一次结果")
        return optimized_graph, sim_result
