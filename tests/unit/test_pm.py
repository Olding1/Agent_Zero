"""Unit tests for PM (Product Manager) module."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from src.core.pm import PM
from src.schemas import ProjectMeta, TaskType
from src.llm import BuilderClient


@pytest.fixture
def mock_builder_client():
    """Create a mock builder client."""
    client = MagicMock(spec=BuilderClient)
    return client


@pytest.fixture
def pm(mock_builder_client):
    """Create a PM instance with mock client."""
    return PM(mock_builder_client)


@pytest.mark.asyncio
async def test_analyze_requirements_chat(pm, mock_builder_client):
    """Test analyzing a simple chat requirement."""
    # Mock LLM response
    mock_response = ProjectMeta(
        agent_name="friendly_chatbot",
        description="A friendly chatbot assistant",
        has_rag=False,
        task_type=TaskType.CHAT,
        language="en-US",
        user_intent_summary="Create a friendly chatbot",
        clarification_needed=False,
    )
    
    mock_builder_client.call = AsyncMock(return_value=mock_response)
    
    # Test
    result = await pm.analyze_requirements("Create a friendly chatbot")
    
    assert result.agent_name == "friendly_chatbot"
    assert result.task_type == TaskType.CHAT
    assert result.has_rag is False
    assert result.clarification_needed is False


@pytest.mark.asyncio
async def test_analyze_requirements_with_files(pm, mock_builder_client):
    """Test analyzing requirement with file uploads."""
    # Mock LLM response
    mock_response = ProjectMeta(
        agent_name="document_qa",
        description="Q&A system for uploaded documents",
        has_rag=True,
        task_type=TaskType.RAG,
        language="zh-CN",
        user_intent_summary="Answer questions about documents",
        clarification_needed=False,
    )
    
    mock_builder_client.call = AsyncMock(return_value=mock_response)
    
    # Test with file paths
    file_paths = [Path("test.pdf"), Path("doc.docx")]
    result = await pm.analyze_requirements(
        "帮我分析这些文档",
        file_paths=file_paths
    )
    
    assert result.has_rag is True
    assert result.task_type == TaskType.RAG
    assert result.file_paths == ["test.pdf", "doc.docx"]


@pytest.mark.asyncio
async def test_fallback_analysis(pm, mock_builder_client):
    """Test fallback analysis when LLM fails."""
    # Mock LLM to raise exception
    mock_builder_client.call = AsyncMock(side_effect=Exception("API Error"))
    
    # Test fallback
    result = await pm.analyze_requirements("创建一个聊天机器人")
    
    # Should still return a valid ProjectMeta
    assert isinstance(result, ProjectMeta)
    assert result.language == "zh-CN"  # Detected Chinese
    assert result.task_type == TaskType.CHAT


@pytest.mark.asyncio
async def test_ask_clarification(pm, mock_builder_client):
    """Test generating clarification questions."""
    project_meta = ProjectMeta(
        agent_name="test_agent",
        description="Test description",
        has_rag=False,
        task_type=TaskType.CHAT,
        language="en-US",
        user_intent_summary="Test intent",
        clarification_needed=True,
        clarification_questions=None,
    )
    
    # Mock LLM response
    mock_builder_client.call = AsyncMock(
        return_value="1. What specific features do you need?\n2. What is the expected response format?"
    )
    
    questions = await pm.ask_clarification(project_meta)
    
    assert len(questions) == 2
    assert "features" in questions[0].lower()
    assert "format" in questions[1].lower()


def test_save_and_load_project_meta(pm, tmp_path):
    """Test saving and loading project metadata."""
    project_meta = ProjectMeta(
        agent_name="test_agent",
        description="Test description",
        has_rag=False,
        task_type=TaskType.CHAT,
        language="en-US",
        user_intent_summary="Test intent",
    )
    
    # Save
    output_path = tmp_path / "project_meta.json"
    pm.save_project_meta(project_meta, output_path)
    
    assert output_path.exists()
    
    # Load
    loaded = pm.load_project_meta(output_path)
    
    assert loaded.agent_name == project_meta.agent_name
    assert loaded.task_type == project_meta.task_type
    assert loaded.has_rag == project_meta.has_rag


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
