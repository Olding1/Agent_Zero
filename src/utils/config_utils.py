"""
Configuration utilities for Agent Zero v7.0.

Provides atomic file writing to prevent configuration corruption during runtime updates.
"""

import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Union

def atomic_write_json(path: Union[str, Path], data: Dict[str, Any], indent: int = 2):
    """
    Atomically write a JSON file.
    
    Writes data to a temporary file first, then renames it to the target path.
    This ensures that the target file is never in a half-written state.
    
    Args:
        path: Target file path
        data: JSON data to write
        indent: JSON indentation
    """
    path = Path(path)
    # Create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create temp file in the same directory to ensure atomic rename works across filesystems
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, text=True)
    
    try:
        with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        # Atomic rename
        os.replace(tmp_path, path)
    except Exception:
        # Cleanup temp file on error
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

def load_json_safe(path: Union[str, Path], default: Any = None) -> Any:
    """
     safely load a JSON file with default fallback.
    
    Args:
        path: File path
        default: Default value if file doesn't exist or load fails
        
    Returns:
        Loaded data or default
    """
    path = Path(path)
    if not path.exists():
        return default
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default
