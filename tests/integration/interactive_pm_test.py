"""
交互式 PM 澄清测试

这个脚本会:
1. 调用 PM 分析需求
2. 如果需要澄清,显示问题并等待您输入答案
3. 提交答案后重新分析
4. 重复直到 PM 状态变为 ready

运行: python tests/integration/interactive_pm_test.py
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
    print("交互式 PM 澄清测试")
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
    
    print("\n" + "=" * 80)
    print("第 1 轮: 初始分析")
    print("=" * 80)
    print("\n🤖 调用 PM 分析...")
    
    project_meta = await pm.analyze_with_clarification_loop(
        user_query=user_query,
        chat_history=[],
        file_paths=file_paths
    )
    
    # 澄清循环
    round_num = 1
    max_rounds = 5  # 最多 5 轮澄清
    
    while project_meta.status == "clarifying" and round_num <= max_rounds:
        print("\n" + "=" * 80)
        print(f"⚠️  PM 需要澄清 (第 {round_num} 轮)")
        print("=" * 80)
        
        if not project_meta.clarification_questions:
            print("\n❌ 错误: clarification_questions 为空")
            break
        
        print(f"\n澄清问题数量: {len(project_meta.clarification_questions)}")
        print("\n请回答以下问题:")
        print("-" * 80)
        
        # 收集答案
        clarification_answers = {}
        
        for i, question in enumerate(project_meta.clarification_questions, 1):
            print(f"\n问题 {i}:")
            print(f"{question}")
            print()
            
            # 等待用户输入
            answer = input("您的回答: ").strip()
            
            if not answer:
                print("⚠️  答案为空,使用默认答案: '按默认配置'")
                answer = "按默认配置"
            
            clarification_answers[question] = answer
            print(f"✓ 已记录答案: {answer}")
        
        # 显示所有答案
        print("\n" + "=" * 80)
        print("您提供的答案:")
        print("=" * 80)
        for q, a in clarification_answers.items():
            print(f"\nQ: {q}")
            print(f"A: {a}")
        
        # 重新分析
        print("\n" + "=" * 80)
        print(f"第 {round_num + 1} 轮: 根据澄清重新分析")
        print("=" * 80)
        print("\n🤖 调用 PM 重新分析...")
        
        try:
            project_meta = await pm.refine_with_clarification(
                project_meta,
                clarification_answers
            )
            
            print(f"\n✓ 重新分析完成")
            print(f"  状态: {project_meta.status}")
            print(f"  Agent 名称: {project_meta.agent_name}")
            
        except Exception as e:
            print(f"\n❌ 重新分析失败: {e}")
            
            # 尝试不使用 structured output
            print("\n🔄 尝试使用普通模式重新分析...")
            try:
                # 直接调用 analyze_requirements (不使用 structured output)
                project_meta = await pm.analyze_requirements(
                    user_input=user_query,
                    file_paths=file_paths,
                    clarification_answers=clarification_answers
                )
                print(f"\n✓ 普通模式分析完成")
                print(f"  状态: {project_meta.status}")
                print(f"  Agent 名称: {project_meta.agent_name}")
            except Exception as e2:
                print(f"\n❌ 普通模式也失败: {e2}")
                break
        
        round_num += 1
    
    # 最终结果
    print("\n" + "=" * 80)
    print("最终结果")
    print("=" * 80)
    
    print(f"\n状态: {project_meta.status}")
    
    if project_meta.status == "ready":
        print("\n🎉 成功! PM 澄清完成,状态为 ready")
        print("\n最终 ProjectMeta:")
        print(f"  Agent 名称: {project_meta.agent_name}")
        print(f"  任务类型: {project_meta.task_type}")
        print(f"  需要 RAG: {project_meta.has_rag}")
        print(f"  复杂度: {project_meta.complexity_score}/10")
        
        if project_meta.execution_plan:
            print(f"\n  执行计划 ({len(project_meta.execution_plan)} 步):")
            for step in project_meta.execution_plan:
                print(f"    {step.step}. [{step.role}] {step.goal}")
        
        # 保存结果
        output_file = project_root / "tests" / "integration" / "pm_clarification_result.json"
        output_file.write_text(project_meta.model_dump_json(indent=2), encoding='utf-8')
        print(f"\n✓ 结果已保存到: {output_file}")
        
    elif project_meta.status == "clarifying":
        print(f"\n⚠️  澄清未完成 (已进行 {round_num - 1} 轮)")
        if round_num > max_rounds:
            print(f"   达到最大轮数限制 ({max_rounds} 轮)")
        print("\n当前仍需澄清的问题:")
        for i, q in enumerate(project_meta.clarification_questions or [], 1):
            print(f"  {i}. {q}")
    
    else:
        print(f"\n❓ 未知状态: {project_meta.status}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     交互式 PM 澄清测试                                       ║
║                                                                              ║
║  这个脚本会引导您完成 PM 的澄清流程                                          ║
║  您需要手动回答 PM 提出的问题                                                ║
║  测试目标: 验证澄清流程能否成功到达 ready 状态                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    asyncio.run(main())
