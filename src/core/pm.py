"""PM (Product Manager) - Requirements Analyzer.

This module serves as the system's "brain" for understanding user intent.
It analyzes natural language requirements and outputs structured project metadata.
"""

import json
import re
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from ..schemas import ProjectMeta, TaskType, ExecutionStep
from ..llm import BuilderClient


class PM:
    """PM (Product Manager) - Analyzes user requirements and outputs structured metadata.
    
    The PM module is responsible for:
    1. Understanding user's natural language requirements
    2. Determining task type (CHAT/SEARCH/RAG/ANALYSIS)
    3. Identifying if RAG is needed
    4. Asking clarification questions if requirements are ambiguous
    5. Outputting structured ProjectMeta
    """
    
    def __init__(self, builder_client: BuilderClient):
        """Initialize PM with a builder client.
        
        Args:
            builder_client: LLM client for requirement analysis
        """
        self.builder = builder_client
        self.conversation_history: List[Dict[str, str]] = []
    
    async def analyze_requirements(
        self,
        user_input: str,
        file_paths: Optional[List[Path]] = None,
    ) -> ProjectMeta:
        """Analyze user requirements and return structured project metadata.
        
        Args:
            user_input: User's natural language requirement description
            file_paths: Optional list of file paths user wants to use
            
        Returns:
            ProjectMeta: Structured project metadata
        """
        # Add user input to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(user_input, file_paths)
        
        # Call LLM with structured output
        try:
            response = await self.builder.call(
                prompt=prompt,
                schema=ProjectMeta
            )
            
            # Parse response as ProjectMeta
            if isinstance(response, str):
                project_meta = ProjectMeta.model_validate_json(response)
            else:
                project_meta = response
            
            # Add file paths if provided
            if file_paths:
                project_meta.file_paths = [str(p) for p in file_paths]
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": f"Analysis complete: {project_meta.agent_name}"
            })
            
            return project_meta
            
        except Exception as e:
            # Fallback to basic parsing if structured output fails
            print(f"Warning: Structured output failed, using fallback: {e}")
            return await self._fallback_analysis(user_input, file_paths)
    
    async def ask_clarification(
        self,
        project_meta: ProjectMeta
    ) -> List[str]:
        """Generate clarification questions if requirements are ambiguous.
        
        Args:
            project_meta: Current project metadata
            
        Returns:
            List of clarification questions
        """
        if not project_meta.clarification_needed:
            return []
        
        prompt = self._build_clarification_prompt(project_meta)
        
        try:
            response = await self.builder.call(prompt=prompt)
            
            # Parse questions from response
            questions = self._parse_questions(response)
            return questions
            
        except Exception as e:
            print(f"Error generating clarification questions: {e}")
            return []
    
    async def refine_with_clarification(
        self,
        project_meta: ProjectMeta,
        clarification_answers: Dict[str, str]
    ) -> ProjectMeta:
        """Refine project metadata with clarification answers.
        
        Args:
            project_meta: Current project metadata
            clarification_answers: Dict mapping questions to answers
            
        Returns:
            Refined ProjectMeta
        """
        # Build refinement prompt
        prompt = self._build_refinement_prompt(project_meta, clarification_answers)
        
        try:
            response = await self.builder.call(
                prompt=prompt,
                schema=ProjectMeta
            )
            
            if isinstance(response, str):
                refined_meta = ProjectMeta.model_validate_json(response)
            else:
                refined_meta = response
            
            # Mark as no longer needing clarification
            refined_meta.clarification_needed = False
            refined_meta.clarification_questions = None
            
            return refined_meta
            
        except Exception as e:
            print(f"Error refining metadata: {e}")
            # Return original if refinement fails
            project_meta.clarification_needed = False
            return project_meta
    
    def _build_analysis_prompt(
        self,
        user_input: str,
        file_paths: Optional[List[Path]] = None
    ) -> str:
        """Build prompt for requirement analysis."""
        
        file_info = ""
        if file_paths:
            file_info = f"\n\nUser has provided {len(file_paths)} file(s):\n"
            for fp in file_paths:
                file_info += f"- {fp.name} ({fp.suffix})\n"
        
        prompt = f"""You are a Product Manager analyzing user requirements for building an AI agent.

User's requirement:
{user_input}
{file_info}

Your task is to analyze this requirement and output structured metadata in JSON format.

Consider:
1. What type of task is this? (chat, search, analysis, rag, custom)
2. Does it need RAG (Retrieval-Augmented Generation)? 
   - If user provides documents/files, likely needs RAG
   - If user wants to query knowledge base, needs RAG
3. What should the agent be named?
4. Is the requirement clear enough, or do we need clarification?

Output a JSON object with this structure:
{{
    "agent_name": "descriptive_agent_name",
    "description": "Clear description of what the agent does",
    "has_rag": true/false,
    "task_type": "chat/search/analysis/rag/custom",
    "language": "zh-CN or en-US",
    "user_intent_summary": "Summary of user's intent",
    "file_paths": null,
    "clarification_needed": true/false,
    "clarification_questions": ["question1", "question2"] or null
}}

Be concise and accurate. If the requirement is clear, set clarification_needed to false.
"""
        return prompt
    
    def _build_clarification_prompt(self, project_meta: ProjectMeta) -> str:
        """Build prompt for generating clarification questions."""
        
        prompt = f"""Based on this project metadata:

Agent Name: {project_meta.agent_name}
Description: {project_meta.description}
Task Type: {project_meta.task_type}
Has RAG: {project_meta.has_rag}

The requirement needs clarification. Generate 2-3 specific questions to clarify:
- Exact functionality needed
- Expected behavior (input/output format)
- Any specific business rules

IMPORTANT:
- DO NOT ask about technology stack (we ALREADY use LangGraph + Python).
- DO NOT ask about underlying LLM (we handle that).
- Focus on BUSINESS LOGIC and USER EXPERIENCE.

Output only the questions, one per line, numbered.
"""
        return prompt
    
    def _build_refinement_prompt(
        self,
        project_meta: ProjectMeta,
        clarification_answers: Dict[str, str]
    ) -> str:
        """Build prompt for refining metadata with clarification answers."""
        
        answers_text = "\n".join([
            f"Q: {q}\nA: {a}"
            for q, a in clarification_answers.items()
        ])
        
        prompt = f"""Original project metadata:
{project_meta.model_dump_json(indent=2)}

Clarification Q&A:
{answers_text}

Based on the clarification answers, refine the project metadata.
Output the complete refined JSON object with the same structure.
Set clarification_needed to false.
"""
        return prompt
    
    def _parse_questions(self, response: str) -> List[str]:
        """Parse questions from LLM response."""
        lines = response.strip().split('\n')
        questions = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering like "1. ", "1) ", etc.
            import re
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
            if cleaned:
                questions.append(cleaned)
        
        return questions
    
    async def _fallback_analysis(
        self,
        user_input: str,
        file_paths: Optional[List[Path]] = None
    ) -> ProjectMeta:
        """Fallback analysis if structured output fails."""
        
        # Simple heuristic-based analysis
        has_rag = bool(file_paths) or any(
            keyword in user_input.lower() 
            for keyword in ['文档', 'document', 'pdf', '知识库', 'knowledge']
        )
        
        # Determine task type
        if has_rag:
            task_type = TaskType.RAG
        elif any(keyword in user_input.lower() for keyword in ['搜索', 'search']):
            task_type = TaskType.SEARCH
        elif any(keyword in user_input.lower() for keyword in ['分析', 'analysis']):
            task_type = TaskType.ANALYSIS
        else:
            task_type = TaskType.CHAT
        
        # Detect language
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in user_input)
        language = "zh-CN" if has_chinese else "en-US"
        
        return ProjectMeta(
            agent_name="custom_agent",
            description=user_input[:200],  # Truncate if too long
            has_rag=has_rag,
            task_type=task_type,
            language=language,
            user_intent_summary=user_input[:100],
            file_paths=[str(p) for p in file_paths] if file_paths else None,
            clarification_needed=False,
        )
    
    def save_project_meta(self, project_meta: ProjectMeta, output_path: Path) -> None:
        """Save project metadata to JSON file.
        
        Args:
            project_meta: Project metadata to save
            output_path: Path to save JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(project_meta.model_dump_json(indent=2))
    
    def load_project_meta(self, input_path: Path) -> ProjectMeta:
        """Load project metadata from JSON file.
        
        Args:
            input_path: Path to JSON file
            
        Returns:
            ProjectMeta object
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            return ProjectMeta.model_validate_json(f.read())
    
    # ==================== PM Dual-Brain Mode Methods ====================
    
    async def clarify_requirements(
        self,
        user_query: str,
        chat_history: Optional[List[Dict]] = None
    ) -> Tuple[bool, Optional[List[str]]]:
        """PM Clarifier: Check requirement completeness.
        
        Args:
            user_query: User's requirement description
            chat_history: Optional conversation history
            
        Returns:
            Tuple of (is_ready, clarification_questions)
            - is_ready: True if requirements are clear enough (>= 80%)
            - clarification_questions: List of questions if not ready
        """
        # Load clarifier prompt
        prompt_path = Path(__file__).parent.parent / "prompts" / "pm_clarifier.txt"
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                clarifier_prompt_template = f.read()
        except FileNotFoundError:
            # Fallback to inline prompt
            clarifier_prompt_template = self._get_default_clarifier_prompt()
        
        # Build context
        history_text = ""
        if chat_history:
            history_text = "\n\nConversation History:\n"
            for msg in chat_history[-3:]:  # Last 3 messages
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"
        
        prompt = f"{clarifier_prompt_template}\n\n## Current Task\n\nUser Query: {user_query}{history_text}\n\nAnalyze the completeness and output JSON with: {{\"is_ready\": bool, \"completeness_score\": int, \"clarification_questions\": [...]}}"  
        
        try:
            response = await self.builder.call(prompt=prompt)
            
            # Parse JSON response
            result = self._extract_json(response)
            
            is_ready = result.get("is_ready", False)
            questions = result.get("clarification_questions", [])
            
            return (is_ready, questions if not is_ready else None)
            
        except Exception as e:
            print(f"Warning: Clarifier failed, using heuristic: {e}")
            # Fallback: simple heuristic
            return self._heuristic_clarify(user_query)
    
    async def create_execution_plan(
        self,
        project_meta: ProjectMeta
    ) -> List[ExecutionStep]:
        """PM Planner: Generate hierarchical task breakdown.
        
        Args:
            project_meta: Project metadata with clear requirements
            
        Returns:
            List of ExecutionStep objects
        """
        # Load planner prompt
        prompt_path = Path(__file__).parent.parent / "prompts" / "pm_planner.txt"
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                planner_prompt_template = f.read()
        except FileNotFoundError:
            planner_prompt_template = self._get_default_planner_prompt()
        
        prompt = f"{planner_prompt_template}\n\n## Task to Plan\n\nAgent Name: {project_meta.agent_name}\nDescription: {project_meta.description}\nTask Type: {project_meta.task_type}\nHas RAG: {project_meta.has_rag}\nUser Intent: {project_meta.user_intent_summary}\n\nGenerate execution plan as JSON: {{\"complexity_score\": int, \"execution_plan\": [...]}}"  
        
        try:
            response = await self.builder.call(prompt=prompt)
            
            # Parse JSON response
            result = self._extract_json(response)
            
            plan_data = result.get("execution_plan", [])
            
            # Convert to ExecutionStep objects
            execution_plan = [
                ExecutionStep(
                    step=item["step"],
                    role=item["role"],
                    goal=item["goal"],
                    expected_output=item.get("expected_output")
                )
                for item in plan_data
            ]
            
            return execution_plan
            
        except Exception as e:
            print(f"Warning: Planner failed, using heuristic: {e}")
            # Fallback: simple plan
            return self._heuristic_plan(project_meta)
    
    async def estimate_complexity(
        self,
        user_query: str,
        has_files: bool = False
    ) -> int:
        """Estimate task complexity (1-10).
        
        Args:
            user_query: User's requirement
            has_files: Whether files are provided
            
        Returns:
            Complexity score (1-10)
        """
        # Simple heuristic-based estimation
        score = 1
        
        # Check for complexity indicators
        query_lower = user_query.lower()
        
        # Multiple functions/features
        if any(word in query_lower for word in ['和', 'and', '以及', '还要', '同时']):
            score += 2
        
        # Iteration/refinement
        if any(word in query_lower for word in ['迭代', '改进', '优化', 'improve', 'refine', 'iterate']):
            score += 2
        
        # Multiple tools
        if any(word in query_lower for word in ['搜索', 'search', '计算', 'calculate', '分析', 'analyze']):
            score += 1
        
        # Complex logic
        if any(word in query_lower for word in ['如果', 'if', '判断', '条件', 'condition']):
            score += 1
        
        # Files/RAG
        if has_files or any(word in query_lower for word in ['文档', 'document', '知识库']):
            score += 2
        
        # Long description
        if len(user_query) > 200:
            score += 1
        
        return min(score, 10)  # Cap at 10
    
    async def analyze_with_clarification_loop(
        self,
        user_query: str,
        chat_history: Optional[List[Dict]] = None,
        file_paths: Optional[List[Path]] = None
    ) -> ProjectMeta:
        """Complete dual-brain mode analysis.
        
        This is the main entry point for PM dual-brain mode.
        
        Args:
            user_query: User's requirement
            chat_history: Conversation history
            file_paths: Optional file paths
            
        Returns:
            ProjectMeta with status="ready" or "clarifying"
        """
        # Step 1: Clarifier checks completeness
        is_ready, questions = await self.clarify_requirements(user_query, chat_history)
        
        if not is_ready:
            # Need clarification
            return ProjectMeta(
                agent_name="pending",
                description=user_query[:200],
                user_intent_summary=user_query[:100],
                status="clarifying",
                clarification_needed=True,
                clarification_questions=questions,
                has_rag=bool(file_paths),
                file_paths=[str(p) for p in file_paths] if file_paths else None
            )
        
        # Step 2: Requirements are clear, proceed with analysis
        project_meta = await self.analyze_requirements(user_query, file_paths)
        
        # Step 3: Estimate complexity
        complexity = await self.estimate_complexity(user_query, bool(file_paths))
        project_meta.complexity_score = complexity
        
        # Step 4: Generate execution plan if complex enough
        if complexity >= 4:
            execution_plan = await self.create_execution_plan(project_meta)
            project_meta.execution_plan = execution_plan
        
        # Mark as ready
        project_meta.status = "ready"
        
        return project_meta
    
    # ==================== Helper Methods ====================
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        # Try to find JSON block
        json_match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try to find raw JSON
        json_match = re.search(r'{.*}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        raise ValueError("No JSON found in response")
    
    def _heuristic_clarify(self, user_query: str) -> Tuple[bool, Optional[List[str]]]:
        """Heuristic-based clarification check."""
        query_lower = user_query.lower()
        
        # Very short query likely needs clarification (less than 15 chars)
        if len(user_query) < 15:
            return (False, [
                "请详细描述你想要的功能是什么？",
                "这个Agent主要用于什么场景？"
            ])
        
        # Check for extremely vague terms with very short description
        vague_terms = ['帮我', '写个', '做个', 'help me', 'create a', 'make a']
        if any(term in query_lower for term in vague_terms) and len(user_query) < 30:
            return (False, [
                "请具体说明需要什么功能？",
                "输入和输出分别是什么？"
            ])
        
        # If query is reasonably long and descriptive, assume it's clear
        return (True, None)
    
    def _heuristic_plan(self, project_meta: ProjectMeta) -> List[ExecutionStep]:
        """Heuristic-based execution plan."""
        plan = []
        
        if project_meta.has_rag:
            plan.append(ExecutionStep(
                step=1,
                role="Architect",
                goal="设计RAG系统架构",
                expected_output="RAG流程图"
            ))
            plan.append(ExecutionStep(
                step=2,
                role="Coder",
                goal="实现文档加载和检索逻辑",
                expected_output="RAG核心代码"
            ))
        else:
            plan.append(ExecutionStep(
                step=1,
                role="Coder",
                goal="实现Agent核心功能",
                expected_output="可执行代码"
            ))
        
        plan.append(ExecutionStep(
            step=len(plan) + 1,
            role="Tester",
            goal="测试功能正确性",
            expected_output="测试报告"
        ))
        
        return plan
    
    def _get_default_clarifier_prompt(self) -> str:
        """Default clarifier prompt if file not found."""
        return """You are a PM Clarifier. Evaluate if the user's requirement is clear enough.
        Score completeness 0-100%. If < 80%, generate 2-3 clarification questions.
        IMPORTANT: DO NOT ask about technology stack (LangGraph is fixed). Focus on BUSINESS LOGIC.
        Output JSON: {"is_ready": bool, "completeness_score": int, "clarification_questions": [...]}"""
    
    def _get_default_planner_prompt(self) -> str:
        """Default planner prompt if file not found."""
        return """You are a PM Planner. Break down the task into execution steps.
Assign roles (Architect/Coder/Tester/etc) and define goals.
Output JSON: {"complexity_score": int, "execution_plan": [{"step": int, "role": str, "goal": str}...]}"""

