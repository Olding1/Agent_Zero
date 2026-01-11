"""Runtime API client for generated agent execution."""

from typing import Optional
from pydantic import BaseModel, Field
import os


class RuntimeAPIConfig(BaseModel):
    """Configuration for Runtime API.
    
    This configuration is used by generated agents during execution.
    """

    provider: str = Field(..., description="API provider (openai/anthropic/ollama)")
    model: str = Field(..., description="Model name")
    api_key: Optional[str] = Field(default=None, description="API key (optional for Ollama)")
    base_url: Optional[str] = Field(default=None, description="Custom base URL")
    timeout: int = Field(default=30, description="Timeout in seconds")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature")


class RuntimeClient:
    """Runtime API client for generated agent execution.
    
    This is a lightweight wrapper that generated agents use to call LLMs.
    Unlike BuilderClient, this supports local models (Ollama) and is designed
    for cost-effective runtime execution.
    """

    def __init__(self, config: RuntimeAPIConfig):
        """Initialize Runtime API client.
        
        Args:
            config: Runtime API configuration
        """
        self.config = config

    @classmethod
    def from_env(cls) -> "RuntimeClient":
        """Create Runtime client from environment variables.
        
        This is the primary way generated agents initialize the client.
        
        Returns:
            Initialized RuntimeClient
        """
        config = RuntimeAPIConfig(
            provider=os.getenv("RUNTIME_PROVIDER", "openai"),
            model=os.getenv("RUNTIME_MODEL", "gpt-3.5-turbo"),
            api_key=os.getenv("RUNTIME_API_KEY"),
            base_url=os.getenv("RUNTIME_BASE_URL"),
            timeout=int(os.getenv("RUNTIME_TIMEOUT", "30")),
            temperature=float(os.getenv("RUNTIME_TEMPERATURE", "0.7")),
        )
        return cls(config)

    def get_env_dict(self) -> dict[str, str]:
        """Get environment variables dictionary for subprocess injection.
        
        Returns:
            Dictionary of environment variables
        """
        env_vars = {
            "RUNTIME_PROVIDER": self.config.provider,
            "RUNTIME_MODEL": self.config.model,
            "RUNTIME_TIMEOUT": str(self.config.timeout),
            "RUNTIME_TEMPERATURE": str(self.config.temperature),
        }

        if self.config.api_key:
            env_vars["RUNTIME_API_KEY"] = self.config.api_key

        if self.config.base_url:
            env_vars["RUNTIME_BASE_URL"] = self.config.base_url

        return env_vars
