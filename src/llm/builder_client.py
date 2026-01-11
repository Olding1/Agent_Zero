"""Builder API client for construction-time LLM calls."""

from typing import Optional, Type, Any
from pydantic import BaseModel, Field
import httpx
import os

# Optional imports for different providers
try:
    from langchain_openai import ChatOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from langchain_anthropic import ChatAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class BuilderAPIConfig(BaseModel):
    """Configuration for Builder API."""

    provider: str = Field(..., description="API provider (openai/anthropic/azure)")
    model: str = Field(..., description="Model name")
    api_key: str = Field(..., description="API key")
    base_url: Optional[str] = Field(default=None, description="Custom base URL")
    timeout: int = Field(default=60, description="Timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature")


class BuilderClient:
    """Builder API client for construction-time LLM calls.
    
    This client is used by PM, Graph Designer, RAG Builder, and other
    construction-time components. It uses a powerful model (GPT-4o, Claude 3.5)
    to generate high-quality agent designs.
    """

    def __init__(self, config: BuilderAPIConfig):
        """Initialize Builder API client.
        
        Args:
            config: Builder API configuration
        """
        self.config = config
        self.client = self._init_client(config)

    def _init_client(self, config: BuilderAPIConfig) -> Any:
        """Initialize LLM client based on provider.
        
        Args:
            config: Builder API configuration
            
        Returns:
            Initialized LLM client
        """
        if config.provider == "openai":
            if not HAS_OPENAI:
                raise ImportError(
                    "langchain-openai is not installed. "
                    "Install it with: pip install langchain-openai"
                )
            return ChatOpenAI(
                model=config.model,
                api_key=config.api_key,
                base_url=config.base_url,
                temperature=config.temperature,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        elif config.provider == "anthropic":
            if not HAS_ANTHROPIC:
                raise ImportError(
                    "langchain-anthropic is not installed. "
                    "Install it with: pip install langchain-anthropic"
                )
            return ChatAnthropic(
                model=config.model,
                api_key=config.api_key,
                temperature=config.temperature,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

    async def call(
        self, prompt: str, schema: Optional[Type[BaseModel]] = None
    ) -> str | BaseModel:
        """Call Builder API with optional structured output.
        
        Args:
            prompt: Input prompt
            schema: Optional Pydantic schema for structured output
            
        Returns:
            Response string or structured output
        """
        if schema:
            # Use structured output
            structured_llm = self.client.with_structured_output(schema)
            result = await structured_llm.ainvoke(prompt)
            return result
        else:
            # Regular text output
            response = await self.client.ainvoke(prompt)
            return response.content

    async def health_check(self) -> bool:
        """Check API connectivity.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Simple test call
            response = await self.client.ainvoke("Hello")
            return True
        except Exception as e:
            print(f"Builder API health check failed: {e}")
            return False

    @classmethod
    def from_env(cls) -> "BuilderClient":
        """Create Builder client from environment variables.
        
        Returns:
            Initialized BuilderClient
        """
        config = BuilderAPIConfig(
            provider=os.getenv("BUILDER_PROVIDER", "openai"),
            model=os.getenv("BUILDER_MODEL", "gpt-4o"),
            api_key=os.getenv("BUILDER_API_KEY", ""),
            base_url=os.getenv("BUILDER_BASE_URL"),
            timeout=int(os.getenv("BUILDER_TIMEOUT", "60")),
            max_retries=int(os.getenv("BUILDER_MAX_RETRIES", "3")),
            temperature=float(os.getenv("BUILDER_TEMPERATURE", "0.7")),
        )
        return cls(config)
