"""Simulator - Blueprint Simulation Module.

This module simulates agent execution flow before code generation,
allowing early detection of logic issues like infinite loops.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..schemas import (
    GraphStructure,
    SimulationResult,
    SimulationStep,
    SimulationIssue,
    SimulationStepType,
    StateField,
)
from ..llm import BuilderClient


class Simulator:
    """Simulator performs blueprint simulation of graph structures.
    
    The Simulator:
    1. Simulates graph execution with sample input
    2. Tracks state changes through each node
    3. Detects logic issues (infinite loops, unreachable nodes)
    4. Generates execution traces and visualizations
    """
    
    def __init__(self, llm_client: BuilderClient):
        """Initialize Simulator with LLM client.
        
        Args:
            llm_client: LLM client for simulating node execution
        """
        self.llm = llm_client
    
    async def simulate(
        self,
        graph: GraphStructure,
        sample_input: str,
        max_steps: int = 20,
        use_llm: bool = True
    ) -> SimulationResult:
        """Simulate graph execution.
        
        Args:
            graph: Graph structure to simulate
            sample_input: Sample user input
            max_steps: Maximum simulation steps
            use_llm: Whether to use real LLM for node simulation (default: True)
            
        Returns:
            SimulationResult with execution trace and issues
        """
        # Initialize state
        state = self._initialize_state(graph.state_schema)
        state["messages"] = [{"role": "user", "content": sample_input}]
        
        # Simulation log
        steps: List[SimulationStep] = []
        visited_nodes: Dict[str, int] = {}
        
        # Start from entry point
        current_node = graph.entry_point
        step_count = 0
        
        while step_count < max_steps:
            step_count += 1
            
            # Track node visits
            visited_nodes[current_node] = visited_nodes.get(current_node, 0) + 1
            
            # Check for infinite loop
            if visited_nodes[current_node] > 5:
                steps.append(SimulationStep(
                    step_number=step_count,
                    step_type=SimulationStepType.ENTER_NODE,
                    node_id=current_node,
                    description=f"⚠️ 检测到无限循环：节点 {current_node} 访问超过5次",
                    state_snapshot=state.copy()
                ))
                break
            
            # Enter node
            steps.append(SimulationStep(
                step_number=step_count,
                step_type=SimulationStepType.ENTER_NODE,
                node_id=current_node,
                description=f"进入节点: {current_node}",
                state_snapshot=state.copy()
            ))
            
            # Find node definition
            node_def = self._find_node(graph, current_node)
            if not node_def:
                break
            
            # Simulate node execution
            state = await self._simulate_node(node_def, state, sample_input, use_llm)
            
            # Exit node
            steps.append(SimulationStep(
                step_number=step_count + 0.5,
                step_type=SimulationStepType.EXIT_NODE,
                node_id=current_node,
                description=f"退出节点: {current_node}",
                state_snapshot=state.copy()
            ))
            
            # Determine next node
            next_node = self._get_next_node(graph, current_node, state)
            
            if next_node == "END" or next_node is None:
                steps.append(SimulationStep(
                    step_number=step_count + 1,
                    step_type=SimulationStepType.EDGE_TRAVERSE,
                    description="到达终点 END",
                    state_snapshot=state.copy()
                ))
                break
            
            # Traverse edge
            steps.append(SimulationStep(
                step_number=step_count + 1,
                step_type=SimulationStepType.EDGE_TRAVERSE,
                description=f"从 {current_node} 到 {next_node}",
                state_snapshot=state.copy()
            ))
            
            current_node = next_node
        
        # Detect issues
        issues = self.detect_issues(steps, graph, visited_nodes)
        
        # Generate traces
        execution_trace = self.generate_readable_log(steps)
        mermaid_trace = self.generate_mermaid_trace(steps, graph)
        
        # Determine success
        success = len(issues) == 0 or not any(i.severity == "error" for i in issues)
        
        return SimulationResult(
            success=success,
            total_steps=len(steps),
            steps=steps,
            issues=issues,
            final_state=state,
            execution_trace=execution_trace,
            mermaid_trace=mermaid_trace,
            simulated_at=datetime.now()
        )
    
    def _initialize_state(self, state_schema) -> Dict[str, Any]:
        """Initialize state with default values."""
        state = {}
        
        for field in state_schema.fields:
            if field.default is not None:
                state[field.name] = field.default
            elif field.type.value == "List[BaseMessage]":
                state[field.name] = []
            elif field.type.value == "List[str]":
                state[field.name] = []
            elif field.type.value == "Dict[str, Any]":
                state[field.name] = {}
            elif field.type.value == "int":
                state[field.name] = 0
            elif field.type.value == "bool":
                state[field.name] = False
            else:
                state[field.name] = None
        
        return state
    
    def _find_node(self, graph: GraphStructure, node_id: str):
        """Find node definition by ID."""
        for node in graph.nodes:
            if node.id == node_id:
                return node
        return None
    
    async def _simulate_node(
        self,
        node_def,
        state: Dict[str, Any],
        sample_input: str,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """Simulate node execution.
        
        Args:
            node_def: Node definition
            state: Current state
            sample_input: Sample user input
            use_llm: Whether to use real LLM (True) or heuristic simulation (False)
        
        Returns:
            Updated state
        """
        if node_def.type == "llm" and use_llm:
            # Use real LLM for simulation
            try:
                messages = state.get("messages", [])
                
                # Build prompt for LLM simulation
                role_desc = node_def.role_description or f"You are {node_def.id} node"
                
                prompt = f"""You are simulating the execution of a LangGraph node.

Node: {node_def.id}
Role: {role_desc}
Current State: {self._format_state_for_llm(state)}

User Input: {sample_input}

Please provide a brief response (1-2 sentences) as this node would respond.
Focus on the node's specific role in the workflow."""

                response = await self.llm.call(prompt=prompt)
                
                # Update state with LLM response
                state["messages"].append({
                    "role": "assistant",
                    "content": response
                })
                
                # Update pattern-specific fields based on response
                if "draft" in state:
                    state["draft"] = response
                if "feedback" in state and "critic" in node_def.id.lower():
                    state["feedback"] = response
                
            except Exception as e:
                print(f"Warning: LLM simulation failed for {node_def.id}, using heuristic: {e}")
                # Fallback to heuristic
                state["messages"].append({
                    "role": "assistant",
                    "content": f"[模拟] {node_def.id} 的响应"
                })
        
        elif node_def.type == "llm":
            # Heuristic simulation for LLM nodes
            state["messages"].append({
                "role": "assistant",
                "content": f"[模拟] {node_def.id} 的响应"
            })
            
            # Update pattern-specific fields
            if "draft" in state:
                state["draft"] = f"Draft from {node_def.id}"
            if "feedback" in state:
                state["feedback"] = f"Feedback from {node_def.id}"
        
        elif node_def.type == "tool":
            # Simulate tool execution
            tool_name = node_def.config.get("tool_name", "unknown") if node_def.config else "unknown"
            state["tool_results"] = state.get("tool_results", {})
            state["tool_results"][tool_name] = f"[模拟] {tool_name} 结果"
        
        elif node_def.type == "rag":
            # Simulate RAG retrieval
            state["retrieved_docs"] = ["Doc1", "Doc2", "Doc3"]
            state["context"] = "[模拟] RAG上下文"
            
            # Add ToolMessage to indicate RAG has been called (Router Pattern)
            state["messages"].append({
                "type": "tool",
                "role": "tool",
                "content": "[模拟] RAG检索结果: 找到3个相关文档"
            })
        
        # Update iteration count if exists
        if "iteration_count" in state:
            state["iteration_count"] += 1
        
        # Update current step if exists
        if "current_step" in state:
            state["current_step"] += 1
        
        return state
    
    def _format_state_for_llm(self, state: Dict[str, Any]) -> str:
        """Format state for LLM prompt."""
        # Only include key fields, avoid verbose data
        formatted = {}
        for key, value in state.items():
            if key == "messages":
                formatted[key] = f"{len(value)} messages"
            elif isinstance(value, (str, int, bool)):
                formatted[key] = value
            elif isinstance(value, list):
                formatted[key] = f"[{len(value)} items]"
            elif isinstance(value, dict):
                formatted[key] = f"{{...}}"
        
        return str(formatted)
    
    def _get_next_node(
        self,
        graph: GraphStructure,
        current_node: str,
        state: Dict[str, Any]
    ) -> Optional[str]:
        """Determine next node based on edges."""
        # Check conditional edges first
        for cond_edge in graph.conditional_edges:
            if cond_edge.source == current_node:
                # Evaluate condition
                next_node = self._evaluate_condition(cond_edge, state)
                if next_node:
                    return next_node
        
        # Check regular edges
        for edge in graph.edges:
            if edge.source == current_node:
                return edge.target
        
        # No edge found, assume END
        return "END"
    
    def _evaluate_condition(self, cond_edge, state: Dict[str, Any]) -> Optional[str]:
        """Evaluate conditional edge.
        
        Supports both heuristic evaluation and condition_logic execution.
        """
        if cond_edge.condition_logic:
            try:
                # Wrap condition logic in a function to return value
                wrapped_code = f"""
def check_condition(state):
    # Safe globals
    import json
    
    # User logic
{'\n'.join('    ' + line for line in cond_edge.condition_logic.split('\n'))}
"""
                # Create execution environment
                exec_globals = {}
                exec(wrapped_code, exec_globals)
                
                # Execute the function
                check_condition = exec_globals['check_condition']
                result = check_condition(state)
                
                if result in cond_edge.branches:
                    return cond_edge.branches[result]
                    
            except Exception as e:
                print(f"Warning: Failed to execute condition_logic: {e}")
        
        # Fallback to heuristic evaluation
        return self._heuristic_evaluate_condition(cond_edge, state)
    
    def _heuristic_evaluate_condition(self, cond_edge, state: Dict[str, Any]) -> Optional[str]:
        """Heuristic-based condition evaluation."""
        # Check iteration count
        if "iteration_count" in state and "max_iterations" in state:
            if state["iteration_count"] >= state["max_iterations"]:
                return cond_edge.branches.get("end", "END")
            else:
                # Continue iteration
                for key in cond_edge.branches:
                    if key != "end":
                        return cond_edge.branches[key]
        
        # Check is_finished
        if state.get("is_finished", False):
            return cond_edge.branches.get("end", "END")
        
        # Check plan completion
        if "current_step" in state and "plan" in state:
            if state["current_step"] >= len(state["plan"]):
                return cond_edge.branches.get("end", "END")
        
        # Router Pattern: Check if RAG has been called
        if "search" in cond_edge.branches and "finish" in cond_edge.branches:
            # This is a Router Pattern conditional edge
            messages = state.get("messages", [])
            
            # Check if we have ToolMessage (RAG has been called)
            has_tool_message = any(
                isinstance(msg, dict) and msg.get("type") == "tool"
                for msg in messages
            )
            
            if has_tool_message:
                # RAG has been called, finish
                return cond_edge.branches.get("finish", "END")
            else:
                # First time, need to search
                return cond_edge.branches.get("search")
        
        # Default: return first non-end branch
        for key, value in cond_edge.branches.items():
            if key != "end":
                return value
        
        return "END"
    
    def detect_issues(
        self,
        simulation_log: List[SimulationStep],
        graph: GraphStructure,
        visited_nodes: Dict[str, int]
    ) -> List[SimulationIssue]:
        """Detect issues in simulation."""
        issues = []
        
        # Check for infinite loops
        for node_id, visit_count in visited_nodes.items():
            if visit_count > 5:
                issues.append(SimulationIssue(
                    issue_type="infinite_loop",
                    severity="error",
                    description=f"检测到无限循环：节点 '{node_id}' 被访问了 {visit_count} 次",
                    affected_nodes=[node_id],
                    suggestion="添加迭代计数器并设置最大迭代次数"
                ))
        
        # Check for unreachable nodes
        all_node_ids = {node.id for node in graph.nodes}
        visited_node_ids = set(visited_nodes.keys())
        unreachable = all_node_ids - visited_node_ids
        
        if unreachable:
            issues.append(SimulationIssue(
                issue_type="unreachable_node",
                severity="warning",
                description=f"发现不可达节点：{', '.join(unreachable)}",
                affected_nodes=list(unreachable),
                suggestion="检查边的连接是否正确"
            ))
        
        return issues
    
    def generate_mermaid_trace(
        self,
        simulation_log: List[SimulationStep],
        graph: GraphStructure
    ) -> str:
        """Generate Mermaid diagram of execution trace."""
        lines = ["graph LR"]
        
        # Track transitions
        transitions = []
        prev_node = None
        
        for step in simulation_log:
            if step.step_type == SimulationStepType.ENTER_NODE and step.node_id:
                if prev_node and prev_node != step.node_id:
                    transitions.append((prev_node, step.node_id))
                prev_node = step.node_id
        
        # Generate Mermaid syntax
        for i, (source, target) in enumerate(transitions):
            lines.append(f"    {source}[{source}] -->|{i+1}| {target}[{target}]")
        
        return "\n".join(lines)
    
    def generate_readable_log(
        self,
        simulation_log: List[SimulationStep]
    ) -> str:
        """Generate readable execution trace."""
        lines = ["=== 仿真执行轨迹 ===\n"]
        
        for step in simulation_log:
            step_num = int(step.step_number) if step.step_number == int(step.step_number) else step.step_number
            lines.append(f"Step {step_num}: {step.description}")
        
        return "\n".join(lines)
