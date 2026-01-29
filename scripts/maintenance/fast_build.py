
import asyncio
import os
from pathlib import Path
from src.core.agent_factory import AgentFactory
from src.core.progress_callback import ProgressCallback
from src.schemas import GraphStructure, SimulationResult

class FastBuildCallback(ProgressCallback):
    def on_step_start(self, step_name, step_num, total_steps):
        print(f"🚀 [Step {step_num}] {step_name}")
    
    def on_step_complete(self, step_name, result):
        print(f"✅ {step_name} OK")
        
    def on_log(self, message):
        print(f"   ℹ️  {message}")
        
    def on_blueprint_review(self, graph: GraphStructure, sim_result: SimulationResult):
        print("\n👀 Blueprint Review (AUTO-APPROVED)")
        print(f"   Pattern: {graph.pattern.pattern_type}")
        print(f"   Nodes: {[n.id for n in graph.nodes]}")
        print(f"   Issues: {[i.issue_type for i in sim_result.issues]}")
        return True, ""  # Auto-approve
        
    def on_api_key_missing(self, tool_name, env_var, help_text=""):
        # Auto-provide fake key if missing, for testing build flow
        if env_var == "TAVILY_API_KEY":
            # Check if env var is already set in OS
            if os.environ.get("TAVILY_API_KEY"):
                return None
            return "tv-fake-key-for-testing"
        return "fake-key"

async def run_fast_build():
    print("⚡ Fast Build Script Started")
    
    # 1. Setup Factory
    factory = AgentFactory(callback=FastBuildCallback())
    
    # --- MOCK PM AGENT to Bypass Interaction ---
    from src.schemas import ProjectMeta
    async def mock_analyze(user_input, file_paths=None):
        print("   ℹ️  [Mock] Skipping PM Agent, returning pre-defined metadata...")
        return ProjectMeta(
            agent_name="FastAgent_PE",
            description="A complex task agent that requires planning.",
            user_intent_summary="Search for AI news and generate a summary.",
            has_rag=False,
            task_type="search",
            # Force Plan-Execute Pattern:
            execution_plan=[
                "Step 1: Plan search queries",
                "Step 2: Search with Tavily",
                "Step 3: Analyze results",
                "Step 4: Generate summary"
            ],
            complexity_score=8
        )
    
    factory.pm.analyze = mock_analyze
    # -------------------------------------------
    
    # 2. Define Request
    user_input = "使用 Tavily 搜索今天的 AI 新闻并生成简洁的纯文本每日摘要"
    
    # 3. Build
    result = await factory.create_agent(
        user_input=user_input,
        output_dir=Path("./temp_agent_fast")
    )
    
    if result.success:
        print("\n🎉 Build Success!")
        print(f"📂 {result.agent_dir}")
    else:
        print("\n❌ Build Failed!")
        if result.judge_feedback:
            print(f"Error: {result.judge_feedback.feedback}")

if __name__ == "__main__":
    asyncio.run(run_fast_build())
