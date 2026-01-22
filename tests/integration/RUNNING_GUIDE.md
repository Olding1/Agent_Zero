# 集成测试实际运行指南

## 问题 1: Mock 数据是什么意思?

### 什么是 Mock?

**Mock** 是测试中的"模拟数据",用来替代真实的外部依赖。

### 为什么使用 Mock?

在集成测试中,PM 和 GraphDesigner 需要调用 LLM API (如 DeepSeek, OpenAI 等):

```python
# 真实调用 (需要 API Key 和网络)
pm = PM(BuilderClient(api_key="sk-xxx"))
result = await pm.analyze_requirements("创建 RAG Agent")
```

但在测试中,我们使用 Mock:

```python
# Mock 调用 (不需要 API Key)
class MockBuilderClient:
    async def call(self, prompt: str, schema=None):
        # 直接返回预设的结果
        return ProjectMeta(
            agent_name="test_agent",
            task_type=TaskType.RAG,
            has_rag=True
        )

pm = PM(MockBuilderClient())
result = await pm.analyze_requirements("创建 RAG Agent")
```

### Mock 的优点

1. **不需要 API Key** - 无需配置真实的 LLM API
2. **测试速度快** - 不需要等待网络请求
3. **结果确定** - 每次运行结果相同,便于验证
4. **成本低** - 不消耗 API 调用额度

### Mock 的缺点

1. **不测试 LLM 质量** - 只测试流程,不测试 LLM 输出质量
2. **可能与真实场景不符** - Mock 数据可能过于理想化

### 测试重点

集成测试的重点是验证**模块间的集成**,而不是 LLM 的质量:
- ✅ PM 的输出能否被 GraphDesigner 正确使用?
- ✅ GraphDesigner 的输出能否被 Compiler 正确使用?
- ✅ 数据在各个模块间传递是否正确?

---

## 问题 2: 如何实际运行 DeepEval 测试?

### 为什么测试中不实际运行?

Runner 在测试中只检查配置,不实际执行 pytest,因为:

1. **需要安装 DeepEval** - 测试环境可能没有安装
2. **需要配置 LLM** - DeepEval 需要 LLM 来评估结果
3. **执行时间长** - 实际测试可能需要几分钟

### 如何实际运行 DeepEval 测试?

按照以下步骤操作:

---

## 实际运行步骤

### Step 1: 运行集成测试生成 Agent

```bash
# 运行 Phase 4 集成测试
python tests/integration/test_phase4_integration.py

# 或运行端到端测试
python tests/integration/test_e2e_phase1_to_4.py
```

测试完成后,会显示生成的 Agent 目录,例如:
```
📁 Agent 目录: /tmp/phase4_test_abc123/test_agent/
```

记下这个路径!

---

### Step 2: 进入生成的 Agent 目录

```bash
# 替换为实际的路径
cd /tmp/phase4_test_abc123/test_agent/

# 或 Windows
cd C:\Users\Administrator\AppData\Local\Temp\phase4_test_abc123\test_agent\
```

---

### Step 3: 安装依赖

#### 方式 1: 使用安装脚本 (推荐)

**Linux/Mac**:
```bash
chmod +x install.sh
./install.sh
```

**Windows**:
```cmd
install.bat
```

安装脚本会:
1. 检查 Python 版本
2. 询问是否创建虚拟环境 (建议选择 y)
3. 使用清华镜像源安装所有依赖 (包括 DeepEval)

#### 方式 2: 手动安装

```bash
# 创建虚拟环境 (可选但推荐)
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖 (使用镜像源加速)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

### Step 4: 配置环境变量

创建 `.env` 文件 (基于 `.env.template`):

```bash
# 复制模板
cp .env.template .env

# 编辑 .env 文件
nano .env  # 或使用其他编辑器
```

配置内容:

```bash
# 如果使用 OpenAI
RUNTIME_MODEL=gpt-3.5-turbo
RUNTIME_API_KEY=sk-your-openai-key-here
RUNTIME_BASE_URL=https://api.openai.com/v1

# 如果使用 DeepSeek
RUNTIME_MODEL=deepseek-chat
RUNTIME_API_KEY=sk-your-deepseek-key-here
RUNTIME_BASE_URL=https://api.deepseek.com

# 如果使用 Ollama (本地)
RUNTIME_MODEL=llama3
RUNTIME_API_KEY=dummy
RUNTIME_BASE_URL=http://localhost:11434

# Embedding 配置 (RAG 需要)
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL_NAME=text-embedding-3-small
```

---

### Step 5: 配置 DeepEval Judge LLM

DeepEval 需要一个 LLM 来评估测试结果。

#### 选项 1: 使用 Ollama (本地,免费)

1. **安装 Ollama**:
   ```bash
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Mac
   brew install ollama
   
   # Windows: 下载安装包
   # https://ollama.com/download
   ```

2. **启动 Ollama**:
   ```bash
   ollama serve
   ```

3. **下载模型**:
   ```bash
   ollama pull llama3
   ```

4. **测试文件已配置好** - 生成的 `test_deepeval.py` 已经配置使用 Ollama

#### 选项 2: 使用 OpenAI

修改 `tests/test_deepeval.py` 中的配置:

```python
# 将这部分:
from langchain_community.chat_models import ChatOllama
judge_llm = ChatOllama(
    model="llama3",
    base_url="http://localhost:11434",
    temperature=0.0
)

# 改为:
from langchain_openai import ChatOpenAI
judge_llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    api_key="sk-your-key",
    temperature=0.0
)
```

---

### Step 6: 运行 DeepEval 测试

```bash
# 确保在 Agent 目录中
cd /tmp/phase4_test_abc123/test_agent/

# 运行测试
pytest tests/test_deepeval.py -v -s

# 或生成 JSON 报告
pytest tests/test_deepeval.py --json-report --json-report-file=results.json -v -s
```

---

### Step 7: 查看测试结果

测试运行后,你会看到:

```
tests/test_deepeval.py::test_rag_fact_1 PASSED
tests/test_deepeval.py::test_rag_fact_2 PASSED
tests/test_deepeval.py::test_logic_1 PASSED

==================== 3 passed in 15.2s ====================
```

如果生成了 JSON 报告:
```bash
cat results.json
```

---

## 完整示例流程

```bash
# 1. 运行集成测试
python tests/integration/test_phase4_integration.py

# 2. 进入生成的目录 (替换为实际路径)
cd /tmp/phase4_test_abc123/test_agent/

# 3. 安装依赖
./install.sh  # 选择 y 创建虚拟环境

# 4. 激活虚拟环境
source venv/bin/activate

# 5. 配置 .env
cp .env.template .env
nano .env  # 配置 API Key

# 6. 启动 Ollama (如果使用本地 LLM)
ollama serve &
ollama pull llama3

# 7. 运行 DeepEval 测试
pytest tests/test_deepeval.py -v -s

# 8. 查看结果
echo "测试完成!"
```

---

## 常见问题

### Q1: DeepEval 安装失败?

**A**: 使用镜像源:
```bash
pip install deepeval -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: Ollama 连接失败?

**A**: 检查 Ollama 是否运行:
```bash
curl http://localhost:11434/api/tags
```

### Q3: 测试超时?

**A**: 增加超时时间:
```bash
pytest tests/test_deepeval.py --timeout=300
```

### Q4: API Key 错误?

**A**: 检查 `.env` 文件配置是否正确

---

## 推荐配置

### 开发测试 (快速)
- 使用 Ollama (本地,免费)
- 模型: llama3 或 qwen2.5

### 生产测试 (高质量)
- 使用 OpenAI 或 DeepSeek
- 模型: gpt-4 或 deepseek-chat

---

**创建时间**: 2026-01-15  
**版本**: v1.0
