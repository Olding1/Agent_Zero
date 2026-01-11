"""Test health check functionality."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.llm import (
    BuilderAPIConfig,
    RuntimeAPIConfig,
    check_builder_api,
    check_runtime_api,
    check_all_apis,
    HealthStatus,
)


async def test_health_checks():
    """Test API health checks."""
    
    print("=" * 60)
    print("API Health Check Test")
    print("=" * 60)
    
    # Test Builder API (using environment variables or defaults)
    print("\n[1/3] Testing Builder API...")
    builder_config = BuilderAPIConfig(
        provider="openai",
        model="gpt-4o",
        api_key="test-key",  # This will fail, but tests the logic
        base_url="https://api.openai.com/v1",
        timeout=5,
        max_retries=1,
        temperature=0.7,
    )
    
    builder_result = await check_builder_api(builder_config)
    print(f"Status: {builder_result.status.value}")
    print(f"Message: {builder_result.message}")
    if builder_result.response_time_ms:
        print(f"Response Time: {builder_result.response_time_ms}ms")
    if builder_result.error:
        print(f"Error: {builder_result.error}")
    
    # Test Runtime API - Ollama (local)
    print("\n[2/3] Testing Runtime API (Ollama)...")
    runtime_config_ollama = RuntimeAPIConfig(
        provider="ollama",
        model="llama2",
        base_url="http://localhost:11434",
        timeout=5,
        temperature=0.7,
    )
    
    runtime_result_ollama = await check_runtime_api(runtime_config_ollama)
    print(f"Status: {runtime_result_ollama.status.value}")
    print(f"Message: {runtime_result_ollama.message}")
    if runtime_result_ollama.response_time_ms:
        print(f"Response Time: {runtime_result_ollama.response_time_ms}ms")
    if runtime_result_ollama.error:
        print(f"Error: {runtime_result_ollama.error}")
    
    # Test Runtime API - OpenAI
    print("\n[3/3] Testing Runtime API (OpenAI)...")
    runtime_config_openai = RuntimeAPIConfig(
        provider="openai",
        model="gpt-3.5-turbo",
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        timeout=5,
        temperature=0.7,
    )
    
    runtime_result_openai = await check_runtime_api(runtime_config_openai)
    print(f"Status: {runtime_result_openai.status.value}")
    print(f"Message: {runtime_result_openai.message}")
    if runtime_result_openai.response_time_ms:
        print(f"Response Time: {runtime_result_openai.response_time_ms}ms")
    if runtime_result_openai.error:
        print(f"Error: {runtime_result_openai.error}")
    
    # Test concurrent checks
    print("\n[Bonus] Testing concurrent API checks...")
    builder_result, runtime_result = await check_all_apis(
        builder_config, runtime_config_openai
    )
    print(f"Builder: {builder_result.status.value}")
    print(f"Runtime: {runtime_result.status.value}")
    
    print("\n" + "=" * 60)
    print("✓ Health Check Test Complete!")
    print("=" * 60)
    print("\nNote: Tests may show UNHEALTHY status if:")
    print("- API keys are not configured")
    print("- Ollama is not running locally")
    print("- Network connectivity issues")
    print("\nThis is expected behavior for the test.")


if __name__ == "__main__":
    asyncio.run(test_health_checks())
