"""
Phase 4 Task 4.1 简化测试 - 直接验证模板文件

这个测试不需要编译,直接检查模板文件是否包含必要的代码
"""

import pytest
from pathlib import Path


def test_trace_manager_class_in_template():
    """测试 1: 验证模板包含 TraceManager 类"""
    
    template_file = Path(__file__).parent.parent.parent / "src" / "templates" / "agent_template.py.j2"
    assert template_file.exists(), f"模板文件不存在: {template_file}"
    
    template_content = template_file.read_text(encoding="utf-8")
    
    # 验证包含 TraceManager 类
    assert "class TraceManager:" in template_content, "应该包含 TraceManager 类"
    assert "def __init__(self, agent_dir: Path = None):" in template_content, "应该有 __init__ 方法"
    assert "def start_new_trace(self) -> str:" in template_content, "应该有 start_new_trace 方法"
    assert "def add_entry(self, entry: Dict[str, Any]):" in template_content, "应该有 add_entry 方法"
    assert "def save(self):" in template_content, "应该有 save 方法"
    assert "def load(self, trace_file: str) -> List[Dict]:" in template_content, "应该有 load 方法"
    
    # 验证全局实例
    assert "_trace_manager = TraceManager()" in template_content, "应该有全局 _trace_manager 实例"
    
    print("✅ 测试 1 通过: TraceManager 类存在于模板中")


def test_trace_file_field_in_template():
    """测试 2: 验证模板包含 trace_file 字段"""
    
    template_file = Path(__file__).parent.parent.parent / "src" / "templates" / "agent_template.py.j2"
    template_content = template_file.read_text(encoding="utf-8")
    
    # 验证 trace_file 字段
    assert "trace_file: Optional[str]" in template_content, "AgentState 应该包含 trace_file 字段"
    assert "# 🆕 Phase 4: 外部 Trace 存储" in template_content, "应该有 Phase 4 注释"
    
    print("✅ 测试 2 通过: trace_file 字段存在于模板中")


def test_node_trace_recording_in_template():
    """测试 3: 验证模板中节点函数记录 trace"""
    
    template_file = Path(__file__).parent.parent.parent / "src" / "templates" / "agent_template.py.j2"
    template_content = template_file.read_text(encoding="utf-8")
    
    # 验证节点函数包含 trace 记录逻辑
    assert "trace_entry = {" in template_content, "节点函数应该创建 trace_entry"
    assert '"step": len(_trace_manager.trace_entries) + 1' in template_content, "应该记录步骤编号"
    assert '"node_id":' in template_content, "应该记录节点 ID"
    assert '"node_type":' in template_content, "应该记录节点类型"
    assert '"timestamp": datetime.now().isoformat()' in template_content, "应该记录时间戳"
    assert "_trace_manager.add_entry(trace_entry)" in template_content, "应该调用 add_entry"
    
    # 验证 LLM 节点的 trace 记录
    assert '"action": "llm_call"' in template_content, "LLM 节点应该记录 action"
    assert '"output_preview": response.content[:100]' in template_content, "应该只存输出预览"
    
    # 验证 RAG 节点的 trace 记录
    assert '"action": "rag_retrieval"' in template_content, "RAG 节点应该记录 action"
    assert 'docs_file = _save_docs_to_file(docs, trace_entry["step"])' in template_content, \
        "RAG 节点应该保存文档到外部文件"
    
    # 验证 Tool 节点的 trace 记录
    assert '"action": "tool_call"' in template_content, "Tool 节点应该记录 action"
    assert '"tool_input": tool_input[:100]' in template_content, "应该截断工具输入"
    assert '"tool_output": tool_output[:200]' in template_content, "应该截断工具输出"
    
    print("✅ 测试 3 通过: 节点函数正确记录 trace")


def test_run_agent_function_in_template():
    """测试 4: 验证模板包含 run_agent 函数"""
    
    template_file = Path(__file__).parent.parent.parent / "src" / "templates" / "agent_template.py.j2"
    template_content = template_file.read_text(encoding="utf-8")
    
    # 验证 run_agent 函数
    assert "def run_agent(user_input: str, return_trace: bool = False):" in template_content, \
        "应该有 run_agent 函数"
    assert "trace_file = _trace_manager.start_new_trace()" in template_content, \
        "应该启动新的 trace"
    assert "_trace_manager.save()" in template_content, \
        "应该保存 trace"
    assert "if return_trace:" in template_content, \
        "应该支持返回 trace"
    assert "trace = _trace_manager.load(trace_file)" in template_content, \
        "应该能加载 trace"
    assert "return output, trace" in template_content, \
        "应该返回 output 和 trace"
    
    print("✅ 测试 4 通过: run_agent 函数存在于模板中")


def test_save_docs_function_in_template():
    """测试 5: 验证模板包含 _save_docs_to_file 函数"""
    
    template_file = Path(__file__).parent.parent.parent / "src" / "templates" / "agent_template.py.j2"
    template_content = template_file.read_text(encoding="utf-8")
    
    # 验证 _save_docs_to_file 函数
    assert "def _save_docs_to_file(docs: List, step: int) -> str:" in template_content, \
        "应该有 _save_docs_to_file 函数"
    assert 'docs_dir = Path(__file__).parent / ".trace" / "docs"' in template_content, \
        "应该创建 .trace/docs 目录"
    assert "docs_dir.mkdir(parents=True, exist_ok=True)" in template_content, \
        "应该创建目录"
    assert "with open(filepath, 'w', encoding='utf-8') as f:" in template_content, \
        "应该写入文件"
    assert "json.dump(doc_contents, f, ensure_ascii=False, indent=2)" in template_content, \
        "应该保存为 JSON"
    
    print("✅ 测试 5 通过: _save_docs_to_file 函数存在于模板中")


def test_main_loop_trace_integration():
    """测试 6: 验证主循环集成了 trace"""
    
    template_file = Path(__file__).parent.parent.parent / "src" / "templates" / "agent_template.py.j2"
    template_content = template_file.read_text(encoding="utf-8")
    
    # 验证主循环中的 trace 集成
    assert '"trace_file": trace_file' in template_content, \
        "initial_state 应该包含 trace_file"
    assert 'print(f"   💾 Trace saved to: {trace_file}")' in template_content, \
        "应该打印 trace 保存位置"
    
    print("✅ 测试 6 通过: 主循环正确集成 trace")


def test_imports_in_template():
    """测试 7: 验证模板包含必要的导入"""
    
    template_file = Path(__file__).parent.parent.parent / "src" / "templates" / "agent_template.py.j2"
    template_content = template_file.read_text(encoding="utf-8")
    
    # 验证导入
    assert "import json" in template_content, "应该导入 json"
    assert "from pathlib import Path" in template_content, "应该导入 Path"
    assert "from datetime import datetime" in template_content, "应该导入 datetime"
    
    print("✅ 测试 7 通过: 必要的导入存在于模板中")


def test_optimization_comments():
    """测试 8: 验证优化注释"""
    
    template_file = Path(__file__).parent.parent.parent / "src" / "templates" / "agent_template.py.j2"
    template_content = template_file.read_text(encoding="utf-8")
    
    # 验证优化注释
    assert "# 🆕 Phase 4:" in template_content, "应该有 Phase 4 标记"
    assert "避免 Context Window 爆炸" in template_content, "应该说明优化目的"
    assert "只存元数据" in template_content, "应该说明存储策略"
    
    print("✅ 测试 8 通过: 优化注释清晰明确")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4 Task 4.1 简化测试 - 验证模板文件")
    print("=" * 60)
    
    # 运行所有测试
    test_trace_manager_class_in_template()
    test_trace_file_field_in_template()
    test_node_trace_recording_in_template()
    test_run_agent_function_in_template()
    test_save_docs_function_in_template()
    test_main_loop_trace_integration()
    test_imports_in_template()
    test_optimization_comments()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过! Task 4.1 模板修改完成!")
    print("=" * 60)
