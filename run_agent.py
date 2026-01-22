"""Simple script to run a generated agent."""

import sys
import subprocess
from pathlib import Path
import shutil


def main():
    """Run a generated agent."""
    
    print("=" * 70)
    print("🤖 Agent Zero - Agent Runner")
    print("=" * 70)
    
    # Check for agents
    agents_dir = Path("agents")
    if not agents_dir.exists():
        print("\n❌ No agents directory found.")
        print("   Please generate an agent first using:")
        print("   python tests/e2e/test_phase1_hello_world.py")
        return
    
    # List available agents
    agents = [d for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if not agents:
        print("\n❌ No agents found.")
        print("   Please generate an agent first using:")
        print("   python tests/e2e/test_phase1_hello_world.py")
        return
    
    print("\n📦 Available Agents:")
    for i, agent in enumerate(agents, 1):
        print(f"   {i}. {agent.name}")
    
    # Select agent
    print()
    try:
        choice = int(input("Select agent number: ").strip())
        if choice < 1 or choice > len(agents):
            print("❌ Invalid selection.")
            return
        
        selected_agent = agents[choice - 1]
    except (ValueError, IndexError):
        print("❌ Invalid input.")
        return
    
    # Check if .env exists
    env_file = selected_agent / ".env"
    env_template = selected_agent / ".env.template"
    main_env = Path(".env")
    
    if not env_file.exists():
        # Try to copy from main project .env first
        if main_env.exists():
            print(f"\n📋 Copying .env configuration from main project...")
            try:
                # Read main .env and extract Runtime API and Embedding settings
                with open(main_env, 'r', encoding='utf-8') as f:
                    main_content = f.read()
                
                # Create agent .env with Runtime API and Embedding settings
                agent_env_content = f"""# Agent Runtime Configuration
# Auto-copied from main project

# Runtime API Configuration
"""
                # Extract Runtime API lines from main .env
                for line in main_content.split('\n'):
                    if line.strip().startswith('RUNTIME_'):
                        agent_env_content += line + '\n'
                
                # Add Embedding Configuration section
                agent_env_content += "\n# Embedding API Configuration\n"
                for line in main_content.split('\n'):
                    if line.strip().startswith('EMBEDDING_') or (line.strip().startswith('#') and 'EMBEDDING' in line):
                        agent_env_content += line + '\n'
                
                # Write to agent .env
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.write(agent_env_content)
                
                print(f"   ✓ Created {env_file}")
                print(f"   ✓ Copied Runtime API configuration")
                print(f"   ✓ Copied Embedding API configuration")
                
            except Exception as e:
                print(f"   ⚠️  Failed to copy .env: {e}")
                print(f"   Creating from template instead...")
                if env_template.exists():
                    shutil.copy(env_template, env_file)
                    print(f"   ✓ Created {env_file} from template")
        elif env_template.exists():
            print(f"\n⚠️  No .env file found for {selected_agent.name}")
            print("   Creating .env from template...")
            shutil.copy(env_template, env_file)
            print(f"   ✓ Created {env_file}")
            print("\n   ⚠️  IMPORTANT: Please edit .env and add your API keys before running!")
            print(f"   Location: {env_file.absolute()}")
            
            response = input("\n   Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return
    
    # Check for Python executable in venv
    if sys.platform == "win32":
        python_exe = selected_agent / ".venv" / "Scripts" / "python.exe"
    else:
        python_exe = selected_agent / ".venv" / "bin" / "python"
    
    if not python_exe.exists():
        print(f"\n❌ Virtual environment not found at {python_exe}")
        print("   Please run the E2E test first to set up the environment.")
        return
    
    # Run the agent
    agent_script = selected_agent / "agent.py"
    if not agent_script.exists():
        print(f"\n❌ Agent script not found at {agent_script}")
        return
    
    print(f"\n🚀 Starting {selected_agent.name}...")
    print(f"   Python: {python_exe}")
    print(f"   Script: {agent_script}")
    print("\n" + "-" * 70)
    print("Type 'quit', 'exit', or 'q' to stop the agent")
    print("-" * 70 + "\n")
    
    # Run the agent
    try:
        subprocess.run(
            [str(python_exe.absolute()), "agent.py"],
            cwd=str(selected_agent.absolute()),
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Agent exited with error code {e.returncode}")
    except KeyboardInterrupt:
        print("\n\n👋 Agent stopped by user.")


if __name__ == "__main__":
    main()
