"""
Phase 6 Task 6.5: Compiler Optimizer

Optimizes compiler configuration (dependencies and environment).
"""

import re
from typing import List, Optional
from pathlib import Path
from ..core.compiler import Compiler
from ..schemas.analysis_result import AnalysisResult


class CompilerOptimizer:
    """Compiler 配置优化器
    
    主要处理:
    1. 依赖项问题 (ImportError, ModuleNotFoundError)
    2. 系统配置问题 (.env, requirements.txt)
    """
    
    def __init__(self, compiler: Compiler):
        """初始化优化器
        
        Args:
            compiler: Compiler 实例
        """
        self.compiler = compiler
    
    async def optimize_dependencies(
        self,
        agent_dir: Path,
        analysis: AnalysisResult,
        error_message: str
    ) -> bool:
        """优化依赖项配置
        
        策略:
        1. 解析错误信息,提取缺失的包名
        2. 添加到 requirements.txt
        3. 不重新编译,只更新依赖文件
        
        Args:
            agent_dir: Agent 目录
            analysis: 分析结果
            error_message: 错误信息
            
        Returns:
            是否成功优化
        """
        # 1. 提取缺失的包名
        missing_packages = self._extract_missing_packages(error_message)
        
        if not missing_packages:
            return False
        
        # 2. 更新 requirements.txt
        requirements_file = agent_dir / "requirements.txt"
        if requirements_file.exists():
            current_content = requirements_file.read_text(encoding="utf-8")
            
            # 添加缺失的包
            new_lines = []
            for pkg in missing_packages:
                if pkg not in current_content:
                    new_lines.append(f"{pkg}>=0.1.0  # Auto-added by optimizer")
            
            if new_lines:
                updated_content = current_content + "\n\n# Auto-added dependencies\n" + "\n".join(new_lines)
                requirements_file.write_text(updated_content, encoding="utf-8")
                print(f"📦 添加依赖: {', '.join(missing_packages)}")
                return True
        
        return False
    
    def _extract_missing_packages(self, error_message: str) -> List[str]:
        """从错误信息中提取缺失的包名
        
        Args:
            error_message: 错误信息
            
        Returns:
            缺失的包名列表
        """
        packages = []
        
        # 匹配 "No module named 'xxx'"
        pattern1 = r"No module named ['\"]([^'\"]+)['\"]"
        matches1 = re.findall(pattern1, error_message)
        packages.extend(matches1)
        
        # 匹配 "ImportError: cannot import name 'xxx' from 'yyy'"
        pattern2 = r"cannot import name ['\"]([^'\"]+)['\"] from ['\"]([^'\"]+)['\"]"
        matches2 = re.findall(pattern2, error_message)
        for _, module in matches2:
            packages.append(module)
        
        # 去重并清理
        return list(set(pkg.split('.')[0] for pkg in packages))
    
    async def optimize_env_config(
        self,
        agent_dir: Path,
        analysis: AnalysisResult
    ) -> bool:
        """优化环境配置 (.env)
        
        策略:
        1. 检查 API Key 配置
        2. 检查 Base URL 配置
        3. 自动从系统环境复制配置
        
        Args:
            agent_dir: Agent 目录
            analysis: 分析结果
            
        Returns:
            是否成功优化
        """
        env_file = agent_dir / ".env"
        if not env_file.exists():
            # 从 .env.template 复制
            template = agent_dir / ".env.template"
            if template.exists():
                env_file.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
                print(f"📝 创建 .env 文件")
                return True
        
        return False
