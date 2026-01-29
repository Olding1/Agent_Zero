"""快速修复 Embedding 模型配置"""

from pathlib import Path

def fix_agent_embedding(agent_name: str):
    """修复指定 Agent 的 embedding 配置"""
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
    
    # 替换模型名称
    original = content
    content = content.replace(
        "EMBEDDING_MODEL_NAME=text-embedding-3-small",
        "EMBEDDING_MODEL_NAME=nomic-embed-text"
    )
    
    if content == original:
        print("⚠️ 未找到需要替换的配置")
        return False
    
    # 写回
    env_file.write_text(content, encoding='utf-8')
    print(f"✅ 已修复 {agent_name} 的 embedding 模型配置")
    print("\n下一步:")
    print("1. 拉取模型: ollama pull nomic-embed-text")
    print("2. 重新测试: python start.py (选择 3)")
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        agent_name = sys.argv[1]
    else:
        agent_name = "AgentZero文档助手"
    
    print(f"🔧 修复 Agent: {agent_name}")
    print("=" * 50)
    
    if fix_agent_embedding(agent_name):
        print("\n✅ 修复完成!")
    else:
        print("\n❌ 修复失败")
