"""Profiler - Data analysis module for file profiling.

This module analyzes uploaded files and generates DataProfile metadata.
"""

import hashlib
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..schemas import DataProfile, FileInfo


class Profiler:
    """Profiler analyzes files and generates data profiles.
    
    The Profiler is responsible for:
    1. File type detection
    2. MD5 hash calculation (for incremental updates)
    3. Text density analysis
    4. Table detection
    5. Token count estimation
    """
    
    def __init__(self):
        """Initialize Profiler."""
        pass
    
    def analyze(self, file_paths: List[Path]) -> DataProfile:
        """Analyze files and return a DataProfile.
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            DataProfile with analysis results
        """
        if not file_paths:
            raise ValueError("No files provided for analysis")
        
        files_info = []
        total_size = 0
        total_text_length = 0
        has_tables = False
        languages = set()
        
        for file_path in file_paths:
            if not file_path.exists():
                print(f"Warning: File not found: {file_path}")
                continue
            
            # Analyze individual file
            file_info = self._analyze_file(file_path)
            files_info.append(file_info)
            total_size += file_info.size_bytes
            
            # Accumulate text for density calculation
            try:
                text_content = self._extract_text(file_path)
                total_text_length += len(text_content)
                
                # Detect language
                lang = self._detect_language(text_content)
                if lang:
                    languages.add(lang)
                
                # Check for tables (simple heuristic)
                if self._has_tables(text_content, file_path):
                    has_tables = True
                    
            except Exception as e:
                print(f"Warning: Could not extract text from {file_path}: {e}")
        
        # Calculate text density (simplified)
        # Text density = ratio of text content to total file size
        text_density = min(1.0, total_text_length / max(total_size, 1) * 0.5)
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = total_text_length // 4
        
        return DataProfile(
            files=files_info,
            total_size_bytes=total_size,
            text_density=text_density,
            has_tables=has_tables,
            estimated_tokens=estimated_tokens,
            languages_detected=list(languages),
            analysis_timestamp=datetime.now().isoformat(),
        )
    
    def _analyze_file(self, file_path: Path) -> FileInfo:
        """Analyze a single file.
        
        Args:
            file_path: Path to file
            
        Returns:
            FileInfo with file metadata
        """
        # Calculate MD5 hash
        file_hash = self._calculate_hash(file_path)
        
        # Get file type from extension
        file_type = file_path.suffix.lstrip('.').lower() or 'unknown'
        
        # Get file size
        size_bytes = file_path.stat().st_size
        
        return FileInfo(
            path=str(file_path),
            file_hash=file_hash,
            file_type=file_type,
            size_bytes=size_bytes,
        )
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash as hex string
        """
        md5_hash = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        
        return md5_hash.hexdigest()
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text content from file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Extracted text content
        """
        file_type = file_path.suffix.lower()
        
        # Handle different file types
        if file_type in ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml']:
            # Plain text files
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        elif file_type == '.pdf':
            # PDF files - use pymupdf if available
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text
            except ImportError:
                print("Warning: pymupdf not installed, cannot extract PDF text")
                return ""
            except Exception as e:
                print(f"Warning: Error extracting PDF text: {e}")
                return ""
        
        elif file_type in ['.docx', '.doc']:
            # Word documents - use python-docx if available
            try:
                import docx
                doc = docx.Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs])
                return text
            except ImportError:
                print("Warning: python-docx not installed, cannot extract DOCX text")
                return ""
            except Exception as e:
                print(f"Warning: Error extracting DOCX text: {e}")
                return ""
        
        else:
            # Unsupported file type
            return ""
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Detect language of text content.
        
        Args:
            text: Text content
            
        Returns:
            Language code (e.g., 'zh-CN', 'en-US') or None
        """
        if not text:
            return None
        
        # Simple heuristic: check for Chinese characters
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text[:1000])
        
        if has_chinese:
            return "zh-CN"
        else:
            return "en-US"
    
    def _has_tables(self, text: str, file_path: Path) -> bool:
        """Check if content contains tables.
        
        Args:
            text: Text content
            file_path: Path to file
            
        Returns:
            True if tables detected, False otherwise
        """
        # Simple heuristics for table detection
        
        # Check for markdown tables
        if '|' in text and text.count('|') > 10:
            lines = text.split('\n')
            table_lines = [line for line in lines if '|' in line]
            if len(table_lines) > 3:
                return True
        
        # Check for CSV-like content
        if file_path.suffix.lower() == '.csv':
            return True
        
        # Check for tab-separated content
        if '\t' in text and text.count('\t') > 20:
            return True
        
        return False
    
    def save_profile(self, profile: DataProfile, output_path: Path) -> None:
        """Save DataProfile to JSON file.
        
        Args:
            profile: DataProfile to save
            output_path: Path to save JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(profile.model_dump_json(indent=2))
    
    def load_profile(self, input_path: Path) -> DataProfile:
        """Load DataProfile from JSON file.
        
        Args:
            input_path: Path to JSON file
            
        Returns:
            DataProfile object
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            return DataProfile.model_validate_json(f.read())
