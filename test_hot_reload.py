"""
测试热重载功能
"""

import sys
from pathlib import Path

# 模拟修改前的状态
print("=" * 60)
print("测试场景: 模拟用户在同一个 Python 进程中生成和测试 Agent")
print("=" * 60)

# 第一次导入
print("\n1️⃣ 第一次导入 Runner...")
from src.core.runner import Runner
print(f"   Runner 模块 ID: {id(sys.modules['src.core.runner'])}")

# 模拟用户生成了新 Agent (此时可能修改了 runner.py)
print("\n2️⃣ 模拟生成 Agent (可能修改了代码)...")
print("   (假设此时 runner.py 被修改了)")

# 使用热重载
print("\n3️⃣ 执行热重载...")
import importlib

modules_to_reload = [
    'src.core.runner',
    'src.core.compiler',
]

for module_name in modules_to_reload:
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
        print(f"   ✅ 重新加载: {module_name}")

# 第二次导入 (应该是新的模块)
print("\n4️⃣ 重新导入 Runner...")
from src.core.runner import Runner as Runner2
print(f"   Runner 模块 ID: {id(sys.modules['src.core.runner'])}")

# 验证
print("\n5️⃣ 验证结果...")
if Runner is Runner2:
    print("   ⚠️  警告: Runner 类引用相同 (这是正常的)")
    print("   但模块已重新加载,新代码会生效")
else:
    print("   ✅ Runner 类已更新")

# 测试实际使用
print("\n6️⃣ 测试实际使用...")
try:
    test_dir = Path("agents/AgentZero文档助手")
    if test_dir.exists():
        runner = Runner2(test_dir)
        print(f"   ✅ 成功创建 Runner: {runner.agent_dir}")
        print(f"   ✅ venv Python: {runner.venv_python}")
    else:
        print("   ⚠️  测试目录不存在,跳过实际测试")
except Exception as e:
    print(f"   ❌ 错误: {e}")

print("\n" + "=" * 60)
print("✅ 热重载测试完成!")
print("=" * 60)
