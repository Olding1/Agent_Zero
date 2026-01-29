

---

# 🚀 Agent_Zero v7.0 架构演进方案：动态运行时与自进化引擎

## 一、 核心哲学变革 (Core Philosophy Shift)

| 维度 | 旧架构 (v6.0) | **新架构 (v7.0 目标)** |
| :--- | :--- | :--- |
| **配置模式** | **Write-Once (硬编码)** <br> 编译时将参数写入 Python 代码 | **Read-Many (动态加载)** <br> 运行时实时读取 JSON 配置文件 |
| **代码逻辑** | **Conditional Generation** <br> 没开启的功能根本不生成代码 | **Conditional Execution** <br> 生成全量逻辑，通过 Config 开关控制 |
| **进化能力** | **Parameter Tuning** <br> 只能调数字 (k, chunk) | **Architectural Evolution** <br> 可切换架构 (Vector $\to$ Hybrid $\to$ Rerank) |
| **依赖管理** | **Minimal** <br> 只安装当下需要的库 | **Superset (全量)** <br> 预装进阶库，为进化预留空间 |

---

## 二、 实施步骤详解 (Implementation Steps)

### 🟢 第一阶段：运行时配置中心 (The Dynamic Core)
**目标**: 确保优化器修改 `rag_config.json` 后，Agent 下次运行立即生效。

#### 1. 修改 `templates/agent_template.py.j2`
在生成的 `agent.py` 头部增加配置加载模块，并将其注入全局。

```python
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# ... 其他 imports ...

# ==================== 核心：动态配置加载器 ====================
class ConfigLoader:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        
    def load_rag_config(self):
        """每次调用都重新读取文件，确保热更新生效"""
        config_path = self.base_dir / "rag_config.json"
        defaults = {{ rag_config.model_dump_json() }} # 编译时的初始值作为兜底
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    # 深度合并逻辑（可选，这里简单覆盖）
                    return {**defaults, **json.load(f)}
            except Exception as e:
                print(f"⚠️ Config load failed, using defaults: {e}")
        return defaults

# 全局单例
CONFIG_LOADER = ConfigLoader()
# 注意：不要在这里直接赋值 RAG_CONFIG = ...，要在函数内部调用
```

---

### 🔵 第二阶段：弹性检索架构 (The Elastic Retriever)
**目标**: 生成的代码必须包含“混合检索”和“重排序”的**潜能**，即使初始配置是关闭的。

#### 1. 修改 `templates/rag_retriever.py.j2`
废弃大部分 Jinja2 的 `{% if %}` 逻辑，改为 Python 的 `if config.get():` 逻辑。

```python
# templates/rag_retriever.py.j2

def get_retriever():
    """工厂函数：根据当前配置动态构建检索器管道"""
    config = CONFIG_LOADER.load_rag_config()
    
    # 1. 基础向量检索 (Vector Store)
    # ------------------------------------------------
    search_kwargs = {
        "k": config.get("k_retrieval", 4),
        "score_threshold": config.get("score_threshold", 0.5)
    }
    
    # 支持动态切换搜索类型 (Similarity vs MMR)
    search_type = config.get("search_type", "similarity")
    
    base_retriever = vectorstore.as_retriever(
        search_type=search_type,
        search_kwargs=search_kwargs
    )
    
    # 2. 混合检索层 (Hybrid Search Layer)
    # ------------------------------------------------
    # 即使初始没开，代码也存在，优化器只要改 JSON 就能激活
    if config.get("enable_hybrid_search", False):
        try:
            from langchain_community.retrievers import BM25Retriever
            from langchain_classic.retrievers import EnsembleRetriever
            
            # 假设 splits 变量在全局或作为参数传入
            if 'splits' in globals():
                bm25 = BM25Retriever.from_documents(splits)
                bm25.k = config.get("k_retrieval", 4)
                
                base_retriever = EnsembleRetriever(
                    retrievers=[base_retriever, bm25],
                    weights=[
                        config.get("vector_weight", 0.5), 
                        config.get("bm25_weight", 0.5)
                    ]
                )
                print("✅ [RAG] 混合检索已激活 (Vector + BM25)")
        except ImportError:
            print("⚠️ [RAG] 未安装 rank_bm25，降级为纯向量检索")

    # 3. 重排序层 (Reranking Layer)
    # ------------------------------------------------
    if config.get("reranker_enabled", False):
        try:
            from langchain.retrievers import ContextualCompressionRetriever
            from langchain.retrievers.document_compressors import FlashrankRerank
            # 推荐使用 Flashrank，因为它轻量且无需额外 API Key，适合本地化
            
            compressor = FlashrankRerank(
                top_n=config.get("k_retrieval", 4)
            )
            
            final_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=base_retriever
            )
            print("✅ [RAG] 重排序已激活 (Flashrank)")
            return final_retriever
        except ImportError:
             print("⚠️ [RAG] 未安装 flashrank，跳过重排序")
    
    return base_retriever

# 初始化全局 retriever
retriever = get_retriever()
```

#### 2. 修改 `compiler.py` 中的依赖生成
为了支持上述动态切换，`requirements.txt` 必须包含进阶库（Superset Dependency）。

```python
def _generate_requirements(self, ...):
    requirements = [
        # ... 基础库 ...
        "rank_bm25>=0.2.0",      # 预装，为了支持混合检索
        "flashrank>=0.2.0",      # 预装，为了支持本地 Rerank
        "langchain_community",
        # ...
    ]
```

---

### 🟠 第三阶段：大脑升级 (Optimizer Upgrade)
**目标**: 教会 `RAGOptimizer` 使用新获得的架构切换能力。

#### 1. 修改 `src/core/rag_optimizer.py`

**Prompt 升级**:
```python
prompt = f"""
...
## 优化策略指南 (Strategy Guide)

1. **解决召回率 (Recall) 为 0 的问题**:
   - 增加 `k_retrieval` (例如 20+)。
   - **必须** 启用混合检索: 将 `enable_hybrid_search` 设为 true。
   - **必须** 增大 `chunk_size` (例如 800-1200)。

2. **解决准确率 (Faithfulness/Precision) 低的问题**:
   - **必须** 启用重排序: 将 `reranker_enabled` 设为 true。
   - 减小 `chunk_size` (例如 400-600) 以减少噪音。

3. **禁止的操作**:
   - 不要修改 vector_store 类型 (chroma/faiss)。

请输出完整的 JSON 配置。
"""
```

**启发式规则 (Heuristic) 升级**:
```python
# rag_optimizer.py

def optimize_config(self, ...):
    # ...
    
    # 规则 1: 绝境求生 (Recall=0 -> 开大招)
    if "recall" in analysis.primary_issue.lower() and test_report.pass_rate < 0.2:
        print("⚡ 检测到召回率极低，强制激活混合检索架构")
        new_config.enable_hybrid_search = True
        new_config.k_retrieval = 30
        new_config.chunk_size = 1000

    # 规则 2: 精益求精 (Pass > 0.5 但 Faithfulness 低 -> 开 Rerank)
    if test_report.pass_rate > 0.5 and avg_faithfulness < 0.6:
        print("⚡ 检测到准确度不足，强制激活重排序")
        new_config.reranker_enabled = True
        new_config.k_retrieval = 15 # Rerank 需要较大的候选集
        
    # ...
```

---

### 🟣 第四阶段：配套设施升级 (Supporting Infra)

这些是我们之前讨论过的，配合上述改动：

1.  **uv 集成**: 
    由于我们预装了 `flashrank` 和 `rank_bm25`，安装时间会变长。必须使用 `uv pip install` 保证体验。

2.  **Trace 可视化**: 
    由于 `retriever` 变成了动态管道，你的 Trace JSON 需要记录当前的架构状态。
    在 `agent.py` 的 Trace 中增加：
    ```python
    trace_entry.update({
        "rag_architecture": {
            "hybrid": RAG_CONFIG.get("enable_hybrid_search"),
            "rerank": RAG_CONFIG.get("reranker_enabled"),
            "k": RAG_CONFIG.get("k_retrieval")
        }
    })
    ```

---

## 三、 演进路线图 (Timeline)

建议按以下顺序落地，每一步都是可测试的闭环：

1.  **Step 1: 动态化改造 (Day 1)**
    *   完成 **Phase 1** (ConfigLoader)。
    *   验证：修改 `rag_config.json`，不重新编译，直接运行 `agent.py`，打印出参数变化。

2.  **Step 2: 弹性骨架 (Day 2)**
    *   完成 **Phase 2** (Python logic in Templates)。
    *   修改 `compiler.py` 加入 `rank_bm25` 等依赖。
    *   验证：手动在 JSON 里把 `enable_hybrid_search` 改为 true，运行 Agent，看日志里是否有 `[RAG] 混合检索已激活`。

3.  **Step 3: 智商充值 (Day 3)**
    *   完成 **Phase 3** (Optimizer Prompt & Rules)。
    *   验证：跑一次完整的 `Iteration`，观察 Log。当 Recall=0 时，Optimizer 是否主动开启了 Hybrid Search。

4.  **Step 4: 性能与体验 (Day 4)**
    *   集成 `uv`。
    *   集成 `ARS` (PM 模块) 提升初始生成的质量。

这是一个**治标又治本**的长远方案。它不仅修复了当前的迭代 bug，还赋予了你的 Agent 在未来“自行升级装备”的能力。