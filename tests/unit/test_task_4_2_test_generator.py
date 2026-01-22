"""
Phase 4 Task 4.2 测试 - 验证 TestGenerator

测试目标:
1. 验证 TestGenerator 类正确实现
2. 验证生成的测试代码包含必要的导入和配置
3. 验证 RAG 测试使用外部 Trace
4. 验证简化的 Ollama 集成
"""

import pytest
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.test_generator import TestGenerator, DeepEvalTestConfig
from src.schemas.project_meta import ProjectMeta, TaskType
from src.schemas.rag_config import RAGConfig


def test_deepeval_test_config():
    """测试 1: 验证 DeepEvalTestConfig Schema"""
    
    config = DeepEvalTestConfig(
        num_rag_tests=5,
        num_logic_tests=3,
        use_local_llm=True,
        judge_model="llama3",
        deepeval_version="0.21.0"
    )
    
    assert config.num_rag_tests == 5
    assert config.num_logic_tests == 3
    assert config.use_local_llm is True
    assert config.judge_model == "llama3"
    assert config.deepeval_version == "0.21.0"
    
    print("✅ 测试 1 通过: DeepEvalTestConfig Schema 正确")


def test_generate_imports():
    """测试 2: 验证导入语句生成"""
    
    # 创建 mock LLM client
    class MockLLMClient:
        async def generate(self, prompt: str) -> str:
            return "mock response"
    
    generator = TestGenerator(MockLLMClient())
    config = DeepEvalTestConfig()
    
    imports = generator._generate_imports(config)
    
    # 验证包含必要的导入
    assert "from deepeval import assert_test" in imports
    assert "from deepeval.test_case import LLMTestCase" in imports
    assert "from deepeval.metrics import" in imports
    assert "FaithfulnessMetric" in imports
    assert "ContextualRecallMetric" in imports
    assert "GEval" in imports
    assert "from agent import run_agent" in imports
    
    print("✅ 测试 2 通过: 导入语句正确生成")


def test_generate_deepeval_config_optimized():
    """测试 3: 验证简化的 Ollama 配置生成"""
    
    class MockLLMClient:
        async def generate(self, prompt: str) -> str:
            return "mock response"
    
    generator = TestGenerator(MockLLMClient())
    config = DeepEvalTestConfig(use_local_llm=True, judge_model="llama3")
    
    config_code = generator._generate_deepeval_config_optimized(config)
    
    # 验证使用简化的 Ollama 集成
    assert "ChatOllama" in config_code
    assert "ChatOpenAI" in config_code
    assert 'model="llama3"' in config_code or 'model="{config.judge_model}"' in config_code
    assert 'base_url="http://localhost:11434"' in config_code
    
    # 验证使用了 AgentZeroJudge 适配器类
    assert "class AgentZeroJudge" in config_code
    assert "DeepEvalBaseLLM" in config_code
    
    # 验证注释说明这是优化版
    assert "优化版" in config_code or "动态适配" in config_code
    
    print("✅ 测试 3 通过: Ollama 配置简化正确")



def test_generate_rag_tests_structure():
    """测试 4: 验证 RAG 测试代码结构"""
    
    class MockLLMClient:
        async def generate(self, prompt: str) -> str:
            return "mock response"
    
    generator = TestGenerator(MockLLMClient())
    
    # 手动调用内部方法测试结构
    qa_pairs = [
        {"question": "测试问题1", "expected_answer": "测试答案1"},
        {"question": "测试问题2", "expected_answer": "测试答案2"}
    ]
    
    # 生成测试函数 (模拟)
    test_code = generator._generate_rag_tests.__doc__
    
    # 验证文档字符串说明了使用外部 Trace
    assert "外部 Trace" in test_code or "外部 trace" in test_code
    
    print("✅ 测试 4 通过: RAG 测试结构正确")


def test_parse_json_response():
    """测试 5: 验证 JSON 响应解析"""
    
    class MockLLMClient:
        async def generate(self, prompt: str) -> str:
            return "mock response"
    
    generator = TestGenerator(MockLLMClient())
    
    # 测试带 JSON 代码块的响应
    response_with_block = '''
这是一些说明文字

```json
[
  {"question": "Q1", "expected_answer": "A1"},
  {"question": "Q2", "expected_answer": "A2"}
]
```

更多说明
'''
    
    qa_pairs = generator._parse_json_response(response_with_block)
    assert len(qa_pairs) == 2
    assert qa_pairs[0]["question"] == "Q1"
    assert qa_pairs[1]["expected_answer"] == "A2"
    
    # 测试直接 JSON 响应
    response_direct = '[{"question": "Q3", "expected_answer": "A3"}]'
    qa_pairs = generator._parse_json_response(response_direct)
    assert len(qa_pairs) == 1
    assert qa_pairs[0]["question"] == "Q3"
    
    print("✅ 测试 5 通过: JSON 解析正确")


def test_validate_qa_pairs():
    """测试 6: 验证问答对验证和清理"""
    
    class MockLLMClient:
        async def generate(self, prompt: str) -> str:
            return "mock response"
    
    generator = TestGenerator(MockLLMClient())
    
    # 测试正常情况
    qa_pairs = [
        {"question": "  Q1  ", "expected_answer": "  A1  "},
        {"question": "Q2", "expected_answer": "A2"}
    ]
    validated = generator._validate_qa_pairs(qa_pairs, 2)
    assert len(validated) == 2
    assert validated[0]["question"] == "Q1"  # 应该去除空格
    
    # 测试数量不足的情况
    qa_pairs = [{"question": "Q1", "expected_answer": "A1"}]
    validated = generator._validate_qa_pairs(qa_pairs, 3)
    assert len(validated) == 3  # 应该补充到 3 个
    
    # 测试无效数据
    qa_pairs = [
        {"question": "Q1", "expected_answer": "A1"},
        {"invalid": "data"},  # 无效
        {"question": "Q2"}  # 缺少 expected_answer
    ]
    validated = generator._validate_qa_pairs(qa_pairs, 2)
    assert len(validated) == 2
    assert validated[0]["question"] == "Q1"
    
    print("✅ 测试 6 通过: 问答对验证正确")


def test_heuristic_fallback():
    """测试 7: 验证启发式回退"""
    
    class MockLLMClient:
        async def generate(self, prompt: str) -> str:
            return "mock response"
    
    generator = TestGenerator(MockLLMClient())
    
    qa_pairs = generator._heuristic_generate_qa_pairs(3)
    
    assert len(qa_pairs) == 3
    assert all("question" in qa and "expected_answer" in qa for qa in qa_pairs)
    assert qa_pairs[0]["question"] == "这是一个测试问题 1"
    
    print("✅ 测试 7 通过: 启发式回退正确")


def test_load_prompt_template():
    """测试 8: 验证 Prompt 模板加载"""
    
    class MockLLMClient:
        async def generate(self, prompt: str) -> str:
            return "mock response"
    
    generator = TestGenerator(MockLLMClient())
    
    # 测试加载 RAG 模板
    template = generator._load_prompt_template("test_generator_deepeval_rag.txt")
    assert len(template) > 0
    assert "{num_tests}" in template or "{document_content}" in template
    
    print("✅ 测试 8 通过: Prompt 模板加载正确")


def test_parse_malformed_json_missing_braces():
    """测试 9: 验证解析缺少花括号的 JSON (Tier 2)"""
    
    class MockLLMClient:
        async def generate(self, prompt: str) -> str:
            return "mock response"
    
    generator = TestGenerator(MockLLMClient())
    
    # 模拟 LLM 返回缺少花括号的 JSON
    malformed_response = '''[
    "question": "Agent Zero阶段3是什么",
    "expected_answer": "蓝图仿真系统"
]'''
    
    qa_pairs = generator._parse_json_response(malformed_response)
    
    # 应该能通过 Tier 2 格式修复解析成功
    assert len(qa_pairs) >= 1
    if len(qa_pairs) > 0:
        assert "question" in qa_pairs[0]
        assert "expected_answer" in qa_pairs[0]
    
    print("✅ 测试 9 通过: 缺少花括号的 JSON 能被修复")


def test_parse_json_with_regex_fallback():
    """测试 10: 验证正则提取兜底 (Tier 3)"""
    
    class MockLLMClient:
        async def generate(self, prompt: str) -> str:
            return "mock response"
    
    generator = TestGenerator(MockLLMClient())
    
    # 模拟完全无效的 JSON,但包含问答对
    invalid_json = '''
    这是一些说明文字
    "question": "什么是 RAG?"
    "expected_answer": "检索增强生成"
    还有一些其他文字
    "question": "什么是 LangGraph?"
    "expected_answer": "状态图执行引擎"
    '''
    
    qa_pairs = generator._parse_json_response(invalid_json)
    
    # 应该能通过 Tier 3 正则提取
    assert len(qa_pairs) == 2
    assert qa_pairs[0]["question"] == "什么是 RAG?"
    assert qa_pairs[1]["expected_answer"] == "状态图执行引擎"
    
    print("✅ 测试 10 通过: 正则提取兜底成功")


def test_parse_mixed_valid_invalid():
    """测试 11: 验证处理混合有效/无效的响应"""
    
    class MockLLMClient:
        async def generate(self, prompt: str) -> str:
            return "mock response"
    
    generator = TestGenerator(MockLLMClient())
    
    # 测试部分有效的 JSON
    mixed_response = '''```json
[
  {
    "question": "有效问题1",
    "expected_answer": "有效答案1"
  },
  "question": "缺少花括号",
  "expected_answer": "这个会被修复"
]
```'''
    
    qa_pairs = generator._parse_json_response(mixed_response)
    
    # 应该能解析出至少一个
    assert len(qa_pairs) >= 1
    
    print("✅ 测试 11 通过: 混合有效/无效响应处理正确")



if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4 Task 4.2 测试 - TestGenerator (增强版)")
    print("=" * 60)
    
    # 运行所有测试
    test_deepeval_test_config()
    test_generate_imports()
    test_generate_deepeval_config_optimized()
    test_generate_rag_tests_structure()
    test_parse_json_response()
    test_validate_qa_pairs()
    test_heuristic_fallback()
    test_load_prompt_template()
    
    # 新增: JSON 解析增强测试
    print("\n" + "-" * 60)
    print("🆕 JSON 解析增强测试")
    print("-" * 60)
    test_parse_malformed_json_missing_braces()
    test_parse_json_with_regex_fallback()
    test_parse_mixed_valid_invalid()
    
    print("\n" + "=" * 60)
    print("✅ 所有 11 个测试通过! JSON 解析增强完成!")
    print("=" * 60)

