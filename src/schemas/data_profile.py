"""Data profile schema for file analysis results."""

from pydantic import BaseModel, Field
from typing import List, Optional
from pathlib import Path


class FileInfo(BaseModel):
    """Information about a single file."""
    
    path: str = Field(..., description="File path")
    file_hash: str = Field(..., description="MD5 hash of the file")
    file_type: str = Field(..., description="File type (pdf, docx, txt, md, etc.)")
    size_bytes: int = Field(..., description="File size in bytes")


class DataProfile(BaseModel):
    """Profile of analyzed data/files.
    
    This schema stores the results of file analysis performed by the Profiler module.
    """
    
    files: List[FileInfo] = Field(..., description="List of analyzed files")
    total_size_bytes: int = Field(..., description="Total size of all files")
    text_density: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Text density (0-1, higher means more text content)"
    )
    has_tables: bool = Field(default=False, description="Whether files contain tables")
    estimated_tokens: int = Field(..., ge=0, description="Estimated total tokens")
    languages_detected: List[str] = Field(
        default_factory=list, 
        description="Detected languages in the content"
    )
    
    # Metadata
    analysis_timestamp: Optional[str] = Field(
        default=None, 
        description="ISO timestamp of when analysis was performed"
    )
    
    @property
    def total_files(self) -> int:
        """Get total number of files."""
        return len(self.files)
    
    @property
    def avg_file_size(self) -> float:
        """Get average file size in bytes."""
        if self.total_files == 0:
            return 0.0
        return self.total_size_bytes / self.total_files
