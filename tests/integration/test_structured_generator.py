"""
测试通用结构化生成器

验证 BuilderClient 的 generate_structured 方法
能够处理 DeepSeek API 的兼容性问题

运行: python tests/integration/test_structured_generator.py
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.llm import BuilderClient
from src.schemas import ProjectMeta, TaskType


async def test_structured_generation():
    """测试结构化生成"""
    print("=" * 80)
    print("测试通用结构化生成器")
    print("=" * 80)
    print()
    
    # 从环境变量加载客户端
    builder = BuilderClient.from_env()
    
    print(f"Provider: {builder.config.provider}")
    print(f"Model: {builder.config.model}")
    print(f"Base URL: {builder.config.base_url}")
    print()
    
    # 测试 Prompt
    prompt = """
    分析以下用户需求，生成 ProjectMeta:
    
    用户需求: "创建一个简单的聊天助手"
    
    要求:
    - agent_name: 合适的名称
    - description: 功能描述
    - has_rag: false (不需要 RAG)
    - task_type: chat
    - language: zh-CN
    - user_intent_summary: 用户意图总结
    - status: ready
    - complexity_score: 1-10 之间
    """
    
    print("🤖 调用结构化生成器...")
    print(f"Prompt: {prompt[:100]}...")
    print()
    
    try:
        # 调用通用结构化生成器
        result = await builder.generate_structured(
            prompt=prompt,
            response_model=ProjectMeta
        )
        
        print("✅ 生成成功!")
        print()
        print("=" * 80)
        print("生成的 ProjectMeta:")
        print("=" * 80)
        print(f"Agent 名称: {result.agent_name}")
        print(f"描述: {result.description}")
        print(f"任务类型: {result.task_type}")
        print(f"需要 RAG: {result.has_rag}")
        print(f"状态: {result.status}")
        print(f"复杂度: {result.complexity_score}/10")
        print()
        
        # 验证类型
        assert isinstance(result, ProjectMeta), "返回类型不正确"
        assert result.agent_name != "", "agent_name 为空"
        assert result.status == "ready", f"状态不正确: {result.status}"
        
        print("✅ 所有验证通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fallback_mode():
    """测试回退模式 (强制使用 Prompt 模式)"""
    print("\n" + "=" * 80)
    print("测试回退模式 (Prompt 增强)")
    print("=" * 80)
    print()
    
    builder = BuilderClient.from_env()
    
    # 简单的测试
    prompt = "创建一个名为 'TestBot' 的聊天助手的 ProjectMeta，状态为 ready"
    
    print("🤖 调用回退模式...")
    
    try:
        # 直接调用回退方法
        schema = ProjectMeta.model_json_schema()
        import json
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
        
        result = await builder._generate_structured_fallback(
            prompt=prompt,
            response_model=ProjectMeta,
            schema_str=schema_str,
            temperature=0.1
        )
        
        print("✅ 回退模式成功!")
        print(f"Agent 名称: {result.agent_name}")
        print(f"状态: {result.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ 回退模式失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  通用结构化生成器测试                                        ║
║                                                                              ║
║  测试目标: 验证 BuilderClient.generate_structured 方法                       ║
║  兼容性: 自动处理 DeepSeek 等不支持 response_format 的 API                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    results = {}
    
    # 测试 1: 标准结构化生成
    results['structured'] = await test_structured_generation()
    
    # 测试 2: 回退模式
    results['fallback'] = await test_fallback_mode()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if all(results.values()):
        print("\n🎉 所有测试通过! 通用结构化生成器工作正常")
        return True
    else:
        print("\n❌ 部分测试失败")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
