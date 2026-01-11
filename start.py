"""Startup script for Agent Zero system."""

import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.llm import (
    BuilderAPIConfig,
    RuntimeAPIConfig,
    check_all_apis,
    HealthStatus,
)


def print_banner():
    """Print Agent Zero banner."""
    print("=" * 70)
    print("🚀 Agent Zero v6.0 - Intelligent Agent Construction Factory")
    print("=" * 70)
    print()


async def check_system_health():
    """Check system health before starting."""
    print("📊 System Health Check")
    print("-" * 70)
    
    # Load environment variables
    load_dotenv()
    
    # Check Builder API
    builder_config = BuilderAPIConfig(
        provider=os.getenv("BUILDER_PROVIDER", "openai"),
        model=os.getenv("BUILDER_MODEL", "gpt-4o"),
        api_key=os.getenv("BUILDER_API_KEY", ""),
        base_url=os.getenv("BUILDER_BASE_URL"),
        timeout=int(os.getenv("BUILDER_TIMEOUT", "60")),
        max_retries=int(os.getenv("BUILDER_MAX_RETRIES", "3")),
        temperature=float(os.getenv("BUILDER_TEMPERATURE", "0.7")),
    )
    
    # Check Runtime API
    runtime_config = RuntimeAPIConfig(
        provider=os.getenv("RUNTIME_PROVIDER", "openai"),
        model=os.getenv("RUNTIME_MODEL", "gpt-3.5-turbo"),
        api_key=os.getenv("RUNTIME_API_KEY"),
        base_url=os.getenv("RUNTIME_BASE_URL"),
        timeout=int(os.getenv("RUNTIME_TIMEOUT", "30")),
        temperature=float(os.getenv("RUNTIME_TEMPERATURE", "0.7")),
    )
    
    print("\n🔍 Checking Builder API...")
    print(f"   Provider: {builder_config.provider}")
    print(f"   Model: {builder_config.model}")
    print(f"   API Key: {'✓ Configured' if builder_config.api_key else '✗ Missing'}")
    
    print("\n🔍 Checking Runtime API...")
    print(f"   Provider: {runtime_config.provider}")
    print(f"   Model: {runtime_config.model}")
    print(f"   API Key: {'✓ Configured' if runtime_config.api_key else '✗ Missing'}")
    
    # Perform health checks
    print("\n⏳ Testing connectivity...")
    try:
        builder_result, runtime_result = await check_all_apis(
            builder_config, runtime_config
        )
        
        print(f"\n   Builder API: {_get_status_emoji(builder_result.status)} {builder_result.status.value.upper()}")
        print(f"   {builder_result.message}")
        if builder_result.response_time_ms:
            print(f"   Response time: {builder_result.response_time_ms}ms")
        
        print(f"\n   Runtime API: {_get_status_emoji(runtime_result.status)} {runtime_result.status.value.upper()}")
        print(f"   {runtime_result.message}")
        if runtime_result.response_time_ms:
            print(f"   Response time: {runtime_result.response_time_ms}ms")
        
        # Check if both are healthy
        both_healthy = (
            builder_result.status == HealthStatus.HEALTHY
            and runtime_result.status == HealthStatus.HEALTHY
        )
        
        print("\n" + "-" * 70)
        if both_healthy:
            print("✅ All systems operational!")
        else:
            print("⚠️  Some systems are not fully operational")
            print("\nPlease check:")
            print("1. API keys are configured in .env file")
            print("2. Network connectivity")
            print("3. API service status")
        
        return both_healthy
        
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        return False


def _get_status_emoji(status: HealthStatus) -> str:
    """Get emoji for health status."""
    if status == HealthStatus.HEALTHY:
        return "✅"
    elif status == HealthStatus.UNHEALTHY:
        return "❌"
    else:
        return "❓"


def show_menu():
    """Show main menu."""
    print("\n" + "=" * 70)
    print("📋 Main Menu")
    print("=" * 70)
    print("\n1. 🏗️  Create New Agent")
    print("2. 📦 List Generated Agents")
    print("3. 🔧 Configure API Settings")
    print("4. 🧪 Run Tests")
    print("5. 📖 View Documentation")
    print("6. 🚪 Exit")
    print()


async def main():
    """Main entry point."""
    print_banner()
    
    # Check if .env exists
    if not Path(".env").exists():
        print("⚠️  No .env file found!")
        print("\nPlease create a .env file from the template:")
        print("   cp .env.template .env")
        print("\nThen edit .env and add your API keys.")
        print()
        return
    
    # Run health check
    is_healthy = await check_system_health()
    
    if not is_healthy:
        print("\n⚠️  System health check failed. You can still continue, but")
        print("   some features may not work properly.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("\nExiting...")
            return
    
    # Show menu
    while True:
        show_menu()
        choice = input("Select an option (1-6): ").strip()
        
        if choice == "1":
            print("\n🏗️  Agent creation wizard coming soon in Phase 2!")
            print("   For now, use the E2E test to generate agents:")
            print("   python tests/e2e/test_phase1_hello_world.py")
        elif choice == "2":
            print("\n📦 Listing generated agents...")
            agents_dir = Path("agents")
            if agents_dir.exists():
                agents = [d for d in agents_dir.iterdir() if d.is_dir()]
                if agents:
                    for i, agent in enumerate(agents, 1):
                        print(f"   {i}. {agent.name}")
                else:
                    print("   No agents found.")
            else:
                print("   No agents directory found.")
        elif choice == "3":
            print("\n🔧 API Configuration")
            print("   Edit the .env file to configure API settings")
            print(f"   Location: {Path('.env').absolute()}")
        elif choice == "4":
            print("\n🧪 Running tests...")
            print("   python tests/e2e/test_phase1_hello_world.py")
        elif choice == "5":
            print("\n📖 Documentation")
            print("   README.md - Project overview")
            print("   Agent Zero项目计划书.md - Project plan")
            print("   Agent_Zero_详细实施计划.md - Implementation plan")
        elif choice == "6":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid option. Please select 1-6.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
