"""End-to-end test for Phase 1: Hello World Agent generation."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.schemas import (
    ProjectMeta,
    TaskType,
    GraphStructure,
    NodeDef,
    EdgeDef,
    ConditionalEdgeDef,
    ToolsConfig,
)
from src.core.compiler import Compiler
from src.core.env_manager import EnvManager


async def test_hello_world_agent():
    """Test complete flow: JSON -> Compile -> Venv -> Run."""
    
    print("=" * 60)
    print("Phase 1 E2E Test: Hello World Agent")
    print("=" * 60)
    
    # Step 1: Define project metadata
    print("\n[1/5] Creating project metadata...")
    project_meta = ProjectMeta(
        agent_name="HelloWorldBot",
        description="A simple greeting agent",
        has_rag=False,
        task_type=TaskType.CHAT,
        language="zh-CN",
        user_intent_summary="Create a simple chatbot that greets users",
    )
    print(f"✓ Project: {project_meta.agent_name}")
    
    # Step 2: Define graph structure
    print("\n[2/5] Defining graph structure...")
    graph = GraphStructure(
        nodes=[
            NodeDef(id="agent", type="llm"),
        ],
        edges=[],
        conditional_edges=[],
        entry_point="agent",
    )
    print(f"✓ Graph with {len(graph.nodes)} node(s)")
    
    # Step 3: Compile to code
    print("\n[3/5] Compiling to executable code...")
    template_dir = Path(__file__).parent.parent.parent / "src" / "templates"
    output_dir = Path(__file__).parent.parent.parent / "agents" / "hello_world_test"
    
    compiler = Compiler(template_dir=template_dir)
    result = compiler.compile(
        project_meta=project_meta,
        graph=graph,
        rag_config=None,
        tools_config=ToolsConfig(enabled_tools=[]),
        output_dir=output_dir,
    )
    
    if not result.success:
        print(f"✗ Compilation failed: {result.error_message}")
        return False
    
    print(f"✓ Generated files: {', '.join(result.generated_files)}")
    
    # Step 4: Setup virtual environment
    print("\n[4/5] Setting up virtual environment...")
    env_manager = EnvManager(agent_dir=output_dir)
    env_result = await env_manager.setup_environment()
    
    if not env_result.success:
        print(f"✗ Environment setup failed: {env_result.error_message}")
        return False
    
    print(f"✓ Virtual environment created at: {env_result.venv_path}")
    print(f"✓ Python executable: {env_result.python_executable}")
    
    # Step 5: Verify generated files
    print("\n[5/5] Verifying generated files...")
    expected_files = ["agent.py", "prompts.yaml", "requirements.txt", ".env.template", "graph.json"]
    
    for filename in expected_files:
        filepath = output_dir / filename
        if filepath.exists():
            print(f"✓ {filename} exists ({filepath.stat().st_size} bytes)")
        else:
            print(f"✗ {filename} missing")
            return False
    
    print("\n" + "=" * 60)
    print("✓ Phase 1 E2E Test PASSED!")
    print("=" * 60)
    print(f"\nGenerated agent location: {output_dir}")
    print("\nNext steps:")
    print("1. Copy .env.template to .env and configure API keys")
    print("2. Activate virtual environment:")
    print(f"   - Windows: {output_dir / '.venv' / 'Scripts' / 'activate'}")
    print(f"   - Linux/Mac: source {output_dir / '.venv' / 'bin' / 'activate'}")
    print("3. Run the agent:")
    print(f"   python {output_dir / 'agent.py'}")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_hello_world_agent())
    sys.exit(0 if success else 1)
