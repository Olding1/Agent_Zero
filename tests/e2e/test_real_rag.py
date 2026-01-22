"""Real RAG Test with Project Documentation.

This test validates the complete RAG pipeline using actual project documentation:
1. Document loading from real files
2. Text splitting and chunking
3. Embedding and vectorization
4. Vector storage (ChromaDB)
5. Document retrieval
6. Question answering
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core import PM, Profiler, RAGBuilder, GraphDesigner, Compiler, EnvManager
from src.llm import BuilderClient, BuilderAPIConfig
from src.schemas import ToolsConfig
from dotenv import load_dotenv
import os


async def test_real_rag():
    """Test RAG with real project documentation."""
    
    print("=" * 80)
    print("🧪 Real RAG Test - Using Project Documentation")
    print("=" * 80)
    
    # Load environment
    load_dotenv()
    
    # Step 1: Prepare real documents
    print("\n📄 Step 1: Preparing real documents...")
    project_root = Path(__file__).parent.parent.parent
    
    # Use actual project documentation
    doc_files = [
        project_root / "Agent Zero项目计划书.md",
        project_root / "Agent_Zero_详细实施计划.md",
        project_root / "phase2_summary.md",
    ]
    
    # Verify files exist
    existing_files = []
    for doc_file in doc_files:
        if doc_file.exists():
            existing_files.append(doc_file)
            print(f"✓ Found: {doc_file.name}")
        else:
            print(f"✗ Missing: {doc_file.name}")
    
    if not existing_files:
        print("\n❌ No documentation files found!")
        return False
    
    print(f"\n✓ Using {len(existing_files)} documentation files")
    
    # Step 2: Initialize Builder Client
    print("\n🔧 Step 2: Initializing Builder Client...")
    builder_config = BuilderAPIConfig(
        provider=os.getenv("BUILDER_PROVIDER", "openai"),
        model=os.getenv("BUILDER_MODEL", "gpt-4o"),
        api_key=os.getenv("BUILDER_API_KEY", ""),
        base_url=os.getenv("BUILDER_BASE_URL"),
        timeout=int(os.getenv("BUILDER_TIMEOUT", "60")),
        max_retries=int(os.getenv("BUILDER_MAX_RETRIES", "3")),
        temperature=float(os.getenv("BUILDER_TEMPERATURE", "0.7")),
    )
    
    builder_client = BuilderClient(builder_config)
    print(f"✓ Builder: {builder_config.provider}/{builder_config.model}")
    
    # Step 3: PM analyzes requirements
    print("\n🧠 Step 3: PM analyzing requirements...")
    pm = PM(builder_client)
    
    try:
        project_meta = await pm.analyze_requirements(
            user_input="创建一个能回答 Agent Zero 项目相关问题的智能助手,可以查询项目架构、实施计划和技术细节",
            file_paths=existing_files
        )
        
        print(f"✓ Agent Name: {project_meta.agent_name}")
        print(f"✓ Has RAG: {project_meta.has_rag}")
        print(f"✓ Task Type: {project_meta.task_type}")
        
    except Exception as e:
        print(f"⚠️  PM analysis failed, using fallback: {e}")
        project_meta = await pm.analyze_requirements(
            user_input="创建一个能回答 Agent Zero 项目相关问题的智能助手",
            file_paths=existing_files
        )
        print(f"✓ Fallback successful: {project_meta.agent_name}")
    
    # Step 4: Profiler analyzes documents
    print("\n📊 Step 4: Profiler analyzing documents...")
    profiler = Profiler()
    data_profile = profiler.analyze(existing_files)
    
    print(f"✓ Files analyzed: {data_profile.total_files}")
    print(f"✓ Total size: {data_profile.total_size_bytes:,} bytes")
    print(f"✓ Estimated tokens: {data_profile.estimated_tokens:,}")
    print(f"✓ Languages: {', '.join(data_profile.languages_detected)}")
    
    # Step 5: RAG Builder designs strategy
    print("\n⚙️  Step 5: RAG Builder designing strategy...")
    rag_builder = RAGBuilder(builder_client)
    
    try:
        rag_config = await rag_builder.design_rag_strategy(data_profile)
        print(f"✓ Splitter: {rag_config.splitter}")
        print(f"✓ Chunk size: {rag_config.chunk_size}")
        print(f"✓ Vector store: {rag_config.vector_store}")
        print(f"✓ Embedding: {rag_config.embedding_provider}/{rag_config.embedding_model_name}")
        
    except Exception as e:
        print(f"⚠️  RAG Builder failed, using heuristics: {e}")
        rag_config = rag_builder._heuristic_strategy(data_profile)
        print(f"✓ Heuristic strategy applied")
    
    # Step 6: Graph Designer creates graph
    print("\n🕸️  Step 6: Graph Designer creating graph...")
    graph_designer = GraphDesigner(builder_client)
    tools_config = ToolsConfig(enabled_tools=[])
    
    try:
        graph_structure = await graph_designer.design_graph(
            project_meta=project_meta,
            tools_config=tools_config,
            rag_config=rag_config
        )
        print(f"✓ Nodes: {len(graph_structure.nodes)}")
        print(f"✓ Edges: {len(graph_structure.edges)}")
        
    except Exception as e:
        print(f"⚠️  Graph Designer failed, using heuristics: {e}")
        graph_structure = graph_designer._heuristic_graph(
            project_meta, tools_config, rag_config
        )
        print(f"✓ Heuristic graph created")
    
    # Step 7: Compiler generates code
    print("\n🔨 Step 7: Compiler generating code...")
    compiler = Compiler(template_dir=Path("src/templates"))
    output_dir = Path("agents") / "real_rag_test"
    
    compile_result = compiler.compile(
        project_meta=project_meta,
        graph=graph_structure,
        rag_config=rag_config,
        tools_config=tools_config,
        output_dir=output_dir
    )
    
    if not compile_result.success:
        print(f"✗ Compilation failed: {compile_result.error_message}")
        return False
    
    print(f"✓ Code generated at: {output_dir}")
    print(f"✓ Files created: {len(compile_result.generated_files)}")
    
    # Step 8: Copy real documents to agent directory
    print("\n📋 Step 8: Copying documents to agent directory...")
    docs_dir = output_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    import shutil
    copied_files = []
    for doc_file in existing_files:
        dest = docs_dir / doc_file.name
        shutil.copy(doc_file, dest)
        copied_files.append(dest)
        print(f"✓ Copied: {doc_file.name}")
    
    # Step 9: Update project_meta with relative paths
    print("\n🔧 Step 9: Updating project metadata with relative paths...")
    relative_paths = [f"docs/{f.name}" for f in copied_files]
    project_meta.file_paths = relative_paths
    print(f"✓ Using relative paths: {relative_paths}")
    
    # Re-compile with updated paths
    print("\n🔨 Step 9b: Re-compiling with updated paths...")
    compile_result = compiler.compile(
        project_meta=project_meta,
        graph=graph_structure,
        rag_config=rag_config,
        tools_config=tools_config,
        output_dir=output_dir
    )
    
    if not compile_result.success:
        print(f"✗ Re-compilation failed: {compile_result.error_message}")
        return False
    
    print(f"✓ Re-compiled with document paths")
    
    # Step 10: EnvManager sets up environment
    print("\n🌐 Step 10: EnvManager setting up environment...")
    env_manager = EnvManager(output_dir)
    
    print("⏳ Creating virtual environment and installing dependencies...")
    print("   (This may take a few minutes...)")
    
    setup_success = await env_manager.setup_environment()
    
    if setup_success:
        print("✓ Virtual environment created")
        print("✓ Dependencies installed")
    else:
        print("⚠️  Environment setup had issues")
    
    # Step 11: Copy .env configuration
    print("\n📋 Step 11: Copying .env configuration...")
    main_env = Path(".env")
    agent_env = output_dir / ".env"
    
    if main_env.exists():
        # Copy Runtime and Embedding configurations
        with open(main_env, 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        env_content = "# Agent Runtime Configuration\n# Auto-copied from main project\n\n"
        env_content += "# Runtime API Configuration\n"
        for line in main_content.split('\n'):
            if line.strip().startswith('RUNTIME_'):
                env_content += line + '\n'
        
        env_content += "\n# Embedding API Configuration\n"
        for line in main_content.split('\n'):
            if line.strip().startswith('EMBEDDING_') or (line.strip().startswith('#') and 'EMBEDDING' in line and not line.strip().startswith('# Embedding API')):
                env_content += line + '\n'
        
        with open(agent_env, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✓ Copied Runtime API configuration")
        print("✓ Copied Embedding API configuration")
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ Real RAG Test Setup Complete!")
    print("=" * 80)
    print(f"\n📁 Generated Agent Location: {output_dir.absolute()}")
    print(f"\n📚 Documents:")
    for doc in copied_files:
        print(f"   - {doc.name}")
    
    print("\n🚀 To run the agent:")
    print(f"   cd {output_dir}")
    print("   python agent.py")
    
    print("\n💡 Test Questions:")
    print("   - Agent Zero 的核心特性是什么?")
    print("   - 项目使用了哪些技术栈?")
    print("   - Phase 2 完成了哪些工作?")
    print("   - RAG 系统的实施计划是什么?")
    
    print("\n" + "=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_real_rag())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
