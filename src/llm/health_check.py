"""Health check utilities for API connectivity testing."""

import asyncio
from typing import Optional, Tuple
from enum import Enum
import httpx
from pydantic import BaseModel, Field

from .builder_client import BuilderClient, BuilderAPIConfig
from .runtime_client import RuntimeClient, RuntimeAPIConfig


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult(BaseModel):
    """Result of health check."""

    status: HealthStatus = Field(..., description="Health status")
    message: str = Field(..., description="Status message")
    response_time_ms: Optional[int] = Field(
        default=None, description="Response time in milliseconds"
    )
    error: Optional[str] = Field(default=None, description="Error message if unhealthy")


async def check_builder_api(config: BuilderAPIConfig) -> HealthCheckResult:
    """Check Builder API connectivity.
    
    Args:
        config: Builder API configuration
        
    Returns:
        HealthCheckResult with status and details
    """
    try:
        import time

        start_time = time.time()

        client = BuilderClient(config)
        is_healthy = await client.health_check()

        response_time = int((time.time() - start_time) * 1000)

        if is_healthy:
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message=f"Builder API ({config.provider}/{config.model}) is accessible",
                response_time_ms=response_time,
            )
        else:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="Builder API health check failed",
                response_time_ms=response_time,
                error="Health check returned False",
            )

    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message="Builder API is not accessible",
            error=str(e),
        )


async def check_runtime_api(config: RuntimeAPIConfig) -> HealthCheckResult:
    """Check Runtime API connectivity.
    
    Args:
        config: Runtime API configuration
        
    Returns:
        HealthCheckResult with status and details
    """
    try:
        import time

        start_time = time.time()

        # For Ollama, check if the server is running
        if config.provider == "ollama":
            base_url = config.base_url or "http://localhost:11434"
            async with httpx.AsyncClient(timeout=config.timeout) as client:
                response = await client.get(f"{base_url}/api/tags")
                response.raise_for_status()

            response_time = int((time.time() - start_time) * 1000)

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message=f"Ollama server is running at {base_url}",
                response_time_ms=response_time,
            )

        # For OpenAI/Anthropic, check API key and endpoint
        elif config.provider in ["openai", "anthropic"]:
            if not config.api_key:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"{config.provider} API key is not configured",
                    error="Missing API key",
                )

            # Simple connectivity check
            base_url = config.base_url or (
                "https://api.openai.com/v1"
                if config.provider == "openai"
                else "https://api.anthropic.com"
            )

            async with httpx.AsyncClient(timeout=config.timeout) as client:
                # Just check if the endpoint is reachable
                response = await client.get(
                    base_url,
                    headers={"Authorization": f"Bearer {config.api_key}"},
                )

            response_time = int((time.time() - start_time) * 1000)

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message=f"Runtime API ({config.provider}/{config.model}) endpoint is reachable",
                response_time_ms=response_time,
            )

        else:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"Unknown provider: {config.provider}",
                error="Unsupported provider",
            )

    except httpx.TimeoutException:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message="Runtime API request timed out",
            error="Connection timeout",
        )
    except httpx.HTTPStatusError as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message=f"Runtime API returned error: {e.response.status_code}",
            error=str(e),
        )
    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message="Runtime API is not accessible",
            error=str(e),
        )


async def check_all_apis(
    builder_config: BuilderAPIConfig, runtime_config: RuntimeAPIConfig
) -> Tuple[HealthCheckResult, HealthCheckResult]:
    """Check both Builder and Runtime APIs concurrently.
    
    Args:
        builder_config: Builder API configuration
        runtime_config: Runtime API configuration
        
    Returns:
        Tuple of (builder_result, runtime_result)
    """
    builder_task = check_builder_api(builder_config)
    runtime_task = check_runtime_api(runtime_config)

    builder_result, runtime_result = await asyncio.gather(
        builder_task, runtime_task, return_exceptions=True
    )

    # Handle exceptions
    if isinstance(builder_result, Exception):
        builder_result = HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message="Builder API check failed",
            error=str(builder_result),
        )

    if isinstance(runtime_result, Exception):
        runtime_result = HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message="Runtime API check failed",
            error=str(runtime_result),
        )

    return builder_result, runtime_result
