"""RAG configuration schema."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional


class RAGConfig(BaseModel):
    """RAG configuration schema.
    
    Defines the retrieval-augmented generation strategy including
    text splitting, embedding, vector storage, and retrieval parameters.
    """

    # Text Splitting Configuration
    splitter: Literal["recursive", "character", "token", "semantic"] = Field(
        default="recursive", description="Text splitter type"
    )
    chunk_size: int = Field(
        default=1000, ge=100, le=4000, description="Chunk size in characters"
    )
    chunk_overlap: int = Field(
        default=200, ge=0, le=500, description="Overlap between chunks"
    )
    
    # Vector Store Configuration
    vector_store: Literal["chroma", "faiss", "pgvector"] = Field(
        default="chroma", description="Vector database type"
    )
    persist_directory: str = Field(
        default="./chroma_db", description="Directory to persist vector store"
    )
    collection_name: Optional[str] = Field(
        default=None, description="Collection name (auto-generated if None)"
    )
    
    # Embedding Model Configuration
    embedding_provider: Literal["openai", "huggingface", "ollama"] = Field(
        default="openai", description="Embedding model provider"
    )
    embedding_model_name: str = Field(
        default="text-embedding-3-small", description="Embedding model name"
    )
    embedding_dimension: Optional[int] = Field(
        default=None, description="Embedding dimension (optional)"
    )
    
    # Legacy field for backward compatibility
    embedding_model: str = Field(
        default="openai", description="Embedding model identifier (deprecated, use embedding_provider)"
    )
    
    # Retrieval Configuration
    k_retrieval: int = Field(
        default=5, ge=1, le=20, description="Number of documents to retrieve"
    )
    retriever_type: Literal["basic", "parent_document", "multi_query"] = Field(
        default="basic", description="Retriever type"
    )
    search_type: Literal["similarity", "mmr", "similarity_score_threshold"] = Field(
        default="similarity", description="Search type for retrieval"
    )
    score_threshold: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Minimum similarity score threshold"
    )
    fetch_k: int = Field(
        default=20, ge=1, le=100, description="Number of documents to fetch for MMR"
    )
    lambda_mult: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Diversity parameter for MMR (0=max diversity, 1=max relevance)"
    )
    
    # Reranker Configuration
    reranker_enabled: bool = Field(
        default=False, description="Whether to enable reranking"
    )
    reranker_provider: Optional[Literal["cohere", "bge", "flashrank"]] = Field(
        default=None, description="Reranker provider"
    )
    
    # Hybrid Search Configuration
    enable_hybrid_search: bool = Field(
        default=False, description="Enable hybrid search (BM25 + Vector)"
    )
    bm25_weight: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Weight for BM25 retriever in hybrid search"
    )
    vector_weight: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Weight for vector retriever in hybrid search"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "splitter": "recursive",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "vector_store": "chroma",
                "persist_directory": "./chroma_db",
                "collection_name": "my_docs",
                "embedding_provider": "openai",
                "embedding_model_name": "text-embedding-3-small",
                "embedding_dimension": None,
                "k_retrieval": 5,
                "retriever_type": "basic",
                "search_type": "similarity",
                "score_threshold": None,
                "fetch_k": 20,
                "lambda_mult": 0.5,
                "reranker_enabled": False,
                "reranker_provider": None,
                "enable_hybrid_search": False,
                "bm25_weight": 0.5,
                "vector_weight": 0.5,
            }
        }
    )
