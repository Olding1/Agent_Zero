# Agent Zero - 完整 RAG 系统实施计划

**目标**: 补充完整的 RAG (检索增强生成) 功能,使生成的 Agent 具备真正的向量检索能力

**当前状态**: RAG 策略设计完成,但缺少核心的向量化和检索实现

**预计时间**: 2-3 周

---

## 📊 现状分析

### ✅ 已完成

- RAG Builder: 智能策略设计
- Profiler: 文档特征分析
- RAGConfig Schema: 完整的配置定义
- 基础模板: agent_template.py.j2 框架

### ❌ 缺失核心功能

```
完整 RAG 流程:
┌─────────────────────────────────────────────────────────┐
│ 1. 文档加载 (Unstructured/PyPDF)           ✅ 部分支持 │
│ 2. 文档切分 (Chunking)                     ✅ 配置完成 │
│ 3. 向量化 (Embedding)                      ❌ 未实现   │
│ 4. 向量存储 (Vector Store)                 ❌ 未实现   │
│ 5. 查询向量化                               ❌ 未实现   │
│ 6. 向量检索 (Retrieval)                    ❌ 未实现   │
│ 7. 混合检索 (Hybrid Search)                ❌ 未实现   │
│ 8. 重排序 (Rerank)                         ❌ 未实现   │
│ 9. 上下文拼接 + LLM 生成                    ✅ 已有     │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 实施目标

### 阶段 2.5: RAG 核心功能补充 (Week 5-6)

**目标**: 实现基础但完整的 RAG 功能

**验收标准**:
- ✅ 生成的 Agent 能加载文档并向量化
- ✅ 能存储向量到 ChromaDB
- ✅ 能根据用户问题进行向量检索
- ✅ 能返回相关文档片段
- ✅ 能基于检索结果生成答案

---

## 📋 详细实施计划

### Week 5: 基础 RAG 实现

#### Day 1-2: 更新 Schema 和配置

**任务 1.1: 扩展 RAGConfig Schema**

**文件**: `src/schemas/rag_config.py`

**新增字段**:
```python
class RAGConfig(BaseModel):
    # 现有字段
    splitter: Literal["recursive", "character", "token", "semantic"]
    chunk_size: int
    chunk_overlap: int
    k_retrieval: int
    embedding_model: str
    retriever_type: Literal["basic", "parent_document", "multi_query"]
    reranker_enabled: bool
    
    # 新增字段
    vector_store: Literal["chroma", "faiss", "pgvector"] = "chroma"
    persist_directory: str = "./chroma_db"
    collection_name: Optional[str] = None
    
    # 嵌入模型详细配置
    embedding_provider: Literal["openai", "huggingface", "ollama"] = "openai"
    embedding_model_name: str = "text-embedding-3-small"
    embedding_dimension: Optional[int] = None
    
    # 检索配置
    search_type: Literal["similarity", "mmr", "similarity_score_threshold"] = "similarity"
    score_threshold: Optional[float] = None
    fetch_k: int = 20  # MMR 使用
    lambda_mult: float = 0.5  # MMR 多样性参数
    
    # 混合检索
    enable_hybrid_search: bool = False
    bm25_weight: float = 0.5
    vector_weight: float = 0.5
```

**验收**: Schema 验证通过,能正确序列化/反序列化

---

**任务 1.2: 更新 requirements.txt 生成逻辑**

**文件**: `src/core/compiler.py`

**修改**: `_generate_requirements()` 方法

**新增依赖**:
```python
if has_rag:
    requirements.extend([
        "",
        "# RAG dependencies",
        "chromadb>=0.4.22",
        "langchain-community>=0.2.0",
        "langchain-openai>=0.1.0",
        "pypdf>=3.17.0",
        "python-docx>=1.1.0",
        "tiktoken>=0.5.0",  # Token 计数
    ])
    
    # 根据 embedding_provider 添加依赖
    if rag_config.embedding_provider == "huggingface":
        requirements.append("sentence-transformers>=2.2.0")
    elif rag_config.embedding_provider == "ollama":
        requirements.append("langchain-ollama>=0.1.0")
```

**验收**: 生成的 requirements.txt 包含所有必要依赖

---

#### Day 3-4: 创建 RAG 模板组件

**任务 2.1: 创建嵌入模型模板**

**文件**: `src/templates/rag_embedding.py.j2`

**内容**:
```jinja2
# 嵌入模型初始化
{% if rag_config.embedding_provider == "openai" %}
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="{{ rag_config.embedding_model_name }}",
    {% if rag_config.embedding_dimension %}
    dimensions={{ rag_config.embedding_dimension }},
    {% endif %}
)

{% elif rag_config.embedding_provider == "huggingface" %}
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="{{ rag_config.embedding_model_name }}",
    model_kwargs={'device': 'cpu'},  # 或 'cuda'
    encode_kwargs={'normalize_embeddings': True}
)

{% elif rag_config.embedding_provider == "ollama" %}
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="{{ rag_config.embedding_model_name }}",
)

{% endif %}
```

**验收**: 模板能正确渲染不同的嵌入模型配置

---

**任务 2.2: 创建向量存储模板**

**文件**: `src/templates/rag_vectorstore.py.j2`

**内容**:
```jinja2
# 向量数据库初始化
{% if rag_config.vector_store == "chroma" %}
from langchain_community.vectorstores import Chroma

vectorstore = Chroma(
    collection_name="{{ rag_config.collection_name or agent_name + '_docs' }}",
    embedding_function=embeddings,
    persist_directory="{{ rag_config.persist_directory }}"
)

{% elif rag_config.vector_store == "faiss" %}
from langchain_community.vectorstores import FAISS

# FAISS 需要先加载文档后创建
vectorstore = None  # 将在文档加载后初始化

{% elif rag_config.vector_store == "pgvector" %}
from langchain_community.vectorstores import PGVector

CONNECTION_STRING = os.getenv("PGVECTOR_CONNECTION_STRING")
vectorstore = PGVector(
    collection_name="{{ rag_config.collection_name or agent_name + '_docs' }}",
    connection_string=CONNECTION_STRING,
    embedding_function=embeddings,
)

{% endif %}
```

**验收**: 模板能正确渲染不同的向量数据库配置

---

**任务 2.3: 创建文档加载模板**

**文件**: `src/templates/rag_document_loader.py.j2`

**内容**:
```jinja2
# 文档加载和处理
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
)
from pathlib import Path

def load_documents(file_paths: list[str]) -> list:
    """加载多个文档"""
    documents = []
    
    for file_path in file_paths:
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"Warning: File not found: {file_path}")
            continue
        
        # 根据文件类型选择加载器
        if file_path.suffix.lower() == '.pdf':
            loader = PyPDFLoader(str(file_path))
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            loader = Docx2txtLoader(str(file_path))
        elif file_path.suffix.lower() == '.md':
            loader = UnstructuredMarkdownLoader(str(file_path))
        elif file_path.suffix.lower() == '.txt':
            loader = TextLoader(str(file_path))
        else:
            print(f"Warning: Unsupported file type: {file_path.suffix}")
            continue
        
        try:
            docs = loader.load()
            documents.extend(docs)
            print(f"Loaded {len(docs)} documents from {file_path.name}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return documents

def split_documents(documents: list) -> list:
    """切分文档"""
    {% if rag_config.splitter == "recursive" %}
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size={{ rag_config.chunk_size }},
        chunk_overlap={{ rag_config.chunk_overlap }},
        length_function=len,
    )
    {% elif rag_config.splitter == "character" %}
    text_splitter = CharacterTextSplitter(
        chunk_size={{ rag_config.chunk_size }},
        chunk_overlap={{ rag_config.chunk_overlap }},
    )
    {% elif rag_config.splitter == "token" %}
    text_splitter = TokenTextSplitter(
        chunk_size={{ rag_config.chunk_size }},
        chunk_overlap={{ rag_config.chunk_overlap }},
    )
    {% endif %}
    
    splits = text_splitter.split_documents(documents)
    print(f"Split into {len(splits)} chunks")
    return splits

# 加载和处理文档
{% if file_paths %}
print("Loading documents...")
documents = load_documents({{ file_paths }})

print("Splitting documents...")
splits = split_documents(documents)

print("Creating vector store...")
{% if rag_config.vector_store == "faiss" %}
# FAISS 需要从文档创建
from langchain_community.vectorstores import FAISS
vectorstore = FAISS.from_documents(splits, embeddings)
vectorstore.save_local("{{ rag_config.persist_directory }}")
{% else %}
# ChromaDB/PGVector 直接添加
vectorstore.add_documents(splits)
{% endif %}

print(f"Indexed {len(splits)} document chunks")
{% endif %}
```

**验收**: 能正确加载不同格式的文档并切分

---

**任务 2.4: 创建检索器模板**

**文件**: `src/templates/rag_retriever.py.j2`

**内容**:
```jinja2
# 检索器配置
{% if rag_config.retriever_type == "basic" %}
# 基础检索器
retriever = vectorstore.as_retriever(
    search_type="{{ rag_config.search_type }}",
    search_kwargs={
        "k": {{ rag_config.k_retrieval }},
        {% if rag_config.search_type == "similarity_score_threshold" %}
        "score_threshold": {{ rag_config.score_threshold or 0.5 }},
        {% elif rag_config.search_type == "mmr" %}
        "fetch_k": {{ rag_config.fetch_k }},
        "lambda_mult": {{ rag_config.lambda_mult }},
        {% endif %}
    }
)

{% elif rag_config.retriever_type == "parent_document" %}
# 父文档检索器
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 父文档存储
parent_store = InMemoryStore()

# 子文档分割器 (更小的块用于检索)
child_splitter = RecursiveCharacterTextSplitter(
    chunk_size={{ rag_config.chunk_size // 2 }},
    chunk_overlap={{ rag_config.chunk_overlap // 2 }},
)

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=parent_store,
    child_splitter=child_splitter,
    search_kwargs={"k": {{ rag_config.k_retrieval }}},
)

{% elif rag_config.retriever_type == "multi_query" %}
# 多查询检索器
from langchain.retrievers.multi_query import MultiQueryRetriever

base_retriever = vectorstore.as_retriever(
    search_kwargs={"k": {{ rag_config.k_retrieval }}}
)

retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=llm,
)

{% endif %}

{% if rag_config.enable_hybrid_search %}
# 混合检索 (向量 + BM25)
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# BM25 检索器
bm25_retriever = BM25Retriever.from_documents(splits)
bm25_retriever.k = {{ rag_config.k_retrieval }}

# 组合检索器
retriever = EnsembleRetriever(
    retrievers=[retriever, bm25_retriever],
    weights=[{{ rag_config.vector_weight }}, {{ rag_config.bm25_weight }}]
)
{% endif %}

{% if rag_config.reranker_enabled %}
# 重排序
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import CohereRerank

compressor = CohereRerank(
    model="rerank-english-v2.0",
    top_n={{ rag_config.k_retrieval }}
)

retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever
)
{% endif %}
```

**验收**: 能正确配置不同类型的检索器

---

**任务 2.5: 创建 RAG Chain 模板**

**文件**: `src/templates/rag_chain.py.j2`

**内容**:
```jinja2
# RAG Chain
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# RAG Prompt
rag_prompt_template = """使用以下上下文来回答问题。如果你不知道答案,就说不知道,不要试图编造答案。

上下文:
{context}

问题: {question}

回答:"""

RAG_PROMPT = PromptTemplate(
    template=rag_prompt_template,
    input_variables=["context", "question"]
)

# 创建 RAG Chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",  # 或 "map_reduce", "refine"
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": RAG_PROMPT}
)

def ask_question(question: str) -> dict:
    """使用 RAG 回答问题"""
    result = qa_chain({"query": question})
    
    return {
        "answer": result["result"],
        "sources": [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in result["source_documents"]
        ]
    }
```

**验收**: RAG Chain 能正确执行检索和生成

---

#### Day 5: 集成到主模板

**任务 3.1: 更新 agent_template.py.j2**

**文件**: `src/templates/agent_template.py.j2`

**修改**: 在主模板中集成所有 RAG 组件

**结构**:
```jinja2
#!/usr/bin/env python3
"""
{{ agent_name }} - Generated by Agent Zero
Description: {{ description }}
Generated at: {{ timestamp }}
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# LLM 初始化
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model=os.getenv("RUNTIME_MODEL", "gpt-3.5-turbo"),
    temperature=float(os.getenv("TEMPERATURE", "0.7")),
)

{% if has_rag %}
# ============================================================================
# RAG 组件
# ============================================================================

{% include 'rag_embedding.py.j2' %}

{% include 'rag_vectorstore.py.j2' %}

{% include 'rag_document_loader.py.j2' %}

{% include 'rag_retriever.py.j2' %}

{% include 'rag_chain.py.j2' %}

{% endif %}

# ============================================================================
# 主程序
# ============================================================================

def main():
    print("=" * 60)
    print(f"🤖 {{ agent_name }}")
    print("=" * 60)
    print()
    
    {% if has_rag %}
    print("RAG 模式已启用")
    print(f"向量数据库: {{ rag_config.vector_store }}")
    print(f"嵌入模型: {{ rag_config.embedding_model_name }}")
    print(f"检索器类型: {{ rag_config.retriever_type }}")
    print()
    {% endif %}
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        try:
            {% if has_rag %}
            # 使用 RAG
            result = ask_question(user_input)
            print(f"\nAgent: {result['answer']}\n")
            
            # 显示来源
            if result['sources']:
                print("📚 来源:")
                for i, source in enumerate(result['sources'][:3], 1):
                    print(f"{i}. {source['content'][:100]}...")
                print()
            {% else %}
            # 直接使用 LLM
            response = llm.invoke(user_input)
            print(f"\nAgent: {response.content}\n")
            {% endif %}
            
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()
```

**验收**: 生成的 agent.py 包含完整的 RAG 功能

---

#### Day 6-7: 测试和优化

**任务 4.1: 创建 RAG 单元测试**

**文件**: `tests/unit/test_rag_components.py`

**测试内容**:
```python
import pytest
from pathlib import Path
import tempfile

def test_rag_config_validation():
    """测试 RAGConfig 验证"""
    from src.schemas import RAGConfig
    
    config = RAGConfig(
        splitter="recursive",
        chunk_size=1000,
        chunk_overlap=200,
        k_retrieval=5,
        embedding_model="openai",
        retriever_type="basic",
        reranker_enabled=False,
    )
    
    assert config.chunk_size == 1000
    assert config.splitter == "recursive"

def test_embedding_template_rendering():
    """测试嵌入模型模板渲染"""
    from jinja2 import Environment, FileSystemLoader
    
    env = Environment(loader=FileSystemLoader("src/templates"))
    template = env.get_template("rag_embedding.py.j2")
    
    # 测试 OpenAI
    result = template.render(
        rag_config={
            "embedding_provider": "openai",
            "embedding_model_name": "text-embedding-3-small"
        }
    )
    
    assert "OpenAIEmbeddings" in result
    assert "text-embedding-3-small" in result

# 更多测试...
```

**验收**: 所有单元测试通过

---

**任务 4.2: 创建 RAG E2E 测试**

**文件**: `tests/e2e/test_rag_full_pipeline.py`

**测试流程**:
```python
async def test_rag_full_pipeline():
    """测试完整的 RAG 流程"""
    
    # 1. 创建测试文档
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Agent Zero 是一个智能体构建工厂。它可以自动生成 Agent。")
        test_file = Path(f.name)
    
    # 2. PM 分析需求
    pm = PM(builder_client)
    project_meta = await pm.analyze_requirements(
        "创建一个能回答 Agent Zero 相关问题的助手",
        file_paths=[test_file]
    )
    
    assert project_meta.has_rag is True
    
    # 3. Profiler 分析文档
    profiler = Profiler()
    data_profile = profiler.analyze([test_file])
    
    # 4. RAG Builder 设计策略
    rag_builder = RAGBuilder(builder_client)
    rag_config = await rag_builder.design_rag_strategy(data_profile)
    
    # 5. 编译生成 Agent
    compiler = Compiler(template_dir=Path("src/templates"))
    output_dir = Path("agents/rag_test")
    
    result = compiler.compile(
        project_meta=project_meta,
        graph=graph_structure,
        rag_config=rag_config,
        tools_config=ToolsConfig(enabled_tools=[]),
        output_dir=output_dir
    )
    
    assert result.success
    assert (output_dir / "agent.py").exists()
    
    # 6. 验证生成的代码包含 RAG 组件
    agent_code = (output_dir / "agent.py").read_text()
    assert "embeddings" in agent_code
    assert "vectorstore" in agent_code
    assert "retriever" in agent_code
    assert "qa_chain" in agent_code
    
    # 7. 设置环境
    env_manager = EnvManager(output_dir)
    await env_manager.setup_environment()
    
    # 8. 运行 Agent 并测试
    # (需要实际运行生成的 agent.py)
    
    print("✅ RAG Full Pipeline Test PASSED!")
```

**验收**: E2E 测试通过,生成的 Agent 能正确回答问题

---

### Week 6: 高级 RAG 功能

#### Day 8-9: 混合检索实现

**任务 5.1: 实现 BM25 检索器**

**文件**: `src/templates/rag_retriever.py.j2` (扩展)

**新增内容**:
```jinja2
{% if rag_config.enable_hybrid_search %}
# BM25 检索器 (关键词检索)
from langchain_community.retrievers import BM25Retriever
from rank_bm25 import BM25Okapi
import jieba  # 中文分词

def tokenize_chinese(text: str) -> list[str]:
    """中文分词"""
    return list(jieba.cut(text))

# 创建 BM25 检索器
bm25_retriever = BM25Retriever.from_documents(
    splits,
    preprocess_func=tokenize_chinese if "{{ language }}" == "zh-CN" else None
)
bm25_retriever.k = {{ rag_config.k_retrieval }}

# 组合检索器 (RRF 融合)
from langchain.retrievers import EnsembleRetriever

ensemble_retriever = EnsembleRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    weights=[{{ rag_config.vector_weight }}, {{ rag_config.bm25_weight }}]
)

retriever = ensemble_retriever
{% endif %}
```

**新增依赖**:
```
rank-bm25>=0.2.2
jieba>=0.42.1  # 中文分词
```

**验收**: 混合检索能提高准确率

---

**任务 5.2: 实现重排序**

**文件**: `src/templates/rag_retriever.py.j2` (扩展)

**支持多种 Reranker**:
```jinja2
{% if rag_config.reranker_enabled %}
from langchain.retrievers import ContextualCompressionRetriever

{% if rag_config.reranker_provider == "cohere" %}
# Cohere Rerank
from langchain_community.document_compressors import CohereRerank

compressor = CohereRerank(
    model="rerank-english-v2.0",
    top_n={{ rag_config.k_retrieval }}
)

{% elif rag_config.reranker_provider == "bge" %}
# BGE Reranker (本地)
from langchain_community.document_compressors import HuggingFaceBgeRerank

compressor = HuggingFaceBgeRerank(
    model_name="BAAI/bge-reranker-v2-m3",
    top_n={{ rag_config.k_retrieval }}
)

{% endif %}

retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever
)
{% endif %}
```

**验收**: Rerank 能提高 Top-K 结果的相关性

---

#### Day 10-11: 多向量数据库支持

**任务 6.1: 支持 Qdrant**

**文件**: `src/templates/rag_vectorstore.py.j2` (扩展)

**新增内容**:
```jinja2
{% elif rag_config.vector_store == "qdrant" %}
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient

# Qdrant 客户端
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

vectorstore = Qdrant(
    client=qdrant_client,
    collection_name="{{ rag_config.collection_name or agent_name + '_docs' }}",
    embeddings=embeddings,
)
{% endif %}
```

**验收**: 能使用 Qdrant 作为向量数据库

---

**任务 6.2: 支持 Milvus**

**新增内容**:
```jinja2
{% elif rag_config.vector_store == "milvus" %}
from langchain_community.vectorstores import Milvus

vectorstore = Milvus(
    embedding_function=embeddings,
    collection_name="{{ rag_config.collection_name or agent_name + '_docs' }}",
    connection_args={
        "host": os.getenv("MILVUS_HOST", "localhost"),
        "port": os.getenv("MILVUS_PORT", "19530"),
    },
)
{% endif %}
```

**验收**: 能使用 Milvus 作为向量数据库

---

#### Day 12-13: 文档和示例

**任务 7.1: 更新用户指南**

**文件**: `docs/RAG_GUIDE.md`

**内容**:
```markdown
# Agent Zero RAG 使用指南

## 什么是 RAG

RAG (Retrieval-Augmented Generation) 是一种结合检索和生成的技术...

## 如何使用

### 1. 准备文档
支持的格式: PDF, DOCX, TXT, MD

### 2. 创建 RAG Agent
```bash
python start.py
# 选择创建 Agent
# 上传文档
# 系统自动配置 RAG
```

### 3. 配置选项
- 嵌入模型: OpenAI, BGE-M3, Ollama
- 向量数据库: ChromaDB, Qdrant, Milvus
- 检索器: 基础, 父文档, 多查询
- 混合检索: 向量 + BM25
- 重排序: Cohere, BGE

## 最佳实践
...
```

**验收**: 文档清晰易懂

---

**任务 7.2: 创建示例 Agent**

**文件**: `examples/rag_agent_example.py`

**内容**: 完整的 RAG Agent 使用示例

**验收**: 示例能正常运行

---

#### Day 14: 性能优化和测试

**任务 8.1: 性能优化**

**优化点**:
1. 向量化批处理
2. 检索结果缓存
3. 延迟加载向量数据库
4. 异步检索

**验收**: 响应时间 < 2 秒

---

**任务 8.2: 全面测试**

**测试场景**:
1. 单文档 RAG
2. 多文档 RAG
3. 大文档 RAG (>100 页)
4. 混合检索
5. 重排序
6. 不同嵌入模型
7. 不同向量数据库

**验收**: 所有场景测试通过

---

## 📊 验收标准

### 功能验收

- [ ] 能加载 PDF/DOCX/TXT/MD 文档
- [ ] 能正确切分文档
- [ ] 能向量化文档并存储
- [ ] 能根据问题检索相关文档
- [ ] 能基于检索结果生成答案
- [ ] 支持至少 2 种嵌入模型
- [ ] 支持至少 2 种向量数据库
- [ ] 支持混合检索 (可选)
- [ ] 支持重排序 (可选)

### 性能验收

- [ ] 文档索引时间 < 1 分钟 (100 页)
- [ ] 检索响应时间 < 2 秒
- [ ] 准确率 > 80% (基准测试集)

### 代码质量

- [ ] 所有模板能正确渲染
- [ ] 生成的代码符合 PEP 8
- [ ] 单元测试覆盖率 > 70%
- [ ] E2E 测试通过
- [ ] 文档完整

---

## 🔄 后续优化 (Week 7+)

### 高级功能

1. **GraphRAG**
   - 实体提取
   - 关系构建
   - 图谱检索

2. **Agentic RAG**
   - Self-RAG (自我反思)
   - Adaptive RAG (自适应检索)
   - 查询重写

3. **多模态 RAG**
   - 图片检索
   - 表格理解
   - OCR 集成

4. **增量更新**
   - 文档增量索引
   - 向量数据库更新
   - 版本管理

### 性能优化

1. **缓存机制**
   - 查询缓存
   - 嵌入缓存
   - 结果缓存

2. **并行处理**
   - 批量向量化
   - 并行检索
   - 异步处理

3. **资源优化**
   - 内存管理
   - GPU 加速
   - 模型量化

---

## 📈 里程碑

### Week 5 结束
- ✅ 基础 RAG 功能完成
- ✅ 支持 ChromaDB + OpenAI Embeddings
- ✅ E2E 测试通过

### Week 6 结束
- ✅ 混合检索实现
- ✅ 重排序实现
- ✅ 多向量数据库支持
- ✅ 文档完善

### Week 7+ (可选)
- ✅ GraphRAG
- ✅ Agentic RAG
- ✅ 性能优化

---

## 🎯 成功指标

**技术指标**:
- 检索准确率: > 80%
- 响应时间: < 2 秒
- 支持文档格式: 4+ 种
- 支持嵌入模型: 3+ 种
- 支持向量数据库: 3+ 种

**用户体验**:
- 一键生成 RAG Agent
- 自动配置最佳策略
- 清晰的错误提示
- 完善的文档

**代码质量**:
- 测试覆盖率: > 70%
- 代码可维护性: 高
- 模块化程度: 高
- 文档完整性: 高

---

## 📚 参考资料

1. **LangChain RAG 文档**
   - https://python.langchain.com/docs/use_cases/question_answering/

2. **向量数据库对比**
   - ChromaDB: 轻量级,易用
   - Qdrant: 高性能,Rust 编写
   - Milvus: 大规模,企业级

3. **嵌入模型选择**
   - OpenAI: 效果好,成本高
   - BGE-M3: 中文强,开源
   - Ollama: 本地部署,隐私

4. **最佳实践**
   - Hybrid Search 必须上
   - Rerank 提升 10-20%
   - Chunk size 根据场景调整

---

**开始实施!** 🚀
