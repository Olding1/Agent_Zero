"""RAG configuration schema."""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class RAGConfig(BaseModel):
    """RAG configuration schema.
    
    Defines the retrieval-augmented generation strategy including
    text splitting, embedding, and retrieval parameters.
    """

    splitter: Literal["recursive", "character", "token", "semantic"] = Field(
        default="recursive", description="Text splitter type"
    )
    chunk_size: int = Field(
        default=1000, ge=100, le=4000, description="Chunk size in characters"
    )
    chunk_overlap: int = Field(
        default=200, ge=0, le=500, description="Overlap between chunks"
    )
    k_retrieval: int = Field(
        default=5, ge=1, le=20, description="Number of documents to retrieve"
    )
    embedding_model: str = Field(
        default="openai", description="Embedding model identifier"
    )
    retriever_type: Literal["basic", "parent_document", "multi_query"] = Field(
        default="basic", description="Retriever type"
    )
    reranker_enabled: bool = Field(
        default=False, description="Whether to enable reranking"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "splitter": "recursive",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "k_retrieval": 5,
                "embedding_model": "openai",
                "retriever_type": "basic",
                "reranker_enabled": False,
            }
        }
