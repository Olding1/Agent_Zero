"""
手动更新现有 Agent 的 .env 文件以包含 Judge API 配置
"""

from pathlib import Path
import os
from dotenv import load_dotenv

def update_agent_env_with_judge_config(agent_name: str):
    """更新指定 Agent 的 .env 文件,添加 Judge API 配置"""
    
    # 加载主 .env
    load_dotenv()
    
    agent_dir = Path(f"agents/{agent_name}")
    env_file = agent_dir / ".env"
    
    if not env_file.exists():
        print(f"❌ 未找到 .env 文件: {env_file}")
        return False
    
    # 读取当前配置
    content = env_file.read_text(encoding='utf-8')
    
    # 备份
    backup_file = agent_dir / ".env.backup"
    backup_file.write_text(content, encoding='utf-8')
    print(f"✅ 已备份到: {backup_file}")
    
    # 检查是否已有 Judge 配置
    if "JUDGE_PROVIDER" in content:
        print("⚠️ 已存在 Judge 配置,跳过")
        return False
    
    # 从主环境获取 Judge 配置
    judge_provider = os.getenv("JUDGE_PROVIDER", os.getenv("RUNTIME_PROVIDER", "openai"))
    judge_model = os.getenv("JUDGE_MODEL", os.getenv("RUNTIME_MODEL", "deepseek-chat"))
    judge_api_key = os.getenv("JUDGE_API_KEY", os.getenv("RUNTIME_API_KEY", ""))
    judge_base_url = os.getenv("JUDGE_BASE_URL", os.getenv("RUNTIME_BASE_URL", "https://api.deepseek.com"))
    judge_timeout = os.getenv("JUDGE_TIMEOUT", "60")
    judge_temperature = os.getenv("JUDGE_TEMPERATURE", "0.0")
    
    # 添加 Judge 配置
    judge_config = f"""
# Judge API Configuration (用于 DeepEval 测试评估)
# 如果未配置,DeepEval 将使用 Runtime API
JUDGE_PROVIDER={judge_provider}
JUDGE_MODEL={judge_model}
JUDGE_API_KEY={judge_api_key}
JUDGE_BASE_URL={judge_base_url}
JUDGE_TIMEOUT={judge_timeout}
JUDGE_TEMPERATURE={judge_temperature}
"""
    
    # 追加到文件末尾
    content += judge_config
    
    # 写回
    env_file.write_text(content, encoding='utf-8')
    print(f"✅ 已更新 {agent_name} 的 .env 文件")
    print("\n添加的配置:")
    print(judge_config)
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        agent_name = sys.argv[1]
    else:
        # 更新所有 Agent
        agents_dir = Path("agents")
        if agents_dir.exists():
            agents = [d.name for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
            
            print(f"找到 {len(agents)} 个 Agent:")
            for i, agent in enumerate(agents, 1):
                print(f"   {i}. {agent}")
            
            choice = input("\n选择 Agent 编号 (0=全部): ").strip()
            
            if choice == "0":
                # 更新所有
                for agent in agents:
                    print(f"\n{'='*50}")
                    print(f"更新: {agent}")
                    print('='*50)
                    update_agent_env_with_judge_config(agent)
            else:
                try:
                    idx = int(choice)
                    if 1 <= idx <= len(agents):
                        agent_name = agents[idx - 1]
                        update_agent_env_with_judge_config(agent_name)
                    else:
                        print("无效序号")
                except ValueError:
                    print("无效输入")
        else:
            print("❌ agents 目录不存在")
