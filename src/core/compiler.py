"""Compiler module for generating agent code from JSON configurations."""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template
from pydantic import BaseModel, Field

from ..schemas import GraphStructure, RAGConfig, ToolsConfig, ProjectMeta


class CompileResult(BaseModel):
    """Result of compilation process."""

    success: bool = Field(..., description="Whether compilation succeeded")
    output_dir: Path = Field(..., description="Output directory path")
    generated_files: list[str] = Field(
        default_factory=list, description="List of generated files"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if compilation failed"
    )


class Compiler:
    """Compiler for generating agent code from JSON configurations.
    
    Transforms JSON intermediate representation into executable Python code
    using Jinja2 templates.
    """

    def __init__(self, template_dir: Path):
        """Initialize compiler with template directory.
        
        Args:
            template_dir: Path to directory containing Jinja2 templates
        """
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def compile(
        self,
        project_meta: ProjectMeta,
        graph: GraphStructure,
        rag_config: Optional[RAGConfig],
        tools_config: ToolsConfig,
        output_dir: Path,
    ) -> CompileResult:
        """Compile JSON configurations into executable agent code.
        
        Args:
            project_meta: Project metadata
            graph: Graph structure definition
            rag_config: RAG configuration (optional)
            tools_config: Tools configuration
            output_dir: Output directory for generated files
            
        Returns:
            CompileResult with success status and generated files
        """
        try:
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            generated_files = []

            # Prepare template context
            context = {
                "timestamp": datetime.now().isoformat(),
                "agent_name": project_meta.agent_name,
                "description": project_meta.description,
                "has_rag": project_meta.has_rag,
                "has_tools": len(tools_config.enabled_tools) > 0,
                "nodes": graph.nodes,
                "edges": graph.edges,
                "conditional_edges": graph.conditional_edges,
                "entry_point": graph.entry_point,
                "enabled_tools": tools_config.enabled_tools,
                "agent_type": project_meta.task_type.value,
                "language": project_meta.language,
                "custom_instructions": project_meta.description,
            }

            # Add RAG config if present
            if rag_config:
                context["rag_config"] = rag_config

            # Generate agent.py
            agent_template = self.env.get_template("agent_template.py.j2")
            agent_code = agent_template.render(**context)
            
            # Format code with black (if available)
            try:
                import black
                agent_code = black.format_str(agent_code, mode=black.Mode())
            except ImportError:
                pass  # Black not available, skip formatting

            agent_file = output_dir / "agent.py"
            agent_file.write_text(agent_code, encoding="utf-8")
            generated_files.append("agent.py")

            # Generate prompts.yaml
            prompts_template = self.env.get_template("prompts_template.yaml.j2")
            prompts_content = prompts_template.render(**context)
            prompts_file = output_dir / "prompts.yaml"
            prompts_file.write_text(prompts_content, encoding="utf-8")
            generated_files.append("prompts.yaml")

            # Generate requirements.txt
            requirements = self._generate_requirements(
                has_rag=project_meta.has_rag,
                has_tools=len(tools_config.enabled_tools) > 0,
            )
            requirements_file = output_dir / "requirements.txt"
            requirements_file.write_text(requirements, encoding="utf-8")
            generated_files.append("requirements.txt")

            # Generate .env.template
            env_template = self._generate_env_template()
            env_file = output_dir / ".env.template"
            env_file.write_text(env_template, encoding="utf-8")
            generated_files.append(".env.template")

            # Save graph.json for UI visualization
            graph_file = output_dir / "graph.json"
            graph_file.write_text(graph.model_dump_json(indent=2), encoding="utf-8")
            generated_files.append("graph.json")

            return CompileResult(
                success=True, output_dir=output_dir, generated_files=generated_files
            )

        except Exception as e:
            return CompileResult(
                success=False,
                output_dir=output_dir,
                error_message=f"Compilation failed: {str(e)}",
            )

    def _generate_requirements(self, has_rag: bool, has_tools: bool) -> str:
        """Generate requirements.txt content based on features.
        
        Args:
            has_rag: Whether RAG is enabled
            has_tools: Whether tools are enabled
            
        Returns:
            Requirements.txt content as string
        """
        requirements = [
            "# Core dependencies",
            "langchain>=0.2.0",
            "langgraph>=0.2.0",
            "langchain-openai>=0.1.0",
            "python-dotenv>=1.0.0",
            "pyyaml>=6.0.1",
        ]

        if has_rag:
            requirements.extend(
                [
                    "",
                    "# RAG dependencies",
                    "chromadb>=0.4.22",
                    "langchain-community>=0.2.0",
                ]
            )

        if has_tools:
            requirements.extend(
                [
                    "",
                    "# Tool dependencies",
                    "langchain-community>=0.2.0",
                ]
            )

        return "\n".join(requirements)

    def _generate_env_template(self) -> str:
        """Generate .env.template content.
        
        Returns:
            Environment template content as string
        """
        return """# Runtime API Configuration
RUNTIME_API_KEY=your-api-key-here
RUNTIME_BASE_URL=https://api.openai.com/v1
RUNTIME_MODEL=gpt-3.5-turbo
TEMPERATURE=0.7

# Optional: Custom configurations
# MAX_TOKENS=2000
# TIMEOUT=60
"""
