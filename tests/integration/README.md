# 集成测试说明

## 测试脚本

### 1. Phase 4 闭环集成测试
**文件**: `test_phase4_integration.py`
**目标**: 验证 Phase 4 完整闭环流程

**测试内容**:
- Task 4.1: 外部 Trace 存储
- Task 4.2: Test Generator
- Task 4.3: Compiler 升级
- Task 4.4: Runner
- Task 4.5: Judge
- Task 4.6: Git 版本管理

**运行**: `python tests/integration/test_phase4_integration.py`

### 2. Phase 1-4 端到端测试
**文件**: `test_e2e_phase1_to_4.py`
**目标**: 验证完整用户流程

**测试内容**:
- Phase 1: Compiler, EnvManager
- Phase 2: RAGBuilder, ToolSelector
- Phase 3: PM, GraphDesigner
- Phase 4: 完整闭环

**运行**: `python tests/integration/test_e2e_phase1_to_4.py`

## 为什么这么测试

1. **真实场景**: 模拟用户实际使用流程
2. **集成验证**: 确保模块间正确协作
3. **完整性**: 覆盖所有关键功能

详细说明请查看测试脚本中的文档字符串。
