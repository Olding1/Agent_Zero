from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import os

class AgentFactoryConfig(BaseModel):
    """AgentFactory 配置"""
    
    # Builder 配置
    builder_provider: str = Field(default="openai")
    builder_model: str = Field(default="gpt-4o")
    builder_api_key: str = Field(default="")
    builder_base_url: Optional[str] = None
    
    # 输出配置
    output_base_dir: Path = Field(default=Path("./agents"))
    template_dir: Path = Field(default=Path("./src/templates"))
    
    # 功能开关
    enable_git: bool = Field(default=True)
    enable_tests: bool = Field(default=True)
    
    # 交互与自动化配置
    interactive: bool = Field(default=True, description="是否启用交互式评审")
    auto_clarify: bool = Field(default=True, description="是否自动处理 PM 澄清")
    max_design_retries: int = Field(default=3, description="设计-仿真循环最大重试次数")
    max_build_retries: int = Field(default=3, description="编译-测试-修复循环最大重试次数")
    
    # Phase 4 优化
    include_deepeval: bool = Field(default=True)
    use_mirror_source: bool = Field(default=True)
    
    @classmethod
    def from_env(cls) -> "AgentFactoryConfig":
        """从环境变量加载"""
        return cls(
            builder_provider=os.getenv("BUILDER_PROVIDER", "openai"),
            builder_model=os.getenv("BUILDER_MODEL", "gpt-4o"),
            builder_api_key=os.getenv("BUILDER_API_KEY", ""),
            builder_base_url=os.getenv("BUILDER_BASE_URL"),
            # 其他配置保持默认或可以从 ENV 加载
        )
