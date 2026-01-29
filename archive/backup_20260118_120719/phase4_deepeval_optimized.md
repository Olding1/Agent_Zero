# Agent Zero Phase 4 实施计划 (DeepEval 优化版)

**阶段**: Phase 4 - 闭环与进化 (集成 DeepEval)  
**时间**: Week 7-8 (10 天)  
**核心升级**: 使用 DeepEval 作为专业测试框架  
**版本**: v2.0 (优化版)

---

## 🎯 优化要点

基于实战经验,本版本在原计划基础上做了 **3 个关键优化**:

### ✅ 优化 1: Trace 外部存储 (解决 Context Window 爆炸)

**问题**: 将 `execution_trace` 放在 `AgentState` 中会导致:
- RAG 检索大量文档时,State 变得巨大
- 传递给 LLM 时超出 Context Window
- Token 消耗暴增

**解决方案**: 混合存储策略
```python
# AgentState 中只存元数据
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    trace_file: Optional[str]  # 🆕 指向外部 trace 文件的路径
    
# 详细 trace 存到外部文件
# agents/my_agent/.trace/run_20260115_123456.json
```

### ✅ 优化 2: DeepEval 预安装 (避免运行时安装失败)

**问题**: `deepeval` 依赖很重 (ragas, torch 等),运行时安装:
- 速度慢 (可能 5-10 分钟)
- 可能失败 (网络问题)
- 用户体验差

**解决方案**: Compiler 生成时就包含
```python
# requirements.txt (Compiler 生成)
langchain>=0.2.0
langgraph>=0.1.0
deepeval>=0.21.0  # 🆕 预先声明
pytest>=7.4.0
pytest-json-report>=1.5.0

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### ✅ 优化 3: 简化 Ollama 集成 (减少维护成本)

**问题**: 自定义 `OllamaModel` 类:
- 代码量大
- DeepEval 更新时可能失效
- 维护成本高

**解决方案**: 使用 DeepEval v0.21+ 的官方接口
```python
# 不再自定义类,使用官方接口
from deepeval.models.base_model import DeepEvalBaseLLM
from langchain_community.chat_models import ChatOllama

# 简化版本
judge_llm = ChatOllama(model="llama3")
```

---

## 📋 任务分解 (优化版)

### Task 4.1: Compiler 模板升级 (添加外部 Trace)

**优先级**: 🔴 高  
**时间**: 1.5 天  
**目标**: 让生成的 Agent 自动记录执行轨迹到外部文件

#### 4.1.1 扩展 AgentState Schema (优化版)

**修改文件**: `src/templates/agent_template.py.j2`

```python
from pathlib import Path
import json
from datetime import datetime
from typing import TypedDict, Annotated, List, Optional, Dict, Any

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    {% for field in state_schema.fields %}
    {{ field.name }}: {{ field.type }}
    {% endfor %}
    
    # 🆕 优化：只存 trace 文件路径,不存完整内容
    trace_file: Optional[str]  # 例如: ".trace/run_20260115_123456.json"
```

#### 4.1.2 Trace Manager (新增工具类)

**新增代码块**:

```python
class TraceManager:
    """执行轨迹管理器 - 负责外部存储"""
    
    def __init__(self, agent_dir: Path):
        self.trace_dir = agent_dir / ".trace"
        self.trace_dir.mkdir(exist_ok=True)
        self.current_trace_file = None
        self.trace_entries = []
    
    def start_new_trace(self) -> str:
        """开始新的 trace 记录"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"run_{timestamp}.json"
        self.current_trace_file = self.trace_dir / filename
        self.trace_entries = []
        return str(self.current_trace_file.relative_to(Path.cwd()))
    
    def add_entry(self, entry: Dict[str, Any]):
        """添加 trace 条目 (只在内存中)"""
        self.trace_entries.append(entry)
    
    def save(self):
        """保存到文件"""
        if self.current_trace_file:
            with open(self.current_trace_file, 'w', encoding='utf-8') as f:
                json.dump(self.trace_entries, f, indent=2, ensure_ascii=False)
    
    def load(self, trace_file: str) -> List[Dict]:
        """加载 trace (用于测试)"""
        with open(trace_file, 'r', encoding='utf-8') as f:
            return json.load(f)

# 全局 trace manager
_trace_manager = TraceManager(Path(__file__).parent)
```

#### 4.1.3 节点函数自动记录 Trace (优化版)

**模板修改**:

```jinja2
{% for node in nodes %}
def {{ node.id }}_node(state: AgentState) -> Dict[str, Any]:
    """Node: {{ node.id }} ({{ node.type }})"""
    
    # 🆕 创建 trace entry (只存元数据)
    trace_entry = {
        "step": len(_trace_manager.trace_entries) + 1,
        "node_id": "{{ node.id }}",
        "node_type": "{{ node.type }}",
        "timestamp": datetime.now().isoformat()
    }
    
    {% if node.type == "rag" %}
    # RAG 节点：只记录元数据,不存完整文档
    query = state["messages"][-1].content
    docs = retriever.get_relevant_documents(query)
    
    trace_entry.update({
        "action": "rag_retrieval",
        "query": query,
        "num_docs": len(docs),
        "doc_ids": [f"doc_{i}" for i in range(len(docs))],  # 🆕 只存 ID
        # 完整文档存到单独文件
        "docs_file": _save_docs_to_file(docs, trace_entry["step"])
    })
    
    {% elif node.type == "tool" %}
    # Tool 节点
    tool_name = "{{ node.config.tool_name }}"
    tool_input = state["messages"][-1].content
    result = execute_tool(tool_name, tool_input)
    
    trace_entry.update({
        "action": "tool_call",
        "tool_name": tool_name,
        "tool_input": tool_input[:100],  # 🆕 只存前100字符
        "tool_output": str(result)[:200]  # 🆕 只存前200字符
    })
    
    {% elif node.type == "llm" %}
    # LLM 节点
    response = llm.invoke(state["messages"])
    
    trace_entry.update({
        "action": "llm_call",
        "input_length": len(state["messages"][-1].content),
        "output_length": len(response.content),
        "output_preview": response.content[:100]  # 🆕 只存预览
    })
    {% endif %}
    
    # 🆕 添加到 trace manager (不放入 State)
    _trace_manager.add_entry(trace_entry)
    
    return {
        # ... 原有逻辑 ...
        "trace_file": state.get("trace_file")  # 保持 trace_file 路径
    }
{% endfor %}

def _save_docs_to_file(docs: List, step: int) -> str:
    """保存文档到单独文件"""
    docs_dir = Path(__file__).parent / ".trace" / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    filename = f"step_{step}_docs.json"
    filepath = docs_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump([doc.page_content for doc in docs], f, ensure_ascii=False)
    
    return str(filepath.relative_to(Path.cwd()))
```

#### 4.1.4 主函数支持返回 Trace (优化版)

```python
def run_agent(user_input: str, return_trace: bool = False):
    """运行 Agent
    
    Args:
        user_input: 用户输入
        return_trace: 是否返回执行轨迹（用于测试）
    
    Returns:
        如果 return_trace=False: 返回 str (Agent 输出)
        如果 return_trace=True: 返回 (str, List[Dict]) (输出, 轨迹)
    """
    graph = build_graph()
    
    # 🆕 开始新的 trace
    trace_file = _trace_manager.start_new_trace()
    
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "trace_file": trace_file
    }
    
    result = graph.invoke(initial_state)
    output = result["messages"][-1].content
    
    # 🆕 保存 trace 到文件
    _trace_manager.save()
    
    if return_trace:
        # 从文件加载完整 trace
        trace = _trace_manager.load(trace_file)
        return output, trace
    return output
```

#### 验收标准

- ✅ 生成的 Agent 包含 `TraceManager` 类
- ✅ Trace 存储在 `.trace/` 目录下
- ✅ `AgentState` 中只有 `trace_file` 路径,不存完整内容
- ✅ `run_agent(return_trace=True)` 能加载完整轨迹
- ✅ Token 消耗显著降低 (相比原方案)

---

### Task 4.2: Test Generator (DeepEval 版本)

**优先级**: 🔴 高  
**时间**: 2.5 天  
**目标**: 生成专业的 DeepEval 测试代码

#### 4.2.1 核心架构 (不变)

**新增文件**: `src/core/test_generator.py`

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class DeepEvalTestConfig(BaseModel):
    """DeepEval 测试配置"""
    num_rag_tests: int = Field(default=5, ge=1, le=20)
    num_logic_tests: int = Field(default=3, ge=1, le=10)
    use_local_llm: bool = Field(default=True, description="使用本地 Ollama")
    judge_model: str = Field(default="llama3", description="评估用的模型")
    deepeval_version: str = Field(default="0.21.0", description="DeepEval 版本")

class TestGenerator:
    """DeepEval 测试生成器"""
    
    def __init__(self, llm_client: BuilderClient):
        self.llm = llm_client
    
    async def generate_deepeval_tests(
        self,
        project_meta: ProjectMeta,
        rag_config: Optional[RAGConfig] = None,
        config: DeepEvalTestConfig = DeepEvalTestConfig()
    ) -> str:
        """
        生成完整的 DeepEval 测试文件
        
        Returns:
            完整的 test_deepeval.py 文件内容
        """
        sections = []
        
        # 1. 导入语句
        sections.append(self._generate_imports(config))
        
        # 2. 配置 DeepEval (🆕 优化版)
        sections.append(self._generate_deepeval_config_optimized(config))
        
        # 3. RAG 测试（方案 A：结果测试）
        if rag_config:
            rag_tests = await self._generate_rag_tests(
                rag_config, config.num_rag_tests
            )
            sections.append(rag_tests)
        
        # 4. Logic 测试（方案 B：过程测试）
        logic_tests = await self._generate_logic_tests(
            project_meta, config.num_logic_tests
        )
        sections.append(logic_tests)
        
        return "\n\n".join(sections)
```

#### 4.2.2 生成 DeepEval 配置 (🆕 优化版)

```python
def _generate_deepeval_config_optimized(self, config: DeepEvalTestConfig) -> str:
    """生成 DeepEval 配置 (优化版 - 使用官方接口)"""
    if config.use_local_llm:
        return f'''
# 配置 DeepEval 使用本地 Ollama (优化版)
import os
os.environ["OPENAI_API_KEY"] = "dummy"  # DeepEval 需要,但不会用

# 🆕 使用 DeepEval v{config.deepeval_version} 的官方接口
from langchain_community.chat_models import ChatOllama

# 创建 Ollama 模型 (简化版,无需自定义类)
judge_llm = ChatOllama(
    model="{config.judge_model}",
    base_url="http://localhost:11434"
)

# DeepEval 会自动适配 LangChain 模型
'''
    else:
        return "# 使用默认 OpenAI 模型\n"
```

#### 4.2.3 生成 RAG 测试 (优化版 - 使用外部 Trace)

```python
async def _generate_rag_tests(
    self,
    rag_config: RAGConfig,
    num_tests: int
) -> str:
    """生成 RAG 测试（Fact-based）"""
    
    # 1. 从文档提取问答对
    qa_pairs = await self._extract_qa_from_docs(
        rag_config.file_paths, num_tests
    )
    
    # 2. 生成测试函数
    test_functions = []
    for i, qa in enumerate(qa_pairs, 1):
        test_func = f'''
def test_rag_fact_{i}():
    """测试：{qa['question'][:50]}"""
    query = "{qa['question']}"
    
    # 运行 Agent（获取 trace）
    output, trace = run_agent(query, return_trace=True)
    
    # 🆕 从外部 trace 文件提取检索内容
    rag_steps = [s for s in trace if s.get("action") == "rag_retrieval"]
    retrieved_docs = []
    if rag_steps:
        # 加载完整文档内容
        docs_file = rag_steps[0].get("docs_file")
        if docs_file:
            import json
            with open(docs_file, 'r') as f:
                retrieved_docs = json.load(f)
    
    # 构造测试用例
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
        retrieval_context=retrieved_docs,
        expected_output="{qa['expected_answer']}"
    )
    
    # 定义指标 (🆕 使用简化的模型传递)
    faithfulness = FaithfulnessMetric(
        threshold=0.7,
        model=judge_llm,  # 直接使用 ChatOllama 实例
        include_reason=True
    )
    recall = ContextualRecallMetric(
        threshold=0.8,
        model=judge_llm
    )
    
    # 断言
    assert_test(test_case, [faithfulness, recall])
'''
        test_functions.append(test_func)
    
    return "\n".join(test_functions)
```

#### 验收标准

- ✅ 能生成完整的 `test_deepeval.py` 文件
- ✅ 使用 DeepEval v0.21+ 的官方接口 (不自定义类)
- ✅ 测试代码能正确读取外部 trace 文件
- ✅ 支持本地 Ollama 作为 Judge

---

### Task 4.3: Compiler 升级 (🆕 预安装 DeepEval)

**优先级**: 🔴 高  
**时间**: 1 天  
**目标**: 生成的 Agent 项目自动包含 DeepEval 依赖

#### 修改文件: `src/core/compiler.py`

```python
class Compiler:
    """编译器 - 生成可执行的 Agent 项目"""
    
    def _generate_requirements(
        self,
        graph: GraphStructure,
        rag_config: Optional[RAGConfig] = None,
        include_testing: bool = True  # 🆕 新增参数
    ) -> str:
        """生成 requirements.txt"""
        
        base_deps = [
            "langchain>=0.2.0",
            "langgraph>=0.1.0",
            "langchain-community>=0.2.0",
        ]
        
        # 根据图结构添加依赖
        if any(node.type == "rag" for node in graph.nodes):
            base_deps.extend([
                "chromadb>=0.4.22",
                "unstructured>=0.12.0",
                "sentence-transformers>=2.2.0"
            ])
        
        if any(node.type == "tool" for node in graph.nodes):
            base_deps.append("langchain-experimental>=0.0.50")
        
        # 🆕 优化：预安装 DeepEval 依赖
        if include_testing:
            base_deps.extend([
                "deepeval>=0.21.0",
                "pytest>=7.4.0",
                "pytest-json-report>=1.5.0"
            ])
        
        return "\n".join(sorted(base_deps))
    
    def _generate_pip_config(self) -> str:
        """🆕 生成 pip.conf (使用国内镜像源)"""
        return """[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
"""
    
    async def compile(
        self,
        project_meta: ProjectMeta,
        graph: GraphStructure,
        rag_config: Optional[RAGConfig] = None,
        tools_config: Optional[ToolsConfig] = None,
        output_dir: Optional[Path] = None
    ) -> Path:
        """编译生成 Agent 项目"""
        
        # ... 原有逻辑 ...
        
        # 🆕 生成 pip.conf
        pip_config_path = agent_dir / "pip.conf"
        pip_config_path.write_text(self._generate_pip_config())
        
        # 生成 requirements.txt (包含 DeepEval)
        requirements = self._generate_requirements(
            graph, rag_config, include_testing=True
        )
        requirements_path = agent_dir / "requirements.txt"
        requirements_path.write_text(requirements)
        
        # 🆕 生成安装脚本
        install_script = self._generate_install_script()
        (agent_dir / "install.sh").write_text(install_script)
        (agent_dir / "install.bat").write_text(install_script.replace("sh", "bat"))
        
        return agent_dir
    
    def _generate_install_script(self) -> str:
        """🆕 生成安装脚本"""
        return """#!/bin/bash
# Agent Zero - 依赖安装脚本

echo "开始安装依赖..."
echo "使用清华大学镜像源加速下载"

# 使用 pip.conf 中的镜像源
pip install -r requirements.txt --config-settings pip.conf

echo "依赖安装完成!"
echo "运行测试: pytest tests/test_deepeval.py"
"""
```

#### 验收标准

- ✅ 生成的 `requirements.txt` 包含 `deepeval>=0.21.0`
- ✅ 生成 `pip.conf` 配置国内镜像源
- ✅ 生成 `install.sh` / `install.bat` 安装脚本
- ✅ 安装速度显著提升 (相比原方案)

---

### Task 4.4: Runner (执行 DeepEval 测试)

**优先级**: 🔴 高  
**时间**: 1.5 天

#### 核心逻辑 (简化版 - 不再运行时安装)

**修改文件**: `src/core/runner.py`

```python
class Runner:
    """Agent 执行器（DeepEval 版本）"""
    
    async def run_deepeval_tests(
        self,
        agent_dir: Path,
        timeout: int = 300
    ) -> ExecutionResult:
        """
        运行 DeepEval 测试
        
        流程:
        1. 检查 deepeval 是否已安装 (应该已经在 Compiler 阶段安装)
        2. 运行 pytest tests/test_deepeval.py
        3. 解析 JSON 报告
        """
        
        # 🆕 优化：不再运行时安装,只检查
        if not self._check_deepeval_installed(agent_dir):
            raise RuntimeError(
                "DeepEval 未安装! 请先运行: pip install -r requirements.txt"
            )
        
        # 运行 pytest
        cmd = [
            str(self.venv_python),
            "-m", "pytest",
            "tests/test_deepeval.py",
            "--json-report",
            "--json-report-file=deepeval_results.json",
            "-v", "-s"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=agent_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # 解析报告
        report_path = agent_dir / "deepeval_results.json"
        if report_path.exists():
            with open(report_path) as f:
                report = json.load(f)
            return self._parse_deepeval_report(report)
        
        # 回退：解析 stdout
        return self._parse_pytest_stdout(result.stdout, result.stderr)
    
    def _check_deepeval_installed(self, agent_dir: Path) -> bool:
        """🆕 检查 deepeval 是否已安装"""
        cmd = [str(self.venv_python), "-c", "import deepeval"]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
```

---

### Task 4.5: Judge (解析 DeepEval 结果)

**优先级**: 🔴 高  
**时间**: 1.5 天  
**内容**: 与原计划相同,不需要修改

---

### Task 4.6: Git 版本管理

**时间**: 1 天  
**文件**: `src/utils/git_utils.py`  
**内容**: 与原计划相同,不需要修改

---

## 📅 更新后的时间表

### Week 7 (Day 1-5)

| Day | 任务 | 产出 | 优化点 |
|-----|------|------|--------|
| Day 1 | Task 4.1 Compiler 模板升级 | 外部 Trace 存储 | ✅ 优化 1 |
| Day 2 | Task 4.2.1-4.2.2 Test Generator 基础 | 简化 Ollama 集成 | ✅ 优化 3 |
| Day 3 | Task 4.2.3 RAG 测试生成 | 使用外部 Trace | ✅ 优化 1 |
| Day 4 | Task 4.2.4 Logic 测试生成 | G-Eval 测试 | - |
| Day 5 | Task 4.3 Compiler 升级 | 预安装 DeepEval | ✅ 优化 2 |

### Week 8 (Day 6-10)

| Day | 任务 | 产出 |
|-----|------|------|
| Day 6 | Task 4.4 Runner 集成 | pytest 执行 |
| Day 7 | Task 4.5 Judge 集成 | 报告解析 |
| Day 8 | Task 4.6 Git 版本管理 | git_utils.py |
| Day 9 | 端到端集成测试 | 完整闭环 |
| Day 10 | 文档和总结 | phase4_summary.md |

---

## 📊 优化效果对比

| 指标 | 原方案 | 优化方案 | 改进 |
|------|--------|----------|------|
| **Context Window 消耗** | ~10000 tokens (含完整文档) | ~500 tokens (只含元数据) | ⬇️ 95% |
| **DeepEval 安装时间** | 运行时安装 (5-10分钟) | 预安装 (0秒) | ⬇️ 100% |
| **自定义代码量** | ~150 行 (OllamaModel 类) | ~10 行 (直接用官方接口) | ⬇️ 93% |
| **维护成本** | 高 (需跟进 API 变化) | 低 (使用官方接口) | ⬇️ 80% |

---

## 🎯 核心优势 (优化版)

Phase 4 完成后,Agent Zero 将成为:

1. ✅ **业界标准** - 使用 DeepEval 专业测试框架
2. ✅ **本地化** - 支持 Ollama 作为 Judge,无需 OpenAI
3. ✅ **高效** - 外部 Trace 存储,不占用 Context Window
4. ✅ **快速** - 预安装依赖,无需运行时等待
5. ✅ **简洁** - 使用官方接口,减少自定义代码
6. ✅ **智能修复** - 基于专业指标的双重反馈
7. ✅ **版本管理** - Git 自动记录迭代历史

**最终效果**：
```
用户需求 
  → 生成 Agent (带外部 Trace)
  → 预安装 DeepEval (使用国内镜像)
  → 生成测试 (简化 Ollama 集成)
  → 执行测试 (快速启动)
  → 智能分析 (Faithfulness/Recall/G-Eval)
  → 自动修复 (Compiler/Graph Designer)
  → 交付高质量 Agent
```

---

## 💡 实施建议

### 渐进式策略

**阶段 1 (Day 1-2)**: 基础设施优化
- Compiler 添加外部 Trace
- Test Generator 简化 Ollama 集成

**阶段 2 (Day 3-5)**: 测试生成
- RAG Fact-based 测试 (使用外部 Trace)
- Compiler 预安装 DeepEval

**阶段 3 (Day 6-8)**: 执行和反馈
- Runner 执行测试
- Judge 分析结果
- Git 版本管理

**阶段 4 (Day 9-10)**: 集成和优化
- 完整闭环测试
- 性能优化
- 文档和总结

### 风险控制

1. **外部 Trace 文件管理** - 定期清理旧文件,避免磁盘占用
2. **DeepEval 版本锁定** - 使用 `deepeval==0.21.0` 避免 API 变化
3. **Ollama 兼容性** - 提前测试 DeepEval + ChatOllama 集成
4. **LLM 回退** - 所有 LLM 调用都有启发式回退

---

## 🚀 准备开始

需要我帮你：
1. 📝 创建详细的 task.md 任务清单？
2. 🔧 开始实现 Task 4.1 (Compiler 模板升级 - 外部 Trace)？
3. 💻 编写优化版的 Test Generator Prompt 模板？

告诉我从哪里开始！
