"""
调试脚本 - 查看 PM 的澄清问题

运行: python tests/integration/debug_pm_clarification.py
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.pm import PM
from src.llm import BuilderClient


async def main():
    print("=" * 80)
    print("调试 PM 澄清问题")
    print("=" * 80)
    print()
    
    builder = BuilderClient.from_env()
    pm = PM(builder)
    
    user_query = "创建一个能够回答 Agent Zero 项目文档问题的智能助手"
    file_paths = [
        project_root / "Agent Zero项目计划书.md",
        project_root / "Agent_Zero_详细实施计划.md"
    ]
    
    print(f"📝 用户需求: {user_query}")
    print(f"📁 文档数量: {len(file_paths)}")
    for fp in file_paths:
        print(f"   - {fp.name}")
    
    print("\n🤖 调用 PM 分析...")
    
    project_meta = await pm.analyze_with_clarification_loop(
        user_query=user_query,
        chat_history=[],
        file_paths=file_paths
    )
    
    print("\n" + "=" * 80)
    print("PM 分析结果")
    print("=" * 80)
    
    print(f"\n状态: {project_meta.status}")
    print(f"Agent 名称: {project_meta.agent_name}")
    print(f"任务类型: {project_meta.task_type}")
    print(f"需要 RAG: {project_meta.has_rag}")
    print(f"复杂度: {project_meta.complexity_score}/10")
    
    if project_meta.status == "clarifying":
        print("\n" + "=" * 80)
        print("⚠️  PM 需要澄清!")
        print("=" * 80)
        
        if project_meta.clarification_questions:
            print(f"\n澄清问题数量: {len(project_meta.clarification_questions)}")
            print("\n问题列表:")
            for i, question in enumerate(project_meta.clarification_questions, 1):
                print(f"\n{i}. {question}")
        else:
            print("\n⚠️  clarification_questions 为空!")
        
        # 显示完整的 ProjectMeta
        print("\n" + "=" * 80)
        print("完整 ProjectMeta (JSON)")
        print("=" * 80)
        print(project_meta.model_dump_json(indent=2, exclude_none=True))
        
    else:
        print("\n✅ PM 状态为 ready,无需澄清")
        
        if project_meta.execution_plan:
            print(f"\n执行计划 ({len(project_meta.execution_plan)} 步):")
            for step in project_meta.execution_plan:
                print(f"  {step.step}. [{step.role}] {step.goal}")


if __name__ == "__main__":
    asyncio.run(main())
