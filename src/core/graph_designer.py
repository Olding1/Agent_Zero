"""Graph Designer - Three-Step Graph Design Module.

This module generates LangGraph structures using a three-step approach:
1. Pattern Selection - Choose design pattern
2. State Definition - Define state schema
3. Nodes & Edges - Design nodes and connections
"""

import yaml
from typing import Optional, List, Dict, Any
from pathlib import Path

from ..schemas import (
    GraphStructure,
    NodeDef,
    EdgeDef,
    ConditionalEdgeDef,
    ProjectMeta,
    ToolsConfig,
    RAGConfig,
    PatternConfig,
    PatternType,
    StateSchema,
    StateField,
    StateFieldType,
    SimulationResult,
    SimulationIssue,
)
from ..llm import BuilderClient


class GraphDesigner:
    """Graph Designer generates LangGraph structures using three-step method.
    
    The Graph Designer follows a three-step process:
    1. Select Pattern - Choose appropriate design pattern
    2. Define State - Create state schema
    3. Design Graph - Generate nodes and edges
    """
    
    def __init__(self, builder_client: BuilderClient):
        """Initialize Graph Designer with a builder client.
        
        Args:
            builder_client: LLM client for graph design
        """
        self.builder = builder_client
        self.pattern_templates = self._load_pattern_templates()
    
    def _load_pattern_templates(self) -> Dict[PatternType, Dict[str, Any]]:
        """Load pattern templates from YAML files.
        
        Returns:
            Dict mapping PatternType to template configuration
        """
        templates = {}
        patterns_dir = Path(__file__).parent.parent.parent / "config" / "patterns"
        
        if not patterns_dir.exists():
            print(f"Warning: Patterns directory not found: {patterns_dir}")
            return templates
        
        pattern_files = {
            PatternType.SEQUENTIAL: "sequential.yaml",
            PatternType.REFLECTION: "reflection.yaml",
            PatternType.SUPERVISOR: "supervisor.yaml",
            PatternType.PLAN_EXECUTE: "plan_execute.yaml",
        }
        
        for pattern_type, filename in pattern_files.items():
            file_path = patterns_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        templates[pattern_type] = yaml.safe_load(f)
                except Exception as e:
                    print(f"Warning: Failed to load {filename}: {e}")
        
        return templates
    
    # ==================== Step 1: Pattern Selection ====================
    
    async def select_pattern(
        self,
        project_meta: ProjectMeta
    ) -> PatternConfig:
        """Step 1: Select appropriate design pattern.
        
        Args:
            project_meta: Project metadata
            
        Returns:
            PatternConfig
        """
        # Use heuristics to select pattern
        pattern_type = self._heuristic_pattern_selection(project_meta)
        
        # Get template config
        template = self.pattern_templates.get(pattern_type, {})
        
        # Create PatternConfig
        pattern = PatternConfig(
            pattern_type=pattern_type,
            max_iterations=3,  # Default
            description=template.get("description", "")
        )
        
        return pattern
    
    def _heuristic_pattern_selection(self, project_meta: ProjectMeta) -> PatternType:
        """Heuristic-based pattern selection.
        
        Args:
            project_meta: Project metadata
            
        Returns:
            PatternType
        """
        # Check execution plan for complexity
        if project_meta.execution_plan and len(project_meta.execution_plan) > 3:
            # Complex multi-step task -> Plan-Execute
            return PatternType.PLAN_EXECUTE
        
        # Check for iteration/refinement keywords
        desc_lower = (project_meta.description + project_meta.user_intent_summary).lower()
        
        if any(word in desc_lower for word in ['迭代', '改进', '优化', '审核', '修改', 
                                                 'iterate', 'improve', 'refine', 'review', 'revise']):
            # Needs iteration -> Reflection
            return PatternType.REFLECTION
        
        # Check for multiple tools
        if project_meta.complexity_score >= 6:
            # Complex with tools -> Supervisor
            return PatternType.SUPERVISOR
        
        # Default to Sequential
        return PatternType.SEQUENTIAL
    
    # ==================== Step 2: State Definition ====================
    
    async def define_state_schema(
        self,
        project_meta: ProjectMeta,
        pattern: PatternConfig
    ) -> StateSchema:
        """Step 2: Define state schema.
        
        Args:
            project_meta: Project metadata
            pattern: Selected pattern
            
        Returns:
            StateSchema
        """
        # Start with base fields
        fields = self._get_base_state_fields()
        
        # Add pattern-specific fields
        pattern_fields = self._get_pattern_state_fields(pattern)
        fields.extend(pattern_fields)
        
        # Add RAG-specific fields if needed
        if project_meta.has_rag:
            fields.extend(self._get_rag_state_fields())
        
        return StateSchema(fields=fields)
    
    def _get_base_state_fields(self) -> List[StateField]:
        """Get base state fields required for all patterns."""
        return [
            StateField(
                name="messages",
                type=StateFieldType.LIST_MESSAGE,
                description="对话历史",
                reducer="add_messages"
            ),
            StateField(
                name="is_finished",
                type=StateFieldType.BOOL,
                description="是否完成任务",
                default=False
            )
        ]
    
    def _get_pattern_state_fields(self, pattern: PatternConfig) -> List[StateField]:
        """Get pattern-specific state fields."""
        fields = []
        
        if pattern.pattern_type == PatternType.REFLECTION:
            fields.extend([
                StateField(name="draft", type=StateFieldType.STRING, default=""),
                StateField(name="feedback", type=StateFieldType.STRING, default=""),
                StateField(name="iteration_count", type=StateFieldType.INT, default=0),
                StateField(name="max_iterations", type=StateFieldType.INT, default=pattern.max_iterations)
            ])
        
        elif pattern.pattern_type == PatternType.SUPERVISOR:
            fields.extend([
                StateField(name="next_action", type=StateFieldType.STRING, default=""),
                StateField(name="tool_results", type=StateFieldType.DICT, default={})
            ])
        
        elif pattern.pattern_type == PatternType.PLAN_EXECUTE:
            fields.extend([
                StateField(name="plan", type=StateFieldType.LIST_STR, default=[]),
                StateField(name="current_step", type=StateFieldType.INT, default=0),
                StateField(name="execution_results", type=StateFieldType.LIST_STR, default=[]),
                StateField(name="need_replan", type=StateFieldType.BOOL, default=False)
            ])
        
        return fields
    
    def _get_rag_state_fields(self) -> List[StateField]:
        """Get RAG-specific state fields."""
        return [
            StateField(
                name="retrieved_docs",
                type=StateFieldType.LIST_STR,
                description="检索到的文档",
                default=[]
            ),
            StateField(
                name="context",
                type=StateFieldType.STRING,
                description="RAG上下文",
                default=""
            ),
            # 🆕 v7.2: LLM 语义路由字段
            StateField(
                name="router_decision",
                type=StateFieldType.OPTIONAL_STR,
                description="路由决策结果: 'SEARCH' 或 'CHAT'",
                default=None
            )
        ]
    
    # ==================== Step 3: Nodes & Edges Design ====================
    
    async def design_nodes_and_edges(
        self,
        project_meta: ProjectMeta,
        pattern: PatternConfig,
        state_schema: StateSchema,
        tools_config: Optional[ToolsConfig] = None,
        rag_config: Optional[RAGConfig] = None
    ) -> GraphStructure:
        """Step 3: Design nodes and edges.
        
        Args:
            project_meta: Project metadata
            pattern: Selected pattern
            state_schema: State schema
            tools_config: Optional tools configuration
            rag_config: Optional RAG configuration
            
        Returns:
            GraphStructure
        """
        # Get base structure from pattern template
        template = self.pattern_templates.get(pattern.pattern_type, {})
        
        nodes = self._create_nodes_from_template(template, pattern)
        edges = self._create_edges_from_template(template)
        conditional_edges = self._create_conditional_edges_from_template(template, pattern)
        
        # Add RAG node if needed (Router Pattern)
        if project_meta.has_rag and rag_config:
            rag_nodes, rag_edges, rag_cond_edges = self._add_rag_integration(nodes, rag_config)
            nodes.extend(rag_nodes)  # 🆕 v7.2: 添加 Router 和 RAG 节点
            edges.extend(rag_edges)
            conditional_edges.extend(rag_cond_edges)
        
        # Add tool nodes if needed
        if tools_config and tools_config.enabled_tools:
            tool_nodes, tool_edges = self._add_tool_integration(
                nodes, tools_config, pattern
            )
            nodes.extend(tool_nodes)
            
            # Update conditional edges for tools
            if pattern.pattern_type == PatternType.SUPERVISOR:
                conditional_edges = self._update_supervisor_edges(
                    conditional_edges, tools_config
                )
        
        # 🆕 v7.2: 如果有 RAG,Entry Point 应该是 intent_router
        entry_point = template.get("entry_point", nodes[0].id if nodes else "agent")
        if project_meta.has_rag and rag_config:
            # 检查是否有 intent_router 节点
            if any(n.id == "intent_router" for n in nodes):
                entry_point = "intent_router"
        
        return GraphStructure(
            pattern=pattern,
            state_schema=state_schema,
            nodes=nodes,
            edges=edges,
            conditional_edges=conditional_edges,
            entry_point=entry_point
        )
    
    def _create_nodes_from_template(
        self,
        template: Dict[str, Any],
        pattern: PatternConfig
    ) -> List[NodeDef]:
        """Create nodes from pattern template."""
        nodes = []
        default_nodes = template.get("default_nodes", [])
        
        for node_def in default_nodes:
            nodes.append(NodeDef(
                id=node_def["id"],
                type=node_def["type"],
                role_description=node_def.get("role_description"),
                config=node_def.get("config")
            ))
        
        return nodes
    
    def _create_edges_from_template(self, template: Dict[str, Any]) -> List[EdgeDef]:
        """Create edges from pattern template."""
        edges = []
        default_edges = template.get("default_edges", [])
        
        for edge_def in default_edges:
            edges.append(EdgeDef(
                source=edge_def["source"],
                target=edge_def["target"]
            ))
        
        return edges
    
    def _create_conditional_edges_from_template(
        self,
        template: Dict[str, Any],
        pattern: PatternConfig
    ) -> List[ConditionalEdgeDef]:
        """Create conditional edges from pattern template."""
        conditional_edges = []
        default_cond_edges = template.get("default_conditional_edges", [])
        
        for edge_def in default_cond_edges:
            conditional_edges.append(ConditionalEdgeDef(
                source=edge_def["source"],
                condition=edge_def["condition"],
                condition_logic=edge_def.get("condition_logic"),
                branches=edge_def["branches"]
            ))
        
        return conditional_edges
    
    def _add_rag_integration(
        self,
        existing_nodes: List[NodeDef],
        rag_config: RAGConfig
    ) -> tuple[List[NodeDef], List[EdgeDef], List[ConditionalEdgeDef]]:
        """Add RAG node with LLM-based Intent Router Pattern (v7.2).
        
        New Flow:
        - START -> intent_router (LLM分类)
        - intent_router -> [SEARCH: rag_retriever | CHAT: agent]
        - rag_retriever -> agent -> END
        
        Returns:
            Tuple of (new_nodes, edges, conditional_edges)
        """
        # 1. 创建 Intent Router 节点 (新增)
        router_node = NodeDef(
            id="intent_router",
            type="llm",
            role_description="""你是一个路由助手。分析用户输入,判断是否需要查询知识库。

规则:
- 如果用户在询问事实性问题、请求文档信息、或需要查找资料,输出 'SEARCH'
- 如果用户只是打招呼、闲聊、或进行简单对话,输出 'CHAT'
- 只输出 'SEARCH' 或 'CHAT',不要输出其他内容

示例:
- "Agent Zero 的核心特性是什么?" -> SEARCH
- "具体步骤?" -> SEARCH  
- "你好" -> CHAT
- "谢谢" -> CHAT""",
            config={"is_router": True}  # 标记为路由节点
        )
        
        # 2. 创建 RAG 检索节点
        rag_node = NodeDef(
            id="rag_retriever",
            type="rag",
            role_description="检索相关文档并返回给 Agent",
            config={
                "splitter": rag_config.splitter,
                "chunk_size": rag_config.chunk_size,
                "k_retrieval": rag_config.k_retrieval
            }
        )
        
        # 找到主 Agent 节点
        llm_nodes = [n for n in existing_nodes if n.type == "llm"]
        if not llm_nodes:
            return [router_node, rag_node], [], []
        
        agent_id = llm_nodes[0].id
        
        # 3. 构建边
        edges = [
            EdgeDef(
                source="rag_retriever",
                target=agent_id,
                description="RAG 检索完成后返回 Agent"
            ),
            EdgeDef(
                source=agent_id,
                target="END",
                description="Agent 回答后结束"
            )
        ]
        
        # 4. Router 的条件边 (基于 LLM 输出)
        conditional_edges = [
            ConditionalEdgeDef(
                source="intent_router",
                condition="route_by_intent",
                condition_logic="""# LLM 语义路由 (v7.2)
# 检查 Router 节点的输出决策
messages = state.get("messages", [])

if not messages:
    return "chat"

# 获取 Router 的输出 (最后一条 AI 消息)
last_message = messages[-1]
decision = ""

if hasattr(last_message, 'content'):
    decision = last_message.content.strip().upper()
elif isinstance(last_message, dict):
    decision = last_message.get("content", "").strip().upper()

# 根据 Router 的决策路由
if "SEARCH" in decision:
    return "search"
else:
    return "chat"
""",
                branches={
                    "search": "rag_retriever",  # 需要检索
                    "chat": agent_id             # 直接对话
                }
            )
        ]
        
        # 返回新节点列表、边、条件边
        return [router_node, rag_node], edges, conditional_edges

    
    def _add_tool_integration(
        self,
        existing_nodes: List[NodeDef],
        tools_config: ToolsConfig,
        pattern: PatternConfig
    ) -> tuple[List[NodeDef], List[EdgeDef]]:
        """Add tool nodes and edges."""
        tool_nodes = []
        tool_edges = []
        
        for tool_name in tools_config.enabled_tools:
            tool_node = NodeDef(
                id=f"tool_{tool_name}",
                type="tool",
                role_description=f"执行{tool_name}工具",
                config={"tool_name": tool_name}
            )
            tool_nodes.append(tool_node)
            
            # For non-supervisor patterns, add return edges
            if pattern.pattern_type != PatternType.SUPERVISOR:
                # Find main agent node
                agent_nodes = [n for n in existing_nodes if n.type == "llm"]
                if agent_nodes:
                    tool_edges.append(EdgeDef(
                        source=f"tool_{tool_name}",
                        target=agent_nodes[0].id
                    ))
        
        return tool_nodes, tool_edges
    
    def _update_supervisor_edges(
        self,
        conditional_edges: List[ConditionalEdgeDef],
        tools_config: ToolsConfig
    ) -> List[ConditionalEdgeDef]:
        """Update supervisor conditional edges with tool branches."""
        # Find supervisor routing edge
        for edge in conditional_edges:
            if edge.condition == "route_to_worker":
                # Add tool branches
                for tool_name in tools_config.enabled_tools:
                    edge.branches[tool_name] = f"tool_{tool_name}"
        
        return conditional_edges
    
    # ==================== Main Entry Point ====================
    
    async def design_graph(
        self,
        project_meta: ProjectMeta,
        tools_config: Optional[ToolsConfig] = None,
        rag_config: Optional[RAGConfig] = None,
    ) -> GraphStructure:
        """Design graph structure using three-step method.
        
        This is the main entry point that orchestrates the three steps.
        
        Args:
            project_meta: Project metadata
            tools_config: Optional tools configuration
            rag_config: Optional RAG configuration
            
        Returns:
            GraphStructure
        """
        # Step 1: Select Pattern
        pattern = await self.select_pattern(project_meta)
        
        # Step 2: Define State
        state_schema = await self.define_state_schema(project_meta, pattern)
        
        # Step 3: Design Nodes & Edges
        graph = await self.design_nodes_and_edges(
            project_meta, pattern, state_schema, tools_config, rag_config
        )
        
        return graph
    
    # ==================== Utility Methods ====================
    
    def save_graph(self, graph: GraphStructure, output_path) -> None:
        """Save graph structure to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(graph.model_dump_json(indent=2))
    
    def load_graph(self, input_path) -> GraphStructure:
        """Load graph structure from JSON file."""
        input_path = Path(input_path)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            return GraphStructure.model_validate_json(f.read())

    async def fix_logic(
        self,
        current_graph: GraphStructure,
        simulation_result: Optional[SimulationResult] = None,
        feedback: Optional[str] = None
    ) -> GraphStructure:
        """根据仿真结果或反馈修复图结构
        
        Args:
            current_graph: 当前图结构
            simulation_result: 仿真结果 (可选)
            feedback: 文本反馈 (可选)
            
        Returns:
            修复后的图结构
        """
        # 构建 Prompt
        issues_desc = ""
        if simulation_result and simulation_result.issues:
            issues_desc += "Simulation Issues:\n"
            for issue in simulation_result.issues:
                issues_desc += f"- [{issue.severity}] {issue.issue_type}: {issue.description}\n"
                if issue.suggestion:
                    issues_desc += f"  Suggestion: {issue.suggestion}\n"
        
        if feedback:
            issues_desc += f"\nExternal Feedback:\n{feedback}\n"
            
        if not issues_desc:
            return current_graph
            
        prompt = f"""# Graph Repair Task

## Current Graph
Pattern: {current_graph.pattern.pattern_type}
Nodes: {', '.join(n.id for n in current_graph.nodes)}

## Issues Detected
{issues_desc}

## Requirement
Please fix the graph structure based on the issues above.
Focus on:
1. Breaking infinite loops (e.g., adding iteration limits)
2. Connecting unreachable nodes
3. Fixing logic errors in conditional edges

## CRITICAL CONSTRAINTS

### 1. Node Targets - Use 'END' for termination
All edge targets MUST be either:
- Actual node IDs from the nodes list above
- The special node "END" (all caps) to terminate the workflow

DO NOT use variants like '__end__', 'end', '__start__', or 'START'.
If you need to end the workflow, use "END" (all caps).

### 2. State Field Types - MUST use exact enum values
type MUST be one of: "str", "int", "bool", "float", "List[BaseMessage]", "List[str]", "Dict[str, Any]", "Optional[str]", "Optional[int]", "Any"
FORBIDDEN: "Optional[List[str]]", "List[Dict]", or custom strings

### 3. Condition Logic - Define all variables first
All variables in condition_logic MUST be defined in state_schema.fields.
Use: state['variable_name'] syntax.

### 4. Prevent Infinite Loops
Add iteration counters with max limits for any loops.

Return the full updated GraphStructure JSON.
"""
        
        # 调用 LLM 修复
        response = await self.builder.call(prompt, schema=GraphStructure)
        
        # 🔧 后处理: 统一特殊节点为 "END"
        if isinstance(response, dict):
            response = self._normalize_special_nodes(response)
            return GraphStructure(**response)
        return response
    
    def _normalize_special_nodes(self, graph_dict: dict) -> dict:
        """将所有特殊节点名统一为 'END'
        
        LLM 可能生成 '__end__', 'end', '__END__' 等变体,
        统一转换为 LangGraph 标准的 'END'
        
        Args:
            graph_dict: Graph 字典
            
        Returns:
            规范化后的 Graph 字典
        """
        END_VARIANTS = ['__end__', 'end', '__END__', '_end_', 'End', '__end', 'end__']
        
        # 处理 conditional_edges
        for edge in graph_dict.get('conditional_edges', []):
            branches = edge.get('branches', {})
            for key, value in list(branches.items()):
                if value in END_VARIANTS:
                    branches[key] = "END"
                    print(f"🔧 [GraphDesigner] 规范化节点: '{value}' → 'END'")
        
        # 处理 regular edges
        for edge in graph_dict.get('edges', []):
            if edge.get('target') in END_VARIANTS:
                print(f"🔧 [GraphDesigner] 规范化节点: '{edge['target']}' → 'END'")
                edge['target'] = "END"
        
        return graph_dict
