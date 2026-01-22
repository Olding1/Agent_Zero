"""
Phase 4 Task 4.3 测试 - 验证 Compiler 升级

测试目标:
1. 验证 requirements.txt 包含 DeepEval 依赖
2. 验证生成 pip.conf 文件
3. 验证生成安装脚本 (install.sh 和 install.bat)
4. 验证安装脚本内容正确
"""

import pytest
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.compiler import Compiler


def test_requirements_include_deepeval():
    """测试 1: 验证 requirements.txt 包含 DeepEval"""
    
    template_dir = project_root / "src" / "templates"
    compiler = Compiler(template_dir)
    
    # 生成 requirements (包含测试依赖)
    requirements = compiler._generate_requirements(
        has_rag=False,
        has_tools=False,
        include_testing=True
    )
    
    # 验证包含 DeepEval 依赖
    assert "deepeval>=0.21.0" in requirements
    assert "pytest>=7.4.0" in requirements
    assert "pytest-json-report>=1.5.0" in requirements
    assert "# Testing dependencies (Phase 4 - DeepEval)" in requirements
    
    print("✅ 测试 1 通过: requirements.txt 包含 DeepEval 依赖")


def test_requirements_exclude_testing():
    """测试 2: 验证可以排除测试依赖"""
    
    template_dir = project_root / "src" / "templates"
    compiler = Compiler(template_dir)
    
    # 生成 requirements (不包含测试依赖)
    requirements = compiler._generate_requirements(
        has_rag=False,
        has_tools=False,
        include_testing=False
    )
    
    # 验证不包含 DeepEval 依赖
    assert "deepeval" not in requirements
    assert "pytest" not in requirements
    
    print("✅ 测试 2 通过: 可以排除测试依赖")


def test_generate_pip_config():
    """测试 3: 验证生成 pip.conf"""
    
    template_dir = project_root / "src" / "templates"
    compiler = Compiler(template_dir)
    
    pip_config = compiler._generate_pip_config()
    
    # 验证包含镜像源配置
    assert "[global]" in pip_config
    assert "index-url = https://pypi.tuna.tsinghua.edu.cn/simple" in pip_config
    assert "[install]" in pip_config
    assert "trusted-host = pypi.tuna.tsinghua.edu.cn" in pip_config
    
    print("✅ 测试 3 通过: pip.conf 生成正确")


def test_generate_install_script_sh():
    """测试 4: 验证生成 install.sh"""
    
    template_dir = project_root / "src" / "templates"
    compiler = Compiler(template_dir)
    
    install_sh = compiler._generate_install_script_sh()
    
    # 验证脚本内容
    assert "#!/bin/bash" in install_sh
    assert "Agent Zero - 依赖安装" in install_sh
    assert "清华大学镜像源" in install_sh
    assert "pip3 install -r requirements.txt" in install_sh
    assert "https://pypi.tuna.tsinghua.edu.cn/simple" in install_sh
    assert "pytest tests/test_deepeval.py" in install_sh
    
    print("✅ 测试 4 通过: install.sh 生成正确")


def test_generate_install_script_bat():
    """测试 5: 验证生成 install.bat"""
    
    template_dir = project_root / "src" / "templates"
    compiler = Compiler(template_dir)
    
    install_bat = compiler._generate_install_script_bat()
    
    # 验证脚本内容
    assert "@echo off" in install_bat
    assert "Agent Zero - 依赖安装" in install_bat
    assert "清华大学镜像源" in install_bat
    assert "pip install -r requirements.txt" in install_bat
    assert "https://pypi.tuna.tsinghua.edu.cn/simple" in install_bat
    assert "pytest tests\\test_deepeval.py" in install_bat  # Windows 路径
    
    print("✅ 测试 5 通过: install.bat 生成正确")


def test_env_template_updated():
    """测试 6: 验证 .env.template 更新"""
    
    template_dir = project_root / "src" / "templates"
    compiler = Compiler(template_dir)
    
    env_template = compiler._generate_env_template()
    
    # 验证包含必要的配置
    assert "RUNTIME_MODEL" in env_template
    assert "RUNTIME_API_KEY" in env_template
    assert "RUNTIME_BASE_URL" in env_template
    assert "TEMPERATURE" in env_template
    assert "EMBEDDING_PROVIDER" in env_template
    assert "EMBEDDING_MODEL_NAME" in env_template
    
    print("✅ 测试 6 通过: .env.template 更新正确")


def test_optimization_comments():
    """测试 7: 验证优化注释"""
    
    template_dir = project_root / "src" / "templates"
    compiler = Compiler(template_dir)
    
    # 检查 requirements 方法的注释
    import inspect
    source = inspect.getsource(compiler._generate_requirements)
    assert "Phase 4" in source
    assert "优化 2" in source or "预安装" in source
    
    # 检查 pip_config 方法的注释
    source = inspect.getsource(compiler._generate_pip_config)
    assert "Phase 4" in source
    assert "国内镜像源" in source
    
    print("✅ 测试 7 通过: 优化注释清晰")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4 Task 4.3 测试 - Compiler 升级")
    print("=" * 60)
    
    # 运行所有测试
    test_requirements_include_deepeval()
    test_requirements_exclude_testing()
    test_generate_pip_config()
    test_generate_install_script_sh()
    test_generate_install_script_bat()
    test_env_template_updated()
    test_optimization_comments()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过! Task 4.3 完成!")
    print("=" * 60)
