# RAG 测试失败原因分析

## 📊 测试结果总览

- **总测试**: 6
- **通过**: 1 (test_basic_response)
- **失败**: 5 (所有 RAG 测试)
- **通过率**: 16.7%

## 🔍 失败原因分析

### 核心问题

**所有 5 个 RAG 测试都因为同一个原因失败**:

```
Contextual Recall (score: 0.0, threshold: 0.8)
Reason: the retrieval context is empty / the context provided is empty
```

### 详细分析

#### 测试 1-3, 5: retrieval_context 完全为空
```
reason: The score is 0.00 because the entire expected output (sentence 1) 
cannot be attributed to any node in the retrieval context, 
as the context provided is empty.
```

#### 测试 4: retrieval_context 有内容,但是**错误的内容**!
```
Faithfulness (score: 0.0)
reason: The score is 0.00 because the actual output describes a systematic 
three-step method for chart design, including defining purposes, processing data, 
and selecting/optimizing chart types with visual elements. 

However, every single point in this description contradicts the retrieval context, 
which exclusively discusses **a writer experiencing writer's block while staring 
at a blank screen**, with no mention of chart design, data processing, or 
visualization steps whatsoever.
```

**这说明检索到了完全不相关的文档!**

## 🎯 问题根源判断

### 不是 Graph Designer 的问题

Graph Designer 生成的图结构是正确的:
- ✅ 有 `agent` 节点
- ✅ 有 `rag_retriever` 节点  
- ✅ 有条件路由 `route_decision`
- ✅ 路由逻辑合理 (检查疑问词)

### 是 Agent 代码实现的问题

问题出在生成的 `agent.py` 中:

#### 问题 1: Trace 保存逻辑

测试代码期望:
```python
# 从 trace 中提取 RAG 检索步骤
rag_steps = [s for s in trace if s.get("action") == "rag_retrieval"]
retrieved_docs = []
if rag_steps:
    docs_file = rag_steps[0].get("docs_file")
    if docs_file:
        with open(docs_file, 'r', encoding='utf-8') as f:
            retrieved_docs = json.load(f)
```

但是 `agent.py` 中:
1. ✅ 有 `TraceManager` 和 `_save_docs_to_file` 函数
2. ✅ `rag_retriever_node` 中调用了 `_save_docs_to_file`
3. ❌ **但是 trace 可能没有正确保存或加载**

#### 问题 2: RAG 节点可能没有被调用

从测试结果看,大部分测试的 `retrieval_context` 是空的,说明:
- 可能路由逻辑没有正确触发 RAG 节点
- 或者 RAG 节点被调用了,但没有正确保存 trace

#### 问题 3: 文档检索可能有问题

测试 4 检索到了错误的文档 ("writer's block"),说明:
- 向量数据库中可能有错误的文档
- 或者检索逻辑有问题

## 🔧 需要检查的地方

### 1. 检查 agent.py 的路由逻辑

查看 `route_decision` 函数是否正确判断需要检索:

```python
def route_decision(state: AgentState) -> str:
    # 检查是否需要知识库（启发式）
    if messages:
        user_query = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                user_query = msg.get("content", "")
                break

        # 简单启发式：包含疑问词或专业术语
        need_kb = any(word in user_query for word in ["什么", "如何", "为什么", "介绍", "解释", "Agent Zero", "项目"])
        if need_kb and not any(msg.get("type") == "tool" for msg in messages if isinstance(msg, dict)):
            return "search"

    return "finish"
```

**问题**: 这个逻辑检查的是 `dict` 类型的消息,但 LangGraph 使用的是 `BaseMessage` 对象!

### 2. 检查 trace 保存逻辑

`rag_retriever_node` 中:
```python
# 保存文档到外部文件
docs_file = _save_docs_to_file(docs, trace_entry["step"])

# 记录 RAG 检索
trace_entry.update({
    "action": "rag_retrieval",
    "docs_file": docs_file,  # 这个路径对吗?
})
_trace_manager.add_entry(trace_entry)
```

需要确认:
- `docs_file` 路径是否正确
- trace 是否正确保存到文件
- `run_agent` 函数是否正确返回 trace

### 3. 检查向量数据库

可能的问题:
- 文档没有正确加载
- 文档被错误地索引
- 检索参数不正确

## 📝 结论

**这不是 Graph Designer 的问题,而是生成的 Agent 代码的问题!**

具体来说:
1. **路由逻辑问题**: 使用了错误的消息类型检查
2. **Trace 保存问题**: 可能没有正确保存或返回 trace
3. **文档检索问题**: 可能检索到了错误的文档

## 🎯 建议修复方向

### 方案 1: 修复 Agent 模板

修改 `src/templates/agent.py.j2`:
1. 修复路由逻辑,正确处理 `BaseMessage` 对象
2. 确保 trace 正确保存和返回
3. 改进文档检索逻辑

### 方案 2: 手动修复现有 Agent

直接修改 `agents/AgentZeroDocAssistant/agent.py`:
1. 修复 `route_decision` 函数
2. 确保 `run_agent` 正确返回 trace
3. 验证向量数据库内容

### 方案 3: 简化测试

修改测试代码,不依赖 trace,直接从 Agent 的返回值中提取信息。

## 🚀 下一步

建议先手动修复现有 Agent,验证修复方案,然后再更新模板。
