# 测试失败诊断报告

## 🔍 问题分析

### 根本原因
**Embedding 模型配置错误**: Agent 配置使用 Ollama 提供商,但模型名称是 OpenAI 的 `text-embedding-3-small`

### 错误信息
```
ollama._types.ResponseError: model "text-embedding-3-small" not found, 
try pulling it first (status code: 404)
```

### 发生位置
- **文件**: `agents/AgentZero文档助手/agent.py:290`
- **操作**: 初始化向量数据库时尝试嵌入文档
- **时机**: pytest 收集测试时导入 `agent.py`

---

## 📊 当前配置

查看 `agents/AgentZero文档助手/.env`:
```bash
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL_NAME=text-embedding-3-small  # ❌ 错误!
EMBEDDING_BASE_URL=http://localhost:11434
```

**问题**: 
- `text-embedding-3-small` 是 OpenAI 的模型
- Ollama 没有这个模型
- 应该使用 Ollama 的嵌入模型,如 `nomic-embed-text`

---

## ✅ 解决方案

### 方案 1: 使用 Ollama 模型 (推荐)

1. **拉取 Ollama 嵌入模型**:
```bash
ollama pull nomic-embed-text
```

2. **修改 `.env` 文件**:
```bash
cd agents/AgentZero文档助手
# 编辑 .env
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL_NAME=nomic-embed-text  # ✅ 正确的 Ollama 模型
EMBEDDING_BASE_URL=http://localhost:11434
```

3. **重新运行测试**:
```bash
python start.py
# 选择 3 - 重新测试现有 Agent
# 选择 5 - AgentZero文档助手
```

### 方案 2: 切换到 OpenAI Embeddings

如果你有 OpenAI API Key:

```bash
# 编辑 .env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL_NAME=text-embedding-3-small
EMBEDDING_API_KEY=sk-your-openai-key-here
EMBEDDING_BASE_URL=https://api.openai.com/v1
```

---

## 🔧 快速修复脚本

创建 `fix_embedding.py`:
```python
from pathlib import Path

agent_dir = Path("agents/AgentZero文档助手")
env_file = agent_dir / ".env"

# 读取当前配置
content = env_file.read_text(encoding='utf-8')

# 替换模型名称
content = content.replace(
    "EMBEDDING_MODEL_NAME=text-embedding-3-small",
    "EMBEDDING_MODEL_NAME=nomic-embed-text"
)

# 写回
env_file.write_text(content, encoding='utf-8')
print("✅ 已修复 embedding 模型配置")
print("请确保运行: ollama pull nomic-embed-text")
```

运行:
```bash
python fix_embedding.py
ollama pull nomic-embed-text
```

---

## 📈 预期结果

修复后,测试应该能够:
1. ✅ 成功收集测试用例
2. ✅ 初始化向量数据库
3. ✅ 运行 DeepEval 测试
4. ✅ 显示详细的测试结果:
   - 测试名称
   - 通过/失败状态
   - 实际输出 vs 预期输出
   - 评分指标 (Faithfulness, Contextual Recall 等)

---

## 🎯 为什么之前看不到测试结果?

1. **pytest 收集阶段失败**: 
   - pytest 在导入 `test_deepeval.py` 时
   - `test_deepeval.py` 导入 `agent.py`
   - `agent.py` 在模块级别初始化向量数据库
   - 向量数据库初始化失败 → pytest 收集失败
   - 收集失败 → 0 个测试

2. **错误被隐藏**:
   - Runner 捕获了错误但只显示 "0 个测试"
   - 没有显示 pytest 的 stderr 输出

---

## 🔍 改进建议

### 1. 显示 pytest 输出

在 `start.py` 的 retest 功能中添加:
```python
# 显示测试执行详情
if test_results.overall_status == ExecutionStatus.ERROR:
    print("\n❌ 测试执行失败!")
    if hasattr(test_results, 'stderr') and test_results.stderr:
        print("\n错误详情:")
        print(test_results.stderr)
```

### 2. 延迟向量数据库初始化

修改 `agent.py` 不在模块级别初始化,而是在函数内:
```python
# 不要在模块级别
# vectorstore = Chroma(...)  # ❌

# 而是在函数内
def run_agent(user_input: str):
    vectorstore = Chroma(...)  # ✅
    # ...
```

### 3. 添加配置验证

在 Agent 启动时验证配置:
```python
def validate_embedding_config():
    provider = os.getenv("EMBEDDING_PROVIDER")
    model = os.getenv("EMBEDDING_MODEL_NAME")
    
    # 检查模型是否匹配提供商
    if provider == "ollama":
        if model.startswith("text-embedding"):
            raise ValueError(
                f"Ollama 不支持模型 {model}。"
                f"请使用 'nomic-embed-text' 或其他 Ollama 模型"
            )
```

---

## 📝 总结

**当前状态**: 
- ❌ 测试无法运行
- ❌ 看不到测试结果
- ❌ 无法评估 Agent 性能

**修复后**:
- ✅ 测试正常运行
- ✅ 显示详细结果
- ✅ 可以看到改进方向

**立即行动**:
```bash
# 1. 拉取正确的模型
ollama pull nomic-embed-text

# 2. 修改配置
cd agents/AgentZero文档助手
# 编辑 .env: EMBEDDING_MODEL_NAME=nomic-embed-text

# 3. 重新测试
cd ../..
python start.py
# 选择 3, 然后选择 5
```
