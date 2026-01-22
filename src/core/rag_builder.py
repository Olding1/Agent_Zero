"""RAG Builder - RAG strategy assembly module.

This module designs RAG strategies based on data profiles.
"""

from typing import Optional

from ..schemas import RAGConfig, DataProfile
from ..llm import BuilderClient


class RAGBuilder:
    """RAG Builder designs RAG strategies based on data characteristics.
    
    The RAG Builder is responsible for:
    1. Choosing splitter type based on content
    2. Recommending chunk_size and chunk_overlap
    3. Selecting retriever type
    4. Configuring embedding model
    """
    
    def __init__(self, builder_client: BuilderClient):
        """Initialize RAG Builder with a builder client.
        
        Args:
            builder_client: LLM client for strategy recommendations
        """
        self.builder = builder_client
    
    async def design_rag_strategy(
        self,
        profile: DataProfile
    ) -> RAGConfig:
        """Design RAG strategy based on data profile.
        
        Args:
            profile: DataProfile from Profiler
            
        Returns:
            RAGConfig with recommended settings
        """
        # Use heuristics for basic strategy
        config = self._heuristic_strategy(profile)
        
        # Optionally refine with LLM
        try:
            refined_config = await self._llm_refine_strategy(profile, config)
            return refined_config
        except Exception as e:
            print(f"Warning: LLM refinement failed, using heuristic strategy: {e}")
            return config
    
    def _heuristic_strategy(self, profile: DataProfile) -> RAGConfig:
        """Generate RAG strategy using heuristics.
        
        Decision rules:
        - Has tables → ParentDocumentRetriever
        - Large files (>100k tokens) → chunk_size=2000
        - Normal documents → RecursiveCharacterTextSplitter
        
        Args:
            profile: DataProfile
            
        Returns:
            RAGConfig
        """
        # Determine splitter type
        if profile.has_tables:
            splitter = "semantic"  # Better for structured content
        elif profile.estimated_tokens > 100000:
            splitter = "token"  # More precise for large documents
        else:
            splitter = "recursive"  # Default for normal text
        
        # Determine chunk size
        if profile.estimated_tokens > 100000:
            chunk_size = 2000
            chunk_overlap = 400
        elif profile.estimated_tokens > 50000:
            chunk_size = 1500
            chunk_overlap = 300
        else:
            chunk_size = 1000
            chunk_overlap = 200
        
        # Determine retriever type
        if profile.has_tables:
            retriever_type = "parent_document"
        elif profile.total_files > 10:
            retriever_type = "multi_query"
        else:
            retriever_type = "basic"
        
        # Determine k_retrieval based on document size
        if profile.estimated_tokens > 50000:
            k_retrieval = 10
        else:
            k_retrieval = 5
        
        # Enable reranker for large document sets
        reranker_enabled = profile.total_files > 5 or profile.estimated_tokens > 50000
        
        return RAGConfig(
            splitter=splitter,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            k_retrieval=k_retrieval,
            embedding_model="openai",  # Default, can be configured
            retriever_type=retriever_type,
            reranker_enabled=reranker_enabled,
        )
    
    async def _llm_refine_strategy(
        self,
        profile: DataProfile,
        base_config: RAGConfig
    ) -> RAGConfig:
        """Refine RAG strategy using LLM.
        
        Args:
            profile: DataProfile
            base_config: Base configuration from heuristics
            
        Returns:
            Refined RAGConfig
        """
        prompt = self._build_refinement_prompt(profile, base_config)
        
        response = await self.builder.call(
            prompt=prompt,
            schema=RAGConfig
        )
        
        if isinstance(response, str):
            return RAGConfig.model_validate_json(response)
        else:
            return response
    
    def _build_refinement_prompt(
        self,
        profile: DataProfile,
        base_config: RAGConfig
    ) -> str:
        """Build prompt for LLM refinement.
        
        Args:
            profile: DataProfile
            base_config: Base configuration
            
        Returns:
            Prompt string
        """
        prompt = f"""You are a RAG (Retrieval-Augmented Generation) expert. 
Analyze the following data profile and refine the RAG configuration.

Data Profile:
- Total files: {profile.total_files}
- Total size: {profile.total_size_bytes / 1024:.1f} KB
- Estimated tokens: {profile.estimated_tokens}
- Text density: {profile.text_density:.2f}
- Has tables: {profile.has_tables}
- Languages: {', '.join(profile.languages_detected)}

Current RAG Configuration:
{base_config.model_dump_json(indent=2)}

Based on the data characteristics, refine the RAG configuration if needed.
Consider:
1. Splitter type (recursive/character/token/semantic)
2. Chunk size and overlap
3. Retriever type (basic/parent_document/multi_query)
4. Number of chunks to retrieve (k_retrieval)
5. Whether to enable reranking

Output the refined configuration in JSON format matching the RAGConfig schema.
"""
        return prompt
    
    def save_config(self, config: RAGConfig, output_path) -> None:
        """Save RAG config to JSON file.
        
        Args:
            config: RAGConfig to save
            output_path: Path to save JSON file
        """
        from pathlib import Path
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(config.model_dump_json(indent=2))
    
    def load_config(self, input_path) -> RAGConfig:
        """Load RAG config from JSON file.
        
        Args:
            input_path: Path to JSON file
            
        Returns:
            RAGConfig object
        """
        from pathlib import Path
        input_path = Path(input_path)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            return RAGConfig.model_validate_json(f.read())
