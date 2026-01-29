"""
快速测试 Test Generator 的调试输出
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.test_generator import TestGenerator, DeepEvalTestConfig
from src.llm.builder_client import BuilderClient
from src.schemas.project_meta import ProjectMeta, TaskType

async def test_debug_output():
    """测试调试输出"""
    print("=" * 70)
    print("🧪 测试 Test Generator 调试输出")
    print("=" * 70)
    
    # 创建 Builder Client
    builder = BuilderClient.from_env()
    
    # 创建 Test Generator
    test_gen = TestGenerator(builder)
    
    # 模拟文档路径
    file_paths = [
        str(project_root / "Agent Zero项目计划书.md"),
        str(project_root / "Agent_Zero_详细实施计划.md")
    ]
    
    print(f"\n📁 测试文档:")
    for fp in file_paths:
        exists = Path(fp).exists()
        print(f"   {'✅' if exists else '❌'} {fp}")
    
    # 提取问答对
    print(f"\n🚀 开始提取问答对...\n")
    qa_pairs = await test_gen._extract_qa_from_docs(file_paths, num_tests=3)
    
    print(f"\n" + "=" * 70)
    print(f"📊 结果:")
    print(f"   提取到 {len(qa_pairs)} 个问答对")
    for i, qa in enumerate(qa_pairs, 1):
        print(f"\n   问答对 {i}:")
        print(f"   Q: {qa.get('question', 'N/A')}")
        print(f"   A: {qa.get('expected_answer', 'N/A')[:100]}...")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_debug_output())
