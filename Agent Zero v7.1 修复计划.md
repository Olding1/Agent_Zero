这是一个**完整、彻底的 Agent Zero v7.1 修复计划 (已修正)**。

你的判断完全正确：**必须加上** Schema 修复和优化器策略升级。但为了彻底解决 83.3% 的卡顿，我们必须补上最关键的一环——**自动清除脏数据（Cache Invalidation）**。

如果不做数据清除，你的优化器（大脑）再聪明，读的也是旧书（旧 Chunk）。

以下是按优先级排序的 **4 步修复方案**：

---

### 🛠️ 第一步：修复 Graph Schema (解锁智力上限)
**目标**：允许 Agent 在进化中增加新的变量类型（如评分 `float`），防止报错。

**文件**: `src/schemas/state_schema.py`

```python
from enum import Enum

class StateFieldType(str, Enum):
    # ... 原有类型 ...
    FLOAT = "float"
    LIST_MESSAGE = "List[BaseMessage]"
    # ...
    OPTIONAL_STR = "Optional[str]"
    OPTIONAL_INT = "Optional[int]"
    OPTIONAL_FLOAT = "Optional[float]" # ✅ 新增: 允许存 0.85 这种分数
    OPTIONAL_DICT = "Optional[Dict[str, Any]]"   # ✅ 新增: 允许存复杂结果
    ANY = "Any"
```

---

### � 第二步：实现自动脏数据清洗 (核心修复)
**目标**：当 Config 变化（如 `chunk_size` 改变）时，自动删除旧的向量库，强制重新索引。**这是解决 83.3% 卡顿的关键。**

**文件**: `src/templates/rag_vectorstore.py.j2`

我们要在生成向量库代码时，加入**配置哈希比对**逻辑。

```python
import shutil
import hashlib
import json
from pathlib import Path

# ... 原有的 imports ...

def get_config_hash(config):
    """计算关键配置的指纹"""
    # 只关注会影响索引结构的参数
    key_params = {
        "chunk_size": config.get("chunk_size"),
        "chunk_overlap": config.get("chunk_overlap"),
        "splitter": config.get("splitter"),
        "embedding_model": config.get("embedding_model_name")
    }
    return hashlib.md5(json.dumps(key_params, sort_keys=True).encode()).hexdigest()

def init_vectorstore():
    persist_dir = "{{ rag_config.persist_directory or './chroma_db' }}"
    config_hash_file = Path(persist_dir) / "config.hash"
    
    current_hash = get_config_hash(RAG_CONFIG)
    
    # 检查是否需要重建
    should_rebuild = False
    if Path(persist_dir).exists():
        if not config_hash_file.exists():
            should_rebuild = True # 旧版本没有 hash 文件，重建
        else:
            stored_hash = config_hash_file.read_text().strip()
            if stored_hash != current_hash:
                print(f"♻️ [RAG] 配置变更检测 (Hash不匹配)，正在重建向量库...")
                should_rebuild = True
    
    if should_rebuild and Path(persist_dir).exists():
        try:
            shutil.rmtree(persist_dir) # 🗑️ 删掉旧库
            print("✅ 旧向量库已清除")
        except Exception as e:
            print(f"⚠️ 清除旧库失败: {e}")

    # ... 原有的 Chroma 初始化代码 ...
    # 记得在创建完 vectorstore 后写入新的 hash
    if not config_hash_file.exists():
         # 确保目录存在
         Path(persist_dir).mkdir(parents=True, exist_ok=True)
         config_hash_file.write_text(current_hash)
    
    return vectorstore

vectorstore = init_vectorstore()
```

---

### 🔗 第三步：修复 Hybrid Search 空转问题
**目标**：确保即使向量库已存在，BM25 也能正确加载所有文档进行统计。

**文件**: `src/templates/rag_document_loader.py.j2`

**核心逻辑修正**: 
1. **始终执行** `load_documents` 和 `split_documents`（建立 splits 列表）。
2. **仅当** 向量库需要重建（或为空）时，才执行 `vectorstore.add_documents`。
3. `BM25Retriever` 始终使用完整的 `splits` 初始化。

```python
# 1. 始终加载和分割文档 (为了 BM25)
print("📚 Loading documents for Hybrid Search...")
documents = load_documents(file_paths)
splits = split_documents(documents)

# 2. 只有在向量库需要更新时才写入
if vectorstore._collection.count() == 0:
    print("Writing to vector store...")
    vectorstore.add_documents(splits)
else:
    print("Vector store up to date.")

# 3. 确保 splits 变量在全局可用，供 rag_retriever 使用
```

---

### 🧠 第四步：升级优化器策略 (停止盲目调参)
**目标**：教优化器在绝境（Recall=0）时不要只会加 K，要懂得“变通”。

**文件**: `src/core/rag_optimizer.py`

**修改 `_llm_optimize` 函数中的 Prompt**:

```python
prompt = f"""
...
## 极端情况处理指南 (Emergency Protocol):

1. **如果 Contextual Recall 依然为 0.0**:
   - 检查 `k_retrieval`: 如果已经 > 30，**停止增加 K 值**（噪音太大）。
   - **强烈建议**: 将 `chunk_size` 调整到 1000 以上（保留完整语义）或者 300 以下（精准匹配）。
   - **必须**: 在 `reasoning` 中指出："可能需要 Graph Designer 增强 query_rewriter 的 Prompt，或者检查源文档解析是否丢失数据"。

2. **如果 Faithfulness 为 0.0**:
   - 必须启用 `reranker_enabled`。
   - 减小 `chunk_size`。

请输出 JSON 配置...
"""
```

---

### 🚀 执行总结

1.  **Step 1 (Schema)**: 修正类型定义，防止报错。
2.  **Step 2 (Data Cleaning)**: 实现 Hash 校验，解决配置不生效问题。
3.  **Step 3 (Hybrid Fix)**: 确保 BM25 始终有效。
4.  **Step 4 (Optimizer)**: 提升优化智力。

把这四步做完，你的 Agent Zero v7.1 就真正修复完成了。