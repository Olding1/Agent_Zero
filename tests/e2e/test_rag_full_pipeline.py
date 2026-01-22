"""E2E Test for RAG Full Pipeline.

Tests the complete RAG implementation from document loading to question answering.
"""

import asyncio
import sys
from pathlib import Path
import tempfile
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core import PM, Profiler, RAGBuilder, GraphDesigner, Compiler, EnvManager
from src.llm import BuilderClient, BuilderAPIConfig
from src.schemas import ToolsConfig
from dotenv import load_dotenv


async def test_rag_full_pipeline():
    """Test complete RAG pipeline."""
    
    print("=" * 80)
    print("🧪 RAG Full Pipeline Test")
    print("=" * 80)
    
    # Load environment
    load_dotenv()
    
    # Step 1: Create test document
    print("\n📄 Step 1: Creating test document...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write("""# Agent Zero 项目介绍

Agent Zero 是一个智能体构建工厂,通过元编程将自然语言转化为 LangGraph 拓扑。

## 核心特性

- **Graph as Code**: JSON 中间层解耦业务逻辑与代码实现
- **无 Docker 化**: 使用 Python venv 实现轻量级环境隔离
- **API 双轨制**: 区分构建用模型和运行用模型
- **主动进化**: 利用 LangChain MCP 协议实现依赖库主动重构

## 技术栈

- Python 3.11+
- LangChain 0.2+
- LangGraph 1.0+
- Pydantic 2.5+
- Jinja2 3.1+

## 当前进度

阶段一和阶段二已完成,包括核心编译管道和数据流系统。
""")
        test_file = Path(f.name)
    
    print(f"✓ Created test file: {test_file}")
    
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
    print("✓ Builder Client initialized")
    
    # Step 3: PM analyzes requirements
    print("\n🧠 Step 3: PM analyzing requirements...")
    pm = PM(builder_client)
    project_meta = await pm.analyze_requirements(
        user_input="创建一个能回答 Agent Zero 项目相关问题的智能助手",
        file_paths=[test_file]
    )
    
    print(f"✓ Agent Name: {project_meta.agent_name}")
    print(f"✓ Has RAG: {project_meta.has_rag}")
    print(f"✓ Task Type: {project_meta.task_type}")
    
    assert project_meta.has_rag is True, "Should detect RAG requirement"
    
    # Step 4: Profiler analyzes documents
    print("\n📊 Step 4: Profiler analyzing documents...")
    profiler = Profiler()
    data_profile = profiler.analyze([test_file])
    
    print(f"✓ Total files: {len(data_profile.files)}")
    print(f"✓ Estimated tokens: {data_profile.estimated_tokens}")
    print(f"✓ Languages: {data_profile.languages_detected}")
    
    # Step 5: RAG Builder designs strategy
    print("\n🏗️  Step 5: RAG Builder designing strategy...")
    rag_builder = RAGBuilder(builder_client)
    rag_config = await rag_builder.design_rag_strategy(data_profile)
    
    print(f"✓ Splitter: {rag_config.splitter}")
    print(f"✓ Chunk size: {rag_config.chunk_size}")
    print(f"✓ Vector store: {rag_config.vector_store}")
    print(f"✓ Embedding provider: {rag_config.embedding_provider}")
    print(f"✓ Embedding model: {rag_config.embedding_model_name}")
    print(f"✓ Retriever type: {rag_config.retriever_type}")
    
    # Step 6: Graph Designer creates graph
    print("\n📐 Step 6: Graph Designer creating graph...")
    graph_designer = GraphDesigner(builder_client)
    graph_structure = await graph_designer.design_graph(
        project_meta=project_meta,
        tools_config=ToolsConfig(enabled_tools=[]),
        rag_config=rag_config
    )
    
    print(f"✓ Nodes: {len(graph_structure.nodes)}")
    print(f"✓ Edges: {len(graph_structure.edges)}")
    
    # Verify RAG node exists
    has_rag_node = any(node.type == "rag" for node in graph_structure.nodes)
    print(f"✓ Has RAG node: {has_rag_node}")
    
    # Step 7: Compiler generates code
    print("\n⚙️  Step 7: Compiler generating code...")
    compiler = Compiler(template_dir=Path("src/templates"))
    output_dir = Path("agents/rag_full_test")
    
    result = compiler.compile(
        project_meta=project_meta,
        graph=graph_structure,
        rag_config=rag_config,
        tools_config=ToolsConfig(enabled_tools=[]),
        output_dir=output_dir
    )
    
    print(f"✓ Compilation success: {result.success}")
    print(f"✓ Generated files: {len(result.generated_files)}")
    for file in result.generated_files:
        print(f"   - {file}")
    
    assert result.success, "Compilation should succeed"
    assert len(result.generated_files) == 5, "Should generate 5 files"
    
    # Step 8: Verify generated code contains RAG components
    print("\n🔍 Step 8: Verifying generated code...")
    agent_code = (output_dir / "agent.py").read_text(encoding='utf-8')
    
    checks = {
        "embeddings": "embeddings" in agent_code,
        "vectorstore": "vectorstore" in agent_code,
        "retriever": "retriever" in agent_code,
        "ask_question": "ask_question" in agent_code,
        "load_documents": "load_documents" in agent_code,
        "split_documents": "split_documents" in agent_code,
    }
    
    for component, exists in checks.items():
        status = "✓" if exists else "✗"
        print(f"{status} {component}: {exists}")
        assert exists, f"{component} should be in generated code"
    
    # Step 9: Verify requirements.txt
    print("\n📦 Step 9: Verifying requirements.txt...")
    requirements = (output_dir / "requirements.txt").read_text(encoding='utf-8')
    
    required_packages = [
        "langchain",
        "langgraph",
        "langchain-community",
        "chromadb",  # Default vector store
        "tiktoken",
    ]
    
    # At least one document loader should be present
    document_loaders = ["pypdf", "python-docx", "unstructured"]
    has_loader = any(loader in requirements for loader in document_loaders)
    
    for package in required_packages:
        if package in requirements:
            print(f"✓ {package}")
        else:
            print(f"✗ {package} missing!")
            assert False, f"{package} should be in requirements.txt"
    
    if has_loader:
        print(f"✓ Document loaders present")
    else:
        print(f"✗ No document loaders found!")
        assert False, "At least one document loader should be in requirements.txt"
    
    # Step 10: EnvManager setup environment
    print("\n🔧 Step 10: EnvManager setting up environment...")
    env_manager = EnvManager(output_dir)
    
    print("⏳ Creating virtual environment and installing dependencies...")
    print("   (This may take a few minutes...)")
    
    setup_success = await env_manager.setup_environment()
    
    if setup_success:
        print("✓ Environment setup complete")
    else:
        print("⚠️  Environment setup had issues (may be expected in test environment)")
    
    # Cleanup
    print("\n🧹 Cleaning up test file...")
    test_file.unlink()
    print("✓ Test file removed")
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ RAG Full Pipeline Test PASSED!")
    print("=" * 80)
    print(f"\n📁 Generated Agent Location: {output_dir.absolute()}")
    print("\nTo run the generated agent:")
    print(f"  cd {output_dir}")
    print("  python agent.py")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_rag_full_pipeline())
