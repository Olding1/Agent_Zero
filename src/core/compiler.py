"""Compiler module for generating agent code from JSON configurations."""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template
from pydantic import BaseModel, Field

from ..schemas import GraphStructure, RAGConfig, ToolsConfig, ProjectMeta
from ..utils.config_utils import atomic_write_json



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
        
        # 🆕 Add custom filter for sanitizing collection names
        def sanitize_collection_name(name: str) -> str:
            """Replace non-ASCII and special characters with underscores"""
            import re
            return re.sub(r'[^a-zA-Z0-9._-]', '_', name)
        
        self.env.filters['sanitize_collection_name'] = sanitize_collection_name

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
                # New Phase 3 fields
                "pattern": graph.pattern,
                "state_schema": graph.state_schema,
                # Graph structure
                "nodes": graph.nodes,
                "edges": graph.edges,
                "conditional_edges": graph.conditional_edges,
                "entry_point": graph.entry_point,
                # Tools and config
                "enabled_tools": tools_config.enabled_tools,
                "agent_type": project_meta.task_type,
                "language": project_meta.language,
                "custom_instructions": project_meta.description,
                "file_paths": project_meta.file_paths or [],
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
                rag_config=rag_config,
                file_paths=project_meta.file_paths,
            )
            requirements_file = output_dir / "requirements.txt"
            requirements_file.write_text(requirements, encoding="utf-8")
            generated_files.append("requirements.txt")

            # Generate .env.template
            env_template = self._generate_env_template()
            env_file = output_dir / ".env.template"
            env_file.write_text(env_template, encoding="utf-8")
            generated_files.append(".env.template")

            # 🆕 Generate real .env with current config (Auto-configuration)
            env_content = self._generate_env_file_content()
            real_env_file = output_dir / ".env"
            real_env_file.write_text(env_content, encoding="utf-8")
            generated_files.append(".env")
            
            # 🆕 Phase 4: 生成 pip.conf (优化 2 - 预安装)
            pip_config = self._generate_pip_config()
            pip_config_file = output_dir / "pip.conf"
            pip_config_file.write_text(pip_config, encoding="utf-8")
            generated_files.append("pip.conf")
            
            # 🆕 Phase 4: 生成安装脚本
            install_sh = self._generate_install_script_sh()
            install_sh_file = output_dir / "install.sh"
            install_sh_file.write_text(install_sh, encoding="utf-8")
            # 设置可执行权限 (Unix/Linux/Mac)
            try:
                import os
                os.chmod(install_sh_file, 0o755)
            except Exception:
                pass  # Windows 不需要
            generated_files.append("install.sh")
            
            install_bat = self._generate_install_script_bat()
            install_bat_file = output_dir / "install.bat"
            install_bat_file.write_text(install_bat, encoding="utf-8")
            generated_files.append("install.bat")

            # Save graph.json for UI visualization
            graph_file = output_dir / "graph.json"
            graph_file.write_text(graph.model_dump_json(indent=2), encoding="utf-8")
            generated_files.append("graph.json")
            
            # 🆕 Save rag_config.json if RAG is enabled
            if rag_config:
                atomic_write_json(output_dir / "rag_config.json", rag_config.model_dump())
                generated_files.append("rag_config.json")
            
            # 🆕 Save tools_config.json if tools are enabled
            if tools_config and len(tools_config.enabled_tools) > 0:
                atomic_write_json(output_dir / "tools_config.json", tools_config.model_dump())
                generated_files.append("tools_config.json")

            return CompileResult(
                success=True, output_dir=output_dir, generated_files=generated_files
            )

        except Exception as e:
            return CompileResult(
                success=False,
                output_dir=output_dir,
                error_message=f"Compilation failed: {str(e)}",
            )

    def _generate_requirements(
        self, 
        has_rag: bool, 
        has_tools: bool,
        rag_config: Optional[RAGConfig] = None,
        file_paths: Optional[list] = None,
        include_testing: bool = True,  # 🆕 Phase 4: 添加测试依赖开关
    ) -> str:
        """Generate requirements.txt content based on features.
        
        Args:
            has_rag: Whether RAG is enabled
            has_tools: Whether tools are enabled
            rag_config: RAG configuration (optional)
            file_paths: List of file paths for document loading
            include_testing: Whether to include DeepEval testing dependencies
            
        Returns:
            Requirements.txt content as string
        """
        requirements = [
            "# Core dependencies",
            "langchain>=0.2.0",
            "langgraph>=0.2.28",
            "langchain-openai>=0.1.0",
            "python-dotenv>=1.0.0",
            "pyyaml>=6.0.1",
        ]

        if has_rag and rag_config:
            requirements.extend(
                [
                    "",
                    "# RAG dependencies",
                    "langchain-community>=0.2.0",
                    "tiktoken>=0.5.0",  # Token counting
                ]
            )
            
            # Vector store dependencies
            if rag_config.vector_store == "chroma":
                requirements.append("chromadb>=0.4.22")
            elif rag_config.vector_store == "faiss":
                requirements.append("faiss-cpu>=1.7.4")
            elif rag_config.vector_store == "pgvector":
                requirements.append("pgvector>=0.2.0")
                requirements.append("psycopg2-binary>=2.9.0")
            
            
            # Embedding model dependencies
            # Include all providers since we support runtime switching via env vars
            requirements.append("langchain-openai>=0.1.0")  # For OpenAI embeddings
            requirements.append("langchain-ollama>=0.1.0")  # For Ollama embeddings
            # HuggingFace is optional, only add if explicitly configured
            if rag_config.embedding_provider == "huggingface":
                requirements.append("sentence-transformers>=2.2.0")
            
            # Document loader dependencies (based on file types)
            if file_paths and len(file_paths) > 0:
                has_pdf = any(str(f).lower().endswith('.pdf') for f in file_paths)
                has_docx = any(str(f).lower().endswith(('.docx', '.doc')) for f in file_paths)
                has_md = any(str(f).lower().endswith('.md') for f in file_paths)
                
                if has_pdf:
                    requirements.append("pypdf>=3.17.0")
                if has_docx:
                    requirements.append("python-docx>=1.1.0")
                if has_md:
                    requirements.append("unstructured>=0.12.0")
                    requirements.append("markdown>=3.5.0")  # Required by unstructured for markdown
            else:
                # Add all loaders if no file paths specified
                requirements.extend([
                    "pypdf>=3.17.0",
                    "python-docx>=1.1.0",
                    "markdown>=3.5.0",  # Required by unstructured for markdown
                ])
            
            # [v7.2 Update] Default Dependencies for Evolution Capability
            # Always install these so the Optimizer can switch to them at runtime
            requirements.append("rank-bm25>=0.2.2")
            requirements.append("flashrank>=0.2.0")

            # Hybrid search dependencies (Legacy check for jieba)
            if hasattr(rag_config, 'language') and 'zh' in str(rag_config.language).lower():
                requirements.append("jieba>=0.42.1")
            
            # Additional Reranker dependencies (if specific provider selected)
            if rag_config.reranker_enabled and rag_config.reranker_provider:
                if rag_config.reranker_provider == "cohere":
                    requirements.append("cohere>=4.0.0")
                elif rag_config.reranker_provider == "bge":
                    requirements.append("sentence-transformers>=2.2.0")

        if has_tools:
            requirements.extend(
                [
                    "",
                    "# Tool dependencies",
                    "langchain-community>=0.2.0",
                ]
            )
        
        # 🆕 Phase 4: DeepEval 测试依赖 (优化 2 - 预安装)
        if include_testing:
            requirements.extend(
                [
                    "",
                    "# Testing dependencies (Phase 4 - DeepEval)",
                    "deepeval>=0.21.0",
                    "pytest>=7.4.0",
                    "pytest-json-report>=1.5.0",
                ]
            )

        return "\n".join(requirements)

    def _generate_env_template(self) -> str:
        """Generate .env.template content.
        
        Returns:
            Environment template content as string
        """
        return """# Agent Zero - Generated Agent Configuration
# ==========================================

# Runtime API Configuration (用于生成的 Agent 运行时)
RUNTIME_PROVIDER=openai
RUNTIME_MODEL=deepseek-chat
RUNTIME_API_KEY=your_api_key_here
RUNTIME_BASE_URL=https://api.deepseek.com
RUNTIME_TIMEOUT=30
RUNTIME_TEMPERATURE=0.7

# Embedding Configuration (用于 RAG 向量化)
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL_NAME=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
# EMBEDDING_API_KEY 不需要（Ollama 本地运行）

# Judge API Configuration (用于 DeepEval 测试评估)
# 如果未配置,DeepEval 将使用 Runtime API
JUDGE_PROVIDER=openai
JUDGE_MODEL=deepseek-chat
JUDGE_API_KEY=your_api_key_here
JUDGE_BASE_URL=https://api.deepseek.com
JUDGE_TIMEOUT=60
JUDGE_TEMPERATURE=0.0
"""

    def _generate_env_file_content(self) -> str:
        """Generate .env content populated with current system configuration.
        
        Returns:
            Populated .env content as string
        """
        import os
        from datetime import datetime
        
        # Helper to get env with default (fallback to sensible defaults if env not set)
        def get_val(key, default):
            return os.getenv(key, default)

        return f"""# Agent Zero - Auto-generated Configuration
# Generated from system configuration on {datetime.now().isoformat()}
# This file is auto-populated with your current environment settings.

# Runtime API Configuration
RUNTIME_PROVIDER={get_val("RUNTIME_PROVIDER", "openai")}
RUNTIME_MODEL={get_val("RUNTIME_MODEL", "deepseek-chat")}
RUNTIME_API_KEY={get_val("RUNTIME_API_KEY", "")}
RUNTIME_BASE_URL={get_val("RUNTIME_BASE_URL", "https://api.deepseek.com")}
RUNTIME_TIMEOUT={get_val("RUNTIME_TIMEOUT", "30")}
RUNTIME_TEMPERATURE={get_val("RUNTIME_TEMPERATURE", "0.7")}

# Embedding Configuration
EMBEDDING_PROVIDER={get_val("EMBEDDING_PROVIDER", "ollama")}
EMBEDDING_MODEL_NAME={get_val("EMBEDDING_MODEL_NAME", get_val("EMBEDDING_MODEL", "nomic-embed-text"))}
EMBEDDING_BASE_URL={get_val("EMBEDDING_BASE_URL", "http://localhost:11434")}
EMBEDDING_API_KEY={get_val("EMBEDDING_API_KEY", "")}

# Judge API Configuration (用于 DeepEval 测试评估)
# 如果未配置,DeepEval 将使用 Runtime API
JUDGE_PROVIDER={get_val("JUDGE_PROVIDER", get_val("RUNTIME_PROVIDER", "openai"))}
JUDGE_MODEL={get_val("JUDGE_MODEL", get_val("RUNTIME_MODEL", "deepseek-chat"))}
JUDGE_API_KEY={get_val("JUDGE_API_KEY", get_val("RUNTIME_API_KEY", ""))}
JUDGE_BASE_URL={get_val("JUDGE_BASE_URL", get_val("RUNTIME_BASE_URL", "https://api.deepseek.com"))}
JUDGE_TIMEOUT={get_val("JUDGE_TIMEOUT", "60")}
JUDGE_TEMPERATURE={get_val("JUDGE_TEMPERATURE", "0.0")}
"""
    
    def _generate_pip_config(self) -> str:
        """🆕 Phase 4: 生成 pip.conf (使用国内镜像源)
        
        Returns:
            pip.conf content as string
        """
        return """[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
"""
    
    def _generate_install_script_sh(self) -> str:
        """🆕 Phase 4: 生成 Linux/Mac 安装脚本
        
        Returns:
            install.sh content as string
        """
        return """#!/bin/bash
# Agent Zero - 依赖安装脚本 (Linux/Mac)

echo "=========================================="
echo "Agent Zero - 依赖安装"
echo "=========================================="
echo ""
echo "使用清华大学镜像源加速下载..."
echo ""

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 🆕 自动创建虚拟环境 (非交互模式)
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 虚拟环境创建失败"
        exit 1
    fi
    echo "✅ 虚拟环境已创建"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ 虚拟环境激活失败"
    exit 1
fi

# 安装依赖
echo ""
echo "开始安装依赖..."
python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
python3 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 检查安装结果
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 依赖安装完成!"
    echo "=========================================="
    echo ""
    echo "下一步:"
    echo "1. 配置 .env 文件 (参考 .env.template)"
    echo "2. 运行 Agent: python agent.py"
    echo "3. 运行测试: pytest tests/test_deepeval.py"
else
    echo ""
    echo "❌ 依赖安装失败,请检查错误信息"
    exit 1
fi
"""
    
    def _generate_install_script_bat(self) -> str:
        """🆕 Phase 4: 生成 Windows 安装脚本
        
        Returns:
            install.bat content as string
        """
        return """@echo off
REM Agent Zero - 依赖安装脚本 (Windows)

echo ==========================================
echo Agent Zero - 依赖安装
echo ==========================================
echo.
echo 使用清华大学镜像源加速下载...
echo.

REM 检查 Python 版本
python --version
if errorlevel 1 (
    echo ❌ 未找到 Python,请先安装 Python 3.11+
    pause
    exit /b 1
)

REM 🆕 自动创建虚拟环境 (非交互模式)
if not exist venv (
    echo 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境已创建
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\\Scripts\\activate.bat
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b 1
)

REM 安装依赖
echo.
echo 开始安装依赖...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

REM 检查安装结果
if errorlevel 1 (
    echo.
    echo ❌ 依赖安装失败,请检查错误信息
    pause
    exit /b 1
)

echo.
echo ==========================================
echo ✅ 依赖安装完成!
echo ==========================================
echo.
echo 下一步:
echo 1. 配置 .env 文件 (参考 .env.template)
echo 2. 运行 Agent: python agent.py
echo 3. 运行测试: pytest tests\\test_deepeval.py
echo.
pause
"""
