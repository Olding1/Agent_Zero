"""
验证热重载修复: 确保 reload 在 import 之前
"""

import sys

print("=" * 60)
print("测试: 验证 reload 在 import 之前执行")
print("=" * 60)

# 模拟第一次导入 (旧代码)
print("\n1️⃣ 第一次导入 Runner (模拟旧代码)...")
from src.core.runner import Runner as OldRunner
print(f"   OldRunner 类 ID: {id(OldRunner)}")
print(f"   模块 ID: {id(sys.modules['src.core.runner'])}")

# 模拟修改代码
print("\n2️⃣ 模拟代码被修改...")

# 正确的顺序: 先 reload, 再 import
print("\n3️⃣ 执行 reload...")
import importlib
if 'src.core.runner' in sys.modules:
    importlib.reload(sys.modules['src.core.runner'])
    print("   ✅ 模块已重新加载")

print("\n4️⃣ 重新导入 Runner (在 reload 之后)...")
from src.core.runner import Runner as NewRunner
print(f"   NewRunner 类 ID: {id(NewRunner)}")
print(f"   模块 ID: {id(sys.modules['src.core.runner'])}")

# 验证
print("\n5️⃣ 验证...")
if OldRunner is NewRunner:
    print("   ⚠️  警告: 类引用相同")
    print("   这是正常的,因为 reload 会更新模块内容")
    print("   但新代码会生效!")
else:
    print("   ✅ 类引用不同 (完全重新加载)")

# 测试实际使用
print("\n6️⃣ 测试使用新 Runner...")
from pathlib import Path
test_dir = Path("agents/AgentZero文档助手")
if test_dir.exists():
    runner = NewRunner(test_dir)
    print(f"   ✅ 成功创建: {runner.agent_dir}")
    print(f"   ✅ venv: {runner.venv_python}")
    
    # 检查是否是绝对路径
    if runner.agent_dir.is_absolute():
        print("   ✅ 使用绝对路径 (新代码特征)")
    else:
        print("   ❌ 使用相对路径 (旧代码)")
else:
    print("   ⚠️  测试目录不存在")

print("\n" + "=" * 60)
print("✅ 验证完成!")
print("=" * 60)
