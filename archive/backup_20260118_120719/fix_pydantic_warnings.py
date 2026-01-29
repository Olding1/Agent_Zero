"""
批量修复 Pydantic V2 弃用警告

将所有 Schema 文件从 class Config 迁移到 model_config = ConfigDict
"""

import re
from pathlib import Path

# 需要修复的文件列表
files_to_fix = [
    "src/schemas/tools_config.py",
    "src/schemas/test_cases.py",
    "src/schemas/state_schema.py",
    "src/schemas/simulation.py",
    "src/schemas/project_meta.py",
    "src/schemas/pattern.py",
    "src/schemas/graph_structure.py",
    "src/schemas/execution_result.py",
    "src/core/test_generator.py",
]

def fix_pydantic_config(file_path: Path):
    """修复单个文件的 Pydantic 配置"""
    content = file_path.read_text(encoding='utf-8')
    
    # 1. 添加 ConfigDict 导入
    if 'from pydantic import' in content and 'ConfigDict' not in content:
        content = re.sub(
            r'from pydantic import ([^\n]+)',
            r'from pydantic import \1, ConfigDict',
            content
        )
    
    # 2. 替换 class Config: 为 model_config = ConfigDict(
    # 匹配 class Config: 及其内容
    pattern = r'(\s+)class Config:\s*\n\s*""".*?"""\s*\n\s*\n((?:\s+\w+\s*=\s*[^\n]+\n?)+)'
    
    def replace_config(match):
        indent = match.group(1)
        config_content = match.group(2)
        
        # 提取配置项
        config_lines = config_content.strip().split('\n')
        config_dict = []
        for line in config_lines:
            line = line.strip()
            if '=' in line:
                config_dict.append(f"{indent}    {line}")
        
        return f"{indent}model_config = ConfigDict(\n" + '\n'.join(config_dict) + f"\n{indent})"
    
    content = re.sub(pattern, replace_config, content)
    
    # 简单替换版本(如果上面的复杂替换失败)
    content = re.sub(
        r'(\s+)class Config:\s*\n\s*"""[^"]*"""\s*\n',
        r'\1model_config = ConfigDict(\n',
        content
    )
    
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ 已修复: {file_path}")

# 执行修复
base_dir = Path("c:/Users/Administrator/Desktop/game/Agent_Zero")
for file_rel in files_to_fix:
    file_path = base_dir / file_rel
    if file_path.exists():
        try:
            fix_pydantic_config(file_path)
        except Exception as e:
            print(f"❌ 修复失败 {file_path}: {e}")
    else:
        print(f"⚠️ 文件不存在: {file_path}")

print("\n✅ 批量修复完成!")
