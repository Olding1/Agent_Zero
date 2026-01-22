"""
Test Generator - DeepEval 版本

生成专业的 DeepEval 测试代码,支持:
1. RAG Fact-based 测试 (使用外部 Trace)
2. Logic G-Eval 测试 (验证工具调用)
3. 简化的 Ollama 集成 (使用官方接口)
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path
import json

from src.llm.builder_client import BuilderClient
from src.schemas.project_meta import ProjectMeta, TaskType
from src.schemas.rag_config import RAGConfig


class DeepEvalTestConfig(BaseModel):
    """DeepEval 测试配置"""
    num_rag_tests: int = Field(default=5, ge=1, le=20, description="RAG 测试数量")
    num_logic_tests: int = Field(default=3, ge=1, le=10, description="Logic 测试数量")
    use_local_llm: bool = Field(default=True, description="使用本地 Ollama")
    judge_model: str = Field(default="llama3", description="评估用的模型")
    deepeval_version: str = Field(default="0.21.0", description="DeepEval 版本")
    
model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "num_rag_tests": 5,
                "num_logic_tests": 3,
                "use_local_llm": True,
                "judge_model": "llama3",
                "deepeval_version": "0.21.0"
            }
        }
    )


class TestGenerator:
    """DeepEval 测试生成器 (优化版)
    
    优化点:
    1. 使用外部 Trace 文件 (不占用 Context Window)
    2. 简化 Ollama 集成 (使用 ChatOllama,不自定义类)
    3. 支持启发式回退 (LLM 失败时)
    """
    
    def __init__(self, llm_client: BuilderClient):
        """初始化测试生成器
        
        Args:
            llm_client: Builder LLM 客户端 (用于生成测试用例)
        """
        self.llm = llm_client
    
    async def generate_deepeval_tests(
        self,
        project_meta: ProjectMeta,
        rag_config: Optional[RAGConfig] = None,
        config: DeepEvalTestConfig = DeepEvalTestConfig()
    ) -> str:
        """生成完整的 DeepEval 测试文件
        
        Args:
            project_meta: 项目元信息
            rag_config: RAG 配置 (如果有)
            config: 测试配置
        
        Returns:
            完整的 test_deepeval.py 文件内容
        """
        sections = []
        
        # 1. 导入语句
        sections.append(self._generate_imports(config))
        
        # 2. 配置 DeepEval (优化版 - 简化 Ollama 集成)
        sections.append(self._generate_deepeval_config_optimized(config))
        
        # 3. RAG 测试 (如果有 RAG)
        if rag_config and project_meta.has_rag:
            rag_tests = await self._generate_rag_tests(
                project_meta, rag_config, config.num_rag_tests
            )
            sections.append(rag_tests)
        
        # 4. Logic 测试
        logic_tests = await self._generate_logic_tests(
            project_meta, config.num_logic_tests
        )
        sections.append(logic_tests)
        
        return "\n\n".join(sections)
    
    def _generate_imports(self, config: DeepEvalTestConfig) -> str:
        """生成导入语句"""
        return f'''"""
Auto-generated DeepEval tests by Agent Zero
Generated with DeepEval v{config.deepeval_version}
"""
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualRecallMetric,
    ContextualPrecisionMetric,
    GEval
)
from deepeval.test_case import LLMTestCaseParams
import sys
import json
from pathlib import Path

# 导入 Agent
sys.path.insert(0, "..")
from agent import run_agent
'''
    
    def _generate_deepeval_config_optimized(self, config: DeepEvalTestConfig) -> str:
        """生成 DeepEval 配置 (优化版 - 使用官方接口)
        
        优化点:
        - 不再自定义 OllamaModel 类 (~150 行代码)
        - 直接使用 ChatOllama (~10 行代码)
        - DeepEval 会自动适配 LangChain 模型
        """
        if config.use_local_llm:
            return f'''
# ==================== DeepEval 配置 (动态适配版) ====================
import os
from deepeval.models import DeepEvalBaseLLM
from langchain_community.chat_models import ChatOpenAI, ChatOllama

class AgentZeroJudge(DeepEvalBaseLLM):
    """统一的 Agent Zero 评判模型适配器
    
    支持:
    1. OpenAI 兼容接口 (DeepSeek, GPT-4) - 优先
    2. Ollama 本地模型 - 回退
    """
    def __init__(self):
        # 1. 尝试读取 JUDGE 或 RUNTIME 环境变量
        self.api_key = os.getenv("JUDGE_API_KEY") or os.getenv("RUNTIME_API_KEY")
        self.base_url = os.getenv("JUDGE_BASE_URL") or os.getenv("RUNTIME_BASE_URL")
        self.model_name = os.getenv("JUDGE_MODEL") or os.getenv("RUNTIME_MODEL") or "deepseek-chat"
        self.provider = os.getenv("JUDGE_PROVIDER") or "openai"
        
        # 2. 判断通过哪种方式初始化
        if self.api_key and "sk-" in self.api_key:
            print(f"⚖️  DeepEval Judge: 使用云端模型 ({{self.model_name}})")
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                temperature=0.0
            )
            self._is_local = False
        else:
            print(f"⚖️  DeepEval Judge: 使用本地 Ollama ({config.judge_model})")
            self.llm = ChatOllama(
                model="{config.judge_model}",
                base_url="http://localhost:11434",
                temperature=0.0,
                format="json"  # 强制 JSON
            )
            self._is_local = True

    def load_model(self):
        return self.llm

    def generate(self, prompt: str) -> str:
        return self.llm.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        res = await self.llm.ainvoke(prompt)
        return res.content
        
    def get_model_name(self):
        return self.model_name

# 全局评判实例
judge_llm = AgentZeroJudge()
'''
        else:
            return '''
# ==================== DeepEval 配置 ====================
# 使用默认 OpenAI 模型
import os
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("请设置 OPENAI_API_KEY 环境变量")

judge_llm = None  # DeepEval 会使用默认 OpenAI 模型
'''
    
    async def _generate_rag_tests(
        self,
        project_meta: ProjectMeta,
        rag_config: RAGConfig,
        num_tests: int
    ) -> str:
        """生成 RAG 测试 (Fact-based,使用外部 Trace)
        
        Args:
            project_meta: 项目元信息 (包含 file_paths)
            rag_config: RAG 配置
            num_tests: 测试数量
        
        Returns:
            RAG 测试函数代码
        """
        # 1. 从文档提取问答对 (file_paths 在 project_meta 中)
        file_paths = project_meta.file_paths or []
        qa_pairs = await self._extract_qa_from_docs(
            file_paths, num_tests
        )
        
        # 2. 生成测试函数
        test_functions = []
        for i, qa in enumerate(qa_pairs, 1):
            test_func = f'''
def test_rag_fact_{i}():
    """测试 RAG Fact {i}: {qa['question'][:50]}..."""
    query = """{qa['question']}"""
    
    # 运行 Agent (获取 trace)
    output, trace = run_agent(query, return_trace=True)
    
    # 🆕 从外部 trace 文件提取检索内容
    rag_steps = [s for s in trace if s.get("action") == "rag_retrieval"]
    retrieved_docs = []
    if rag_steps:
        # 加载完整文档内容 (从外部文件)
        docs_file = rag_steps[0].get("docs_file")
        if docs_file:
            with open(docs_file, 'r', encoding='utf-8') as f:
                retrieved_docs = json.load(f)
    
    # 构造测试用例
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
        retrieval_context=retrieved_docs,
        expected_output="""{qa['expected_answer']}"""
    )
    
    # 定义指标 (🆕 直接使用 ChatOllama)
    faithfulness = FaithfulnessMetric(
        threshold=0.7,
        model=judge_llm,
        include_reason=True
    )
    recall = ContextualRecallMetric(
        threshold=0.8,
        model=judge_llm
    )
    
    # 断言
    assert_test(test_case, [faithfulness, recall])
    print(f"✅ RAG Fact {i} 测试通过")
'''
            test_functions.append(test_func)
        
        header = f'''
# ==================== RAG Fact-based 测试 ====================
# 从文档中提取的事实性问题,验证 RAG 准确性
# 使用指标: Faithfulness (忠实度), ContextualRecall (召回率)
'''
        return header + "\n".join(test_functions)
    
    async def _extract_qa_from_docs(
        self,
        file_paths: List[str],
        num_tests: int
    ) -> List[Dict[str, str]]:
        """从文档提取问答对 (使用 LLM)
        
        Args:
            file_paths: 文档路径列表
            num_tests: 需要提取的问答对数量
        
        Returns:
            问答对列表 [{"question": "...", "expected_answer": "..."}]
        """
        try:
            print(f"🔍 [调试] 开始提取问答对: {num_tests} 个, 文档数: {len(file_paths)}")
            
            # 1. 加载文档内容
            print(f"📄 [调试] 步骤 1/5: 加载文档...")
            document_content = await self._load_documents(file_paths)
            print(f"✅ [调试] 文档加载成功, 长度: {len(document_content)} 字符")
            
            # 2. 加载 Prompt 模板
            print(f"📝 [调试] 步骤 2/5: 加载 Prompt 模板...")
            prompt_template = self._load_prompt_template("test_generator_deepeval_rag.txt")
            print(f"✅ [调试] Prompt 模板加载成功, 长度: {len(prompt_template)} 字符")
            
            # 3. 构造 Prompt
            print(f"🔧 [调试] 步骤 3/5: 构造 Prompt...")
            prompt = prompt_template.format(
                num_tests=num_tests,
                document_content=document_content[:10000]  # 限制长度,避免超出 Context Window
            )
            print(f"✅ [调试] Prompt 构造成功, 长度: {len(prompt)} 字符")
            
            # 4. 调用 LLM
            print(f"🤖 [调试] 步骤 4/5: 调用 LLM 生成问答对...")
            response = await self.llm.call(prompt)  # 使用 call() 而非 generate()
            print(f"✅ [调试] LLM 响应成功, 长度: {len(response)} 字符")
            print(f"📋 [调试] LLM 响应预览 (前 200 字符):\n{response[:200]}...")
            
            # 5. 解析 JSON 响应
            print(f"🔍 [调试] 步骤 5/5: 解析 JSON 响应...")
            qa_pairs = self._parse_json_response(response)
            print(f"✅ [调试] JSON 解析成功, 提取到 {len(qa_pairs)} 个问答对")
            
            # 6. 验证和清理
            print(f"🧹 [调试] 验证和清理问答对...")
            qa_pairs = self._validate_qa_pairs(qa_pairs, num_tests)
            print(f"✅ [调试] 最终问答对数量: {len(qa_pairs)}")
            
            return qa_pairs
        
        except Exception as e:
            print(f"❌ [调试] 异常详情:")
            print(f"   异常类型: {type(e).__name__}")
            print(f"   异常信息: {e}")
            import traceback
            print(f"   堆栈跟踪:\n{traceback.format_exc()}")
            print(f"⚠️ LLM 提取失败: {e}, 使用启发式回退")
            return self._heuristic_generate_qa_pairs(num_tests)

    
    async def _load_documents(self, file_paths: List[str]) -> str:
        """加载文档内容
        
        Args:
            file_paths: 文档路径列表
        
        Returns:
            合并的文档内容
        """
        contents = []
        for file_path in file_paths[:5]:  # 最多加载 5 个文档
            try:
                path = Path(file_path)
                if path.exists() and path.suffix in ['.txt', '.md']:
                    content = path.read_text(encoding='utf-8')
                    contents.append(f"## {path.name}\n\n{content}")
            except Exception as e:
                print(f"⚠️ 无法加载文档 {file_path}: {e}")
        
        return "\n\n".join(contents) if contents else "示例文档内容"
    
    def _load_prompt_template(self, template_name: str) -> str:
        """加载 Prompt 模板
        
        Args:
            template_name: 模板文件名
        
        Returns:
            模板内容
        """
        template_path = Path(__file__).parent.parent / "prompts" / template_name
        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
        else:
            return "请从文档中提取 {num_tests} 个问答对:\n\n{document_content}"
    
    def _parse_json_response(self, response: str) -> List[Dict[str, str]]:
        """解析 LLM 的 JSON 响应 (增强版 - 三层解析策略)
        
        Args:
            response: LLM 响应
        
        Returns:
            问答对列表
        """
        import re
        
        # 1. 提取 JSON 代码块
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response
        
        # 2. Tier 1: 尝试直接解析
        try:
            qa_pairs = json.loads(json_str)
            if isinstance(qa_pairs, list):
                print(f"✅ JSON 解析成功 (Tier 1: 直接解析)")
                return qa_pairs
        except json.JSONDecodeError:
            pass
        
        # 3. Tier 2: 尝试修复常见格式错误
        try:
            # 修复缺少花括号的问题: [ "question" → [{"question"
            fixed_json = re.sub(
                r'\[\s*"question"',
                r'[{"question"',
                json_str
            )
            # 修复对象间缺少花括号: }, "question" → },{"question"
            fixed_json = re.sub(
                r'}\s*,\s*"question"',
                r'},{"question"',
                fixed_json
            )
            # 修复数组结尾缺少花括号: "answer": "..." ] → "answer": "..."}]
            fixed_json = re.sub(
                r'"\s*\]$',
                r'"}]',
                fixed_json
            )
            
            qa_pairs = json.loads(fixed_json)
            if isinstance(qa_pairs, list):
                print(f"✅ JSON 解析成功 (Tier 2: 格式修复)")
                return qa_pairs
        except:
            pass
        
        # 4. Tier 3: 使用正则提取问答对 (最后的兜底)
        questions = re.findall(r'"question"\s*:\s*"([^"]+)"', json_str)
        answers = re.findall(r'"expected_answer"\s*:\s*"([^"]+)"', json_str)
        
        if questions and answers and len(questions) == len(answers):
            print(f"✅ JSON 解析成功 (Tier 3: 正则提取, {len(questions)} 对)")
            return [
                {"question": q, "expected_answer": a}
                for q, a in zip(questions, answers)
            ]
        
        # 所有方法都失败
        return []
    
    def _validate_qa_pairs(
        self,
        qa_pairs: List[Dict[str, str]],
        num_tests: int
    ) -> List[Dict[str, str]]:
        """验证和清理问答对
        
        Args:
            qa_pairs: 原始问答对
            num_tests: 需要的数量
        
        Returns:
            验证后的问答对
        """
        validated = []
        for qa in qa_pairs:
            if isinstance(qa, dict) and 'question' in qa and 'expected_answer' in qa:
                validated.append({
                    'question': qa['question'].strip(),
                    'expected_answer': qa['expected_answer'].strip()
                })
        
        # 如果数量不足,补充示例
        while len(validated) < num_tests:
            validated.append({
                'question': f"示例问题 {len(validated) + 1}",
                'expected_answer': f"示例答案 {len(validated) + 1}"
            })
        
        return validated[:num_tests]
    
    def _heuristic_generate_qa_pairs(self, num_tests: int) -> List[Dict[str, str]]:
        """启发式生成问答对 (LLM 失败时的回退)
        
        Args:
            num_tests: 需要的数量
        
        Returns:
            问答对列表
        """
        return [
            {
                "question": f"这是一个测试问题 {i}",
                "expected_answer": f"这是对应的测试答案 {i}"
            }
            for i in range(1, num_tests + 1)
        ]
    
    async def _generate_logic_tests(
        self,
        project_meta: ProjectMeta,
        num_tests: int
    ) -> str:
        """生成 Logic 测试 (G-Eval,验证工具调用和流程)
        
        Args:
            project_meta: 项目元信息
            num_tests: 测试数量
        
        Returns:
            Logic 测试函数代码
        """
        # 基于 task_type 生成不同的测试
        if project_meta.task_type in [TaskType.ANALYSIS, TaskType.SEARCH]:
            return self._generate_tool_usage_tests(project_meta, num_tests)
        else:
            return self._generate_basic_logic_tests(project_meta, num_tests)
    
    def _generate_tool_usage_tests(
        self,
        project_meta: ProjectMeta,
        num_tests: int
    ) -> str:
        """生成工具使用测试 (G-Eval)"""
        test_func = '''
# ==================== Logic 测试 - 工具使用 ====================
# 验证工具调用逻辑是否正确

def test_tool_usage_correctness():
    """测试: 工具调用逻辑"""
    query = "计算 123 * 456 的结果"
    
    # 运行 Agent
    output, trace = run_agent(query, return_trace=True)
    
    # 提取工具调用
    tool_calls = [s for s in trace if s.get("action") == "tool_call"]
    
    # 构造测试用例
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
        retrieval_context=[json.dumps(trace, ensure_ascii=False)]  # 把 trace 作为上下文
    )
    
    # 自定义 G-Eval 指标
    tool_correctness = GEval(
        name="Tool Selection Correctness",
        criteria="""
        评估标准:
        1. 如果问题涉及数学计算,必须调用 calculator 工具
        2. 工具必须在最终回答之前被调用
        3. 最终答案必须包含正确的计算结果
        """,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.RETRIEVAL_CONTEXT
        ],
        threshold=0.8,
        model=judge_llm
    )
    
    # 断言
    assert_test(test_case, [tool_correctness])
    
    # 额外的硬性检查
    tool_names = [s.get("tool_name") for s in tool_calls]
    assert "calculator" in tool_names or "math" in tool_names, "应该调用计算工具"
    print("✅ 工具使用测试通过")
'''
        return test_func
    
    def _generate_basic_logic_tests(
        self,
        project_meta: ProjectMeta,
        num_tests: int
    ) -> str:
        """生成基础逻辑测试"""
        test_func = '''
# ==================== Logic 测试 - 基础逻辑 ====================
# 验证 Agent 的基本响应能力

def test_basic_response():
    """测试: 基本响应能力"""
    query = "你好"
    
    # 运行 Agent
    output, trace = run_agent(query, return_trace=True)
    
    # 构造测试用例
    test_case = LLMTestCase(
        input=query,
        actual_output=output
    )
    
    # 使用 Answer Relevancy 指标
    relevancy = AnswerRelevancyMetric(
        threshold=0.7,
        model=judge_llm
    )
    
    # 断言
    assert_test(test_case, [relevancy])
    
    # 基本检查
    assert len(output) > 0, "输出不应为空"
    print("✅ 基础响应测试通过")
'''
        return test_func


# ==================== 辅助函数 ====================

def save_test_file(test_content: str, output_path: Path):
    """保存测试文件
    
    Args:
        test_content: 测试代码内容
        output_path: 输出路径
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(test_content, encoding="utf-8")
    print(f"✅ 测试文件已保存: {output_path}")
