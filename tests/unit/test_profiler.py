"""Unit tests for Profiler module."""

import pytest
from pathlib import Path
import tempfile

from src.core.profiler import Profiler
from src.schemas import DataProfile


@pytest.fixture
def profiler():
    """Create a Profiler instance."""
    return Profiler()


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file."""
    file_path = tmp_path / "sample.txt"
    content = "This is a sample text file.\n" * 100
    file_path.write_text(content, encoding='utf-8')
    return file_path


@pytest.fixture
def sample_markdown_file(tmp_path):
    """Create a sample markdown file with table."""
    file_path = tmp_path / "sample.md"
    content = """# Sample Document

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

Some text content here.
"""
    file_path.write_text(content, encoding='utf-8')
    return file_path


def test_analyze_single_file(profiler, sample_text_file):
    """Test analyzing a single file."""
    profile = profiler.analyze([sample_text_file])
    
    assert profile.total_files == 1
    assert profile.total_size_bytes > 0
    assert profile.estimated_tokens > 0
    assert len(profile.files) == 1
    assert profile.files[0].file_type == "txt"
    assert len(profile.files[0].file_hash) == 32  # MD5 hash length


def test_analyze_multiple_files(profiler, sample_text_file, sample_markdown_file):
    """Test analyzing multiple files."""
    profile = profiler.analyze([sample_text_file, sample_markdown_file])
    
    assert profile.total_files == 2
    assert len(profile.files) == 2
    assert profile.total_size_bytes > 0


def test_table_detection(profiler, sample_markdown_file):
    """Test table detection in markdown."""
    profile = profiler.analyze([sample_markdown_file])
    
    assert profile.has_tables is True


def test_language_detection_english(profiler, sample_text_file):
    """Test English language detection."""
    profile = profiler.analyze([sample_text_file])
    
    assert "en-US" in profile.languages_detected


def test_language_detection_chinese(profiler, tmp_path):
    """Test Chinese language detection."""
    file_path = tmp_path / "chinese.txt"
    file_path.write_text("这是一个中文文档。" * 50, encoding='utf-8')
    
    profile = profiler.analyze([file_path])
    
    assert "zh-CN" in profile.languages_detected


def test_hash_calculation(profiler, sample_text_file):
    """Test MD5 hash calculation."""
    hash1 = profiler._calculate_hash(sample_text_file)
    hash2 = profiler._calculate_hash(sample_text_file)
    
    # Same file should have same hash
    assert hash1 == hash2
    assert len(hash1) == 32


def test_save_and_load_profile(profiler, sample_text_file, tmp_path):
    """Test saving and loading data profile."""
    # Analyze and save
    profile = profiler.analyze([sample_text_file])
    output_path = tmp_path / "profile.json"
    profiler.save_profile(profile, output_path)
    
    assert output_path.exists()
    
    # Load
    loaded = profiler.load_profile(output_path)
    
    assert loaded.total_files == profile.total_files
    assert loaded.total_size_bytes == profile.total_size_bytes
    assert loaded.estimated_tokens == profile.estimated_tokens


def test_analyze_empty_list(profiler):
    """Test analyzing empty file list."""
    with pytest.raises(ValueError, match="No files provided"):
        profiler.analyze([])


def test_analyze_nonexistent_file(profiler):
    """Test analyzing non-existent file."""
    # Should not raise exception, but skip the file
    profile = profiler.analyze([Path("nonexistent.txt")])
    
    assert profile.total_files == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
