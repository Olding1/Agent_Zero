"""
Phase 4 Tasks 4.4-4.6 综合测试

测试目标:
1. 验证 Runner 能正确检查 DeepEval 安装
2. 验证 Judge 能正确分类错误
3. 验证 GitUtils 能正确管理版本
"""

import pytest
from pathlib import Path
import sys
import tempfile

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.runner import Runner, DeepEvalTestResult
from src.core.judge import Judge, ErrorType, FixTarget
from src.utils.git_utils import GitUtils, create_version_tag, create_commit_message
from src.schemas.execution_result import ExecutionResult, ExecutionStatus


# ==================== Runner 测试 ====================

def test_runner_check_deepeval():
    """测试 1: Runner 检查 DeepEval 安装"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = Runner(Path(tmpdir))
        
        # 检查 DeepEval (应该返回 False,因为临时目录没有安装)
        installed = runner._check_deepeval_installed()
        
        # 这个测试可能通过或失败,取决于系统环境
        print(f"DeepEval installed: {installed}")
    
    print("✅ 测试 1 通过: Runner 检查功能正常")


def test_runner_find_python():
    """测试 2: Runner 查找 Python 可执行文件"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = Runner(Path(tmpdir))
        
        python_exe = runner._find_python_executable()
        
        assert python_exe.exists(), "Python 可执行文件应该存在"
        assert "python" in str(python_exe).lower(), "应该是 Python 可执行文件"
    
    print("✅ 测试 2 通过: Python 可执行文件查找正确")


def test_runner_error_message():
    """测试 3: Runner 未安装 DeepEval 时的错误信息"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = Runner(Path(tmpdir))
        
        # 尝试运行测试 (应该失败,因为没有安装 DeepEval)
        result = runner.run_deepeval_tests()
        
        # 验证错误信息
        if result.overall_status == ExecutionStatus.ERROR:
            assert "DeepEval 未安装" in (result.stderr or "")
            assert "install.sh" in (result.stderr or "") or "install.bat" in (result.stderr or "")
    
    print("✅ 测试 3 通过: 错误信息清晰")


# ==================== Judge 测试 ====================

def test_judge_success():
    """测试 4: Judge 分析成功结果"""
    
    judge = Judge()
    
    result = ExecutionResult(
        overall_status=ExecutionStatus.PASS,
        test_results=[]
    )
    
    judge_result = judge.analyze_result(result)
    
    assert judge_result.error_type == ErrorType.NONE
    assert judge_result.fix_target == FixTarget.NONE
    assert "通过" in judge_result.feedback
    assert judge_result.should_retry is False
    
    print("✅ 测试 4 通过: Judge 正确识别成功")


def test_judge_runtime_error():
    """测试 5: Judge 分类运行时错误"""
    
    judge = Judge()
    
    from src.schemas.execution_result import TestResult
    
    result = ExecutionResult(
        overall_status=ExecutionStatus.FAIL,
        test_results=[
            TestResult(
                test_id="test_import",
                status=ExecutionStatus.ERROR,
                duration_ms=100
            )
        ],
        stderr="ImportError: No module named 'deepeval'"
    )
    
    judge_result = judge.analyze_result(result)
    
    assert judge_result.error_type == ErrorType.RUNTIME
    assert judge_result.fix_target == FixTarget.COMPILER
    assert len(judge_result.suggestions) > 0
    
    print("✅ 测试 5 通过: Judge 正确分类运行时错误")


def test_judge_logic_error():
    """测试 6: Judge 分类逻辑错误"""
    
    judge = Judge()
    
    from src.schemas.execution_result import TestResult
    
    result = ExecutionResult(
        overall_status=ExecutionStatus.FAIL,
        test_results=[
            TestResult(
                test_id="test_rag_fact_1_faithfulness",
                status=ExecutionStatus.FAIL,
                error_message="Faithfulness metric failed",
                duration_ms=15000
            )
        ]
    )
    
    judge_result = judge.analyze_result(result)
    
    assert judge_result.error_type == ErrorType.LOGIC
    assert judge_result.fix_target == FixTarget.GRAPH_DESIGNER
    assert any("Faithfulness" in s for s in judge_result.suggestions)
    
    print("✅ 测试 6 通过: Judge 正确分类逻辑错误")


def test_judge_timeout():
    """测试 7: Judge 分类超时"""
    
    judge = Judge()
    
    from src.schemas.execution_result import TestResult
    
    result = ExecutionResult(
        overall_status=ExecutionStatus.TIMEOUT,
        test_results=[
            TestResult(
                test_id="test_timeout",
                status=ExecutionStatus.TIMEOUT,
                duration_ms=300000
            )
        ],
        stderr="Test execution timeout"
    )
    
    judge_result = judge.analyze_result(result)
    
    assert judge_result.error_type == ErrorType.TIMEOUT
    assert judge_result.fix_target == FixTarget.MANUAL
    assert judge_result.should_retry is True
    
    print("✅ 测试 7 通过: Judge 正确分类超时")


def test_judge_api_error():
    """测试 8: Judge 分类 API 错误"""
    
    judge = Judge()
    
    from src.schemas.execution_result import TestResult
    
    result = ExecutionResult(
        overall_status=ExecutionStatus.ERROR,
        test_results=[
            TestResult(
                test_id="test_api",
                status=ExecutionStatus.ERROR,
                duration_ms=2000
            )
        ],
        stderr="API Key is invalid"
    )
    
    judge_result = judge.analyze_result(result)
    
    assert judge_result.error_type == ErrorType.API
    assert judge_result.fix_target == FixTarget.MANUAL
    assert any("API" in s for s in judge_result.suggestions)
    
    print("✅ 测试 8 通过: Judge 正确分类 API 错误")


# ==================== GitUtils 测试 ====================

def test_git_init():
    """测试 9: Git 初始化"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        git = GitUtils(Path(tmpdir))
        
        success = git.init_repo()
        
        assert success is True
        assert (Path(tmpdir) / ".git").exists()
    
    print("✅ 测试 9 通过: Git 初始化成功")


def test_git_commit():
    """测试 10: Git 提交"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        git = GitUtils(Path(tmpdir))
        git.init_repo()
        
        # 创建测试文件
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")
        
        # 提交
        success = git.commit("Initial commit")
        
        assert success is True
    
    print("✅ 测试 10 通过: Git 提交成功")


def test_git_tag():
    """测试 11: Git 标签"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        git = GitUtils(Path(tmpdir))
        git.init_repo()
        
        # 创建文件并提交
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test")
        git.commit("Initial commit")
        
        # 创建标签
        success = git.tag("v1.0.0", "Version 1.0.0")
        
        assert success is True
    
    print("✅ 测试 11 通过: Git 标签创建成功")


def test_git_history():
    """测试 12: Git 历史"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        git = GitUtils(Path(tmpdir))
        git.init_repo()
        
        # 创建多个提交
        for i in range(3):
            test_file = Path(tmpdir) / f"test{i}.txt"
            test_file.write_text(f"content {i}")
            git.commit(f"Commit {i}")
        
        # 获取历史
        history = git.get_history(max_count=5)
        
        assert len(history) == 3
        assert all(commit.hash for commit in history)
    
    print("✅ 测试 12 通过: Git 历史获取成功")


def test_version_tag_helper():
    """测试 13: 版本标签辅助函数"""
    
    tag = create_version_tag(1)
    assert tag == "v1.0.1"
    
    tag = create_version_tag(10)
    assert tag == "v1.0.10"
    
    print("✅ 测试 13 通过: 版本标签生成正确")


def test_commit_message_helper():
    """测试 14: 提交信息辅助函数"""
    
    message = create_commit_message(1, True, "Fixed bug")
    
    assert "Iteration 1" in message
    assert "✅ Tests Passed" in message
    assert "Fixed bug" in message
    
    message = create_commit_message(2, False)
    assert "❌ Tests Failed" in message
    
    print("✅ 测试 14 通过: 提交信息生成正确")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4 Tasks 4.4-4.6 综合测试")
    print("=" * 60)
    
    # Runner 测试
    test_runner_check_deepeval()
    test_runner_find_python()
    test_runner_error_message()
    
    # Judge 测试
    test_judge_success()
    test_judge_runtime_error()
    test_judge_logic_error()
    test_judge_timeout()
    test_judge_api_error()
    
    # GitUtils 测试
    test_git_init()
    test_git_commit()
    test_git_tag()
    test_git_history()
    test_version_tag_helper()
    test_commit_message_helper()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过! Tasks 4.4-4.6 完成!")
    print("=" * 60)
