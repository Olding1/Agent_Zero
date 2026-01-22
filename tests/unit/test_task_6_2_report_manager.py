"""
Unit tests for ReportManager - Phase 6
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from src.core.report_manager import ReportManager
from src.schemas.test_report import (
    TestCaseReport,
    IterationReport,
    AgentEvolutionHistory
)


@pytest.fixture
def temp_agent_dir(tmp_path):
    """创建临时Agent目录"""
    agent_dir = tmp_path / "test_agent"
    agent_dir.mkdir()
    return agent_dir


@pytest.fixture
def report_manager(temp_agent_dir):
    """创建ReportManager实例"""
    return ReportManager(temp_agent_dir)


@pytest.fixture
def sample_iteration_report():
    """创建示例迭代报告"""
    return IterationReport(
        iteration_id=0,
        timestamp=datetime.now(),
        agent_name="TestAgent",
        total_tests=5,
        passed_tests=3,
        failed_tests=2,
        pass_rate=0.6,
        test_cases=[
            TestCaseReport(
                test_id="test_1",
                test_name="test_basic",
                status="PASSED",
                metrics={"faithfulness": 0.9},
                actual_output="Good output",
                expected_output="Expected output",
                duration_seconds=1.5
            ),
            TestCaseReport(
                test_id="test_2",
                test_name="test_rag",
                status="FAILED",
                metrics={"faithfulness": 0.4, "recall": 0.3},
                actual_output="Bad output",
                expected_output="Expected output",
                error_message="Recall too low",
                duration_seconds=2.0
            ),
        ],
        error_types={"rag_quality": 1, "logic": 1},
        fix_target="rag_builder",
        judge_feedback="RAG检索质量不足",
        graph_snapshot={"nodes": 2, "edges": 1},
        avg_metrics={"avg_faithfulness": 0.65}
    )


class TestReportManager:
    """ReportManager测试类"""
    
    def test_initialization(self, report_manager, temp_agent_dir):
        """测试初始化"""
        assert report_manager.agent_dir == temp_agent_dir
        assert report_manager.reports_dir.exists()
        assert report_manager.reports_dir == temp_agent_dir / ".reports"
    
    def test_save_iteration_report(self, report_manager, sample_iteration_report):
        """测试保存迭代报告"""
        # 保存报告
        filepath = report_manager.save_iteration_report(sample_iteration_report)
        
        # 验证文件存在
        assert filepath.exists()
        assert filepath.parent == report_manager.reports_dir
        assert filepath.name.startswith("iteration_0_")
        assert filepath.suffix == ".json"
        
        # 验证文件内容
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["iteration_id"] == 0
        assert data["agent_name"] == "TestAgent"
        assert data["total_tests"] == 5
        assert data["pass_rate"] == 0.6
    
    def test_load_iteration_report(self, report_manager, sample_iteration_report):
        """测试加载迭代报告"""
        # 先保存
        report_manager.save_iteration_report(sample_iteration_report)
        
        # 加载
        loaded_report = report_manager.load_iteration_report(0)
        
        assert loaded_report is not None
        assert loaded_report.iteration_id == 0
        assert loaded_report.agent_name == "TestAgent"
        assert loaded_report.total_tests == 5
        assert loaded_report.passed_tests == 3
        assert loaded_report.pass_rate == 0.6
    
    def test_load_nonexistent_report(self, report_manager):
        """测试加载不存在的报告"""
        loaded_report = report_manager.load_iteration_report(999)
        assert loaded_report is None
    
    def test_update_history(self, report_manager, sample_iteration_report):
        """测试更新历史"""
        # 保存第一个报告
        report_manager.save_iteration_report(sample_iteration_report)
        
        # 验证历史文件存在
        assert report_manager.history_file.exists()
        
        # 加载历史
        history = report_manager.load_history()
        assert len(history.iterations) == 1
        assert history.iterations[0].iteration_id == 0
    
    def test_multiple_iterations(self, report_manager, sample_iteration_report):
        """测试多次迭代"""
        # 保存多个迭代
        for i in range(3):
            report = sample_iteration_report.model_copy()
            report.iteration_id = i
            report.pass_rate = 0.6 + i * 0.1
            report_manager.save_iteration_report(report)
        
        # 加载历史
        history = report_manager.load_history()
        assert len(history.iterations) == 3
        
        # 验证排序
        for i, it in enumerate(history.iterations):
            assert it.iteration_id == i
    
    def test_generate_summary(self, report_manager, sample_iteration_report):
        """测试生成总结"""
        # 保存报告
        report_manager.save_iteration_report(sample_iteration_report)
        
        # 生成总结
        summary = report_manager.generate_summary(0)
        
        # 验证总结内容
        assert "迭代 0 总结" in summary
        assert "总测试数: 5" in summary
        assert "通过: 3" in summary
        assert "失败: 2" in summary
        assert "通过率: 60.0%" in summary
        assert "rag_quality" in summary
        assert "RAG检索质量不足" in summary
    
    def test_generate_evolution_summary(self, report_manager, sample_iteration_report):
        """测试生成进化总结"""
        # 保存多个迭代
        for i in range(3):
            report = sample_iteration_report.model_copy()
            report.iteration_id = i
            report.pass_rate = 0.6 + i * 0.15
            report.passed_tests = 3 + i
            report_manager.save_iteration_report(report)
        
        # 生成进化总结
        summary = report_manager.generate_evolution_summary()
        
        # 验证总结内容
        assert "Agent 进化总结" in summary
        assert "总迭代次数: 3" in summary
        assert "初始通过率: 60.0%" in summary
        assert "最终通过率: 90.0%" in summary
        assert "改进幅度: +30.0%" in summary
        assert "迭代 0:" in summary
        assert "迭代 1:" in summary
        assert "迭代 2:" in summary
    
    def test_rebuild_history(self, report_manager, sample_iteration_report):
        """测试重建历史"""
        # 保存多个报告
        for i in range(2):
            report = sample_iteration_report.model_copy()
            report.iteration_id = i
            report_manager.save_iteration_report(report)
        
        # 删除历史文件
        report_manager.history_file.unlink()
        
        # 重建历史
        history = report_manager.load_history()
        
        # 验证重建成功
        assert len(history.iterations) == 2
        assert history.iterations[0].iteration_id == 0
        assert history.iterations[1].iteration_id == 1
    
    def test_update_existing_iteration(self, report_manager, sample_iteration_report):
        """测试更新现有迭代"""
        # 保存初始报告
        report_manager.save_iteration_report(sample_iteration_report)
        
        # 更新报告
        updated_report = sample_iteration_report.model_copy()
        updated_report.pass_rate = 0.8
        updated_report.passed_tests = 4
        updated_report.git_commit_hash = "abc123"
        report_manager.save_iteration_report(updated_report)
        
        # 加载历史
        history = report_manager.load_history()
        
        # 验证只有一个迭代,且是更新后的
        assert len(history.iterations) == 1
        assert history.iterations[0].pass_rate == 0.8
        assert history.iterations[0].passed_tests == 4
        assert history.iterations[0].git_commit_hash == "abc123"


class TestAgentEvolutionHistory:
    """AgentEvolutionHistory测试类"""
    
    def test_get_pass_rate_trend(self):
        """测试获取通过率趋势"""
        history = AgentEvolutionHistory(
            agent_name="TestAgent",
            iterations=[
                IterationReport(
                    iteration_id=0,
                    agent_name="TestAgent",
                    total_tests=5,
                    passed_tests=3,
                    failed_tests=2,
                    pass_rate=0.6
                ),
                IterationReport(
                    iteration_id=1,
                    agent_name="TestAgent",
                    total_tests=5,
                    passed_tests=4,
                    failed_tests=1,
                    pass_rate=0.8
                ),
            ]
        )
        
        trend = history.get_pass_rate_trend()
        assert trend == [0.6, 0.8]
    
    def test_get_metric_trend(self):
        """测试获取指标趋势"""
        history = AgentEvolutionHistory(
            agent_name="TestAgent",
            iterations=[
                IterationReport(
                    iteration_id=0,
                    agent_name="TestAgent",
                    total_tests=5,
                    passed_tests=3,
                    failed_tests=2,
                    pass_rate=0.6,
                    avg_metrics={"avg_faithfulness": 0.7}
                ),
                IterationReport(
                    iteration_id=1,
                    agent_name="TestAgent",
                    total_tests=5,
                    passed_tests=4,
                    failed_tests=1,
                    pass_rate=0.8,
                    avg_metrics={"avg_faithfulness": 0.85}
                ),
            ]
        )
        
        trend = history.get_metric_trend("avg_faithfulness")
        assert trend == [0.7, 0.85]
    
    def test_get_improvement_summary(self):
        """测试获取改进总结"""
        history = AgentEvolutionHistory(
            agent_name="TestAgent",
            iterations=[
                IterationReport(
                    iteration_id=0,
                    agent_name="TestAgent",
                    total_tests=5,
                    passed_tests=3,
                    failed_tests=2,
                    pass_rate=0.6
                ),
                IterationReport(
                    iteration_id=1,
                    agent_name="TestAgent",
                    total_tests=5,
                    passed_tests=5,
                    failed_tests=0,
                    pass_rate=1.0
                ),
            ]
        )
        
        summary = history.get_improvement_summary()
        
        assert summary["total_iterations"] == 2
        assert summary["initial_pass_rate"] == 0.6
        assert summary["final_pass_rate"] == 1.0
        assert summary["improvement"] == 0.4
        assert summary["initial_passed"] == 3
        assert summary["final_passed"] == 5
