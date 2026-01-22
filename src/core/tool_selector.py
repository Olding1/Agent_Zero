"""Tool Selector - Selects appropriate tools based on requirements."""

from typing import List, Optional

from ..schemas import ProjectMeta, ToolsConfig
from ..tools import ToolRegistry, get_global_registry
from ..llm import BuilderClient


class ToolSelector:
    """Tool Selector chooses appropriate tools based on project requirements.
    
    The Tool Selector is responsible for:
    1. Analyzing project requirements
    2. Matching requirements to available tools
    3. Selecting top-K most relevant tools
    4. Outputting ToolsConfig
    """
    
    def __init__(
        self,
        builder_client: BuilderClient,
        registry: Optional[ToolRegistry] = None
    ):
        """Initialize Tool Selector.
        
        Args:
            builder_client: LLM client for tool selection
            registry: Tool registry (uses global if not provided)
        """
        self.builder = builder_client
        self.registry = registry or get_global_registry()
    
    async def select_tools(
        self,
        project_meta: ProjectMeta,
        max_tools: int = 5
    ) -> ToolsConfig:
        """Select tools based on project requirements.
        
        Args:
            project_meta: Project metadata
            max_tools: Maximum number of tools to select
            
        Returns:
            ToolsConfig with selected tools
        """
        # Use heuristic selection first
        selected_tools = self._heuristic_selection(project_meta, max_tools)
        
        # Optionally refine with LLM
        try:
            refined_tools = await self._llm_refine_selection(
                project_meta, selected_tools, max_tools
            )
            return ToolsConfig(enabled_tools=refined_tools)
        except Exception as e:
            print(f"Warning: LLM refinement failed, using heuristic selection: {e}")
            return ToolsConfig(enabled_tools=selected_tools)
    
    def _heuristic_selection(
        self,
        project_meta: ProjectMeta,
        max_tools: int
    ) -> List[str]:
        """Select tools using heuristic rules.
        
        Args:
            project_meta: Project metadata
            max_tools: Maximum number of tools
            
        Returns:
            List of selected tool names
        """
        # Build search query from project description and intent
        query = f"{project_meta.description} {project_meta.user_intent_summary}"
        
        # Search for matching tools
        matching_tools = self.registry.search(query, top_k=max_tools * 2)
        
        # Apply task-type specific rules
        selected = []
        
        # For SEARCH tasks, prioritize search tools
        if project_meta.task_type == "search":
            search_tools = self.registry.list_tools(category="search")
            for tool in search_tools:
                if tool in matching_tools and tool not in selected:
                    selected.append(tool)
        
        # For ANALYSIS tasks, prioritize code/math tools
        elif project_meta.task_type == "analysis":
            code_tools = self.registry.list_tools(category="code")
            math_tools = self.registry.list_tools(category="math")
            
            for tool in code_tools + math_tools:
                if tool in matching_tools and tool not in selected:
                    selected.append(tool)
        
        # Add remaining matching tools
        for tool in matching_tools:
            if tool not in selected:
                selected.append(tool)
            
            if len(selected) >= max_tools:
                break
        
        return selected[:max_tools]
    
    async def _llm_refine_selection(
        self,
        project_meta: ProjectMeta,
        candidate_tools: List[str],
        max_tools: int
    ) -> List[str]:
        """Refine tool selection using LLM.
        
        Args:
            project_meta: Project metadata
            candidate_tools: Candidate tool names
            max_tools: Maximum number of tools
            
        Returns:
            Refined list of tool names
        """
        # Get tool descriptions
        tool_descriptions = []
        for tool_name in candidate_tools:
            metadata = self.registry.get_metadata(tool_name)
            if metadata:
                tool_descriptions.append(
                    f"- {tool_name}: {metadata.description}"
                )
        
        prompt = self._build_selection_prompt(
            project_meta, tool_descriptions, max_tools
        )
        
        response = await self.builder.call(prompt=prompt)
        
        # Parse tool names from response
        selected_tools = self._parse_tool_names(response, candidate_tools)
        
        return selected_tools[:max_tools]
    
    def _build_selection_prompt(
        self,
        project_meta: ProjectMeta,
        tool_descriptions: List[str],
        max_tools: int
    ) -> str:
        """Build prompt for LLM tool selection.
        
        Args:
            project_meta: Project metadata
            tool_descriptions: List of tool descriptions
            max_tools: Maximum number of tools
            
        Returns:
            Prompt string
        """
        tools_text = "\n".join(tool_descriptions)
        
        prompt = f"""You are selecting tools for an AI agent.

Project Information:
- Agent name: {project_meta.agent_name}
- Description: {project_meta.description}
- Task type: {project_meta.task_type}
- User intent: {project_meta.user_intent_summary}

Available Tools:
{tools_text}

Select up to {max_tools} most relevant tools for this agent.
Consider:
1. What capabilities does the agent need?
2. Which tools best match the task type?
3. Are there any redundant tools?

Output only the tool names, one per line, in order of importance.
"""
        return prompt
    
    def _parse_tool_names(
        self,
        response: str,
        candidate_tools: List[str]
    ) -> List[str]:
        """Parse tool names from LLM response.
        
        Args:
            response: LLM response text
            candidate_tools: List of valid tool names
            
        Returns:
            List of parsed tool names
        """
        lines = response.strip().split('\n')
        selected = []
        
        for line in lines:
            line = line.strip()
            
            # Remove numbering, bullets, etc.
            import re
            cleaned = re.sub(r'^[\d\.\-\*\)]+\s*', '', line)
            cleaned = cleaned.strip()
            
            # Check if it matches a candidate tool
            for tool in candidate_tools:
                if tool.lower() in cleaned.lower():
                    if tool not in selected:
                        selected.append(tool)
                    break
        
        return selected
    
    def save_config(self, config: ToolsConfig, output_path) -> None:
        """Save tools config to JSON file.
        
        Args:
            config: ToolsConfig to save
            output_path: Path to save JSON file
        """
        from pathlib import Path
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(config.model_dump_json(indent=2))
    
    def load_config(self, input_path) -> ToolsConfig:
        """Load tools config from JSON file.
        
        Args:
            input_path: Path to JSON file
            
        Returns:
            ToolsConfig object
        """
        from pathlib import Path
        input_path = Path(input_path)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            return ToolsConfig.model_validate_json(f.read())
