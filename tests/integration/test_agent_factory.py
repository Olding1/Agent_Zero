import pytest
import asyncio
from pathlib import Path
import shutil
from src.core.agent_factory import AgentFactory
from src.core.progress_callback import ProgressCallback
from src.schemas.graph_structure import GraphStructure
from src.schemas.simulation import SimulationResult

class MockCallback(ProgressCallback):
    def on_step_start(self, step_name, step_num, total_steps):
        print(f"\n[Test] Step Start: {step_name}")
        
    def on_step_complete(self, step_name, result):
        print(f"[Test] Step Complete: {step_name}")
        
    def on_step_error(self, step_name, error):
        print(f"[Test] Step Error: {step_name} - {error}")
        
    def on_clarification_needed(self, questions):
        pass
        
    def on_blueprint_review(self, graph, result) -> tuple[bool, str]:
        print("[Test] Auto-approving blueprint")
        return True, "" # Auto approve
        
    def on_log(self, message):
        pass

@pytest.mark.asyncio
async def test_factory_create_agent():
    # Setup
    output_dir = Path("./agents/test_factory_agent")
    if output_dir.exists():
        shutil.rmtree(output_dir)
        
    callback = MockCallback()
    factory = AgentFactory(callback=callback)
    
    # Enable interaction to test the callback
    factory.config.interactive = True 
    
    # Run
    print("\nStarting AgentFactory Test...")
    result = await factory.create_agent(
        user_input="Create a simple agent that can calculate 1+1. It should include a python tool.",
        output_dir=output_dir
    )
    
    # Verify
    print(f"\nResult Success: {result.success}")
    if not result.success and result.judge_feedback:
        print(f"Failure feedback: {result.judge_feedback.feedback}")
        
    assert result.agent_dir.exists()
    assert (result.agent_dir / "agent.py").exists()
    assert (result.agent_dir / "requirements.txt").exists()
    
    # Clean up (optional, keep for inspection if failed)
    # shutil.rmtree(output_dir)
