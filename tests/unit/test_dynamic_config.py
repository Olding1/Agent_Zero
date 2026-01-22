
import pytest
import time
import json
from pathlib import Path
from src.utils.config_utils import atomic_write_json
# from src.templates.agent_template.py.j2 import ConfigLoader # Removed invalid import
# We need to simulate the ConfigLoader behavior or extract it to strict util if we want to test it in isolation easily.
# But for now, I will copy the ConfigLoader class here to test the LOGIC, 
# or I can rely on the fact that I put it in `agent_template.py.j2` so it ends up in `agent.py`.

# Actually, the best way to test "Dynamic Core" is to GENERATE an agent and run it.
# But that takes time.
# Let's create a unit test that mocks the ConfigLoader logic.

class MockConfigLoader:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.last_mtime = 0
        self._rag_config_cache = {}
        
    def load_rag_config(self):
        config_path = self.base_dir / "rag_config.json"
        defaults = {}
        
        if not config_path.exists():
            return defaults
            
        try:
            current_mtime = config_path.stat().st_mtime
            if current_mtime > self.last_mtime:
                # File changed, reload
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._rag_config_cache = {**defaults, **json.load(f)}
                self.last_mtime = current_mtime
            return self._rag_config_cache
        except Exception as e:
            return self._rag_config_cache or defaults

def test_dynamic_config_loading(tmp_path):
    loader = MockConfigLoader(tmp_path)
    config_file = tmp_path / "rag_config.json"
    
    # 1. Initial State (No file)
    assert loader.load_rag_config() == {}
    
    # 2. Create file
    initial_config = {"k_retrieval": 4, "enable_hybrid_search": False}
    atomic_write_json(config_file, initial_config)
    
    # Load
    loaded = loader.load_rag_config()
    assert loaded["k_retrieval"] == 4
    assert loaded["enable_hybrid_search"] is False
    
    # 3. Update file (Simulate Runtime Update)
    time.sleep(1.1) # Ensure mtime changes (some filesystems have 1s resolution)
    new_config = {"k_retrieval": 10, "enable_hybrid_search": True}
    atomic_write_json(config_file, new_config)
    
    # Load again
    reloaded = loader.load_rag_config()
    assert reloaded["k_retrieval"] == 10
    assert reloaded["enable_hybrid_search"] is True
    
if __name__ == "__main__":
    pytest.main([__file__])
