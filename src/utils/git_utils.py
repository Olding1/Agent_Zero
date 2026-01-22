"""
Git 版本管理工具

负责:
1. 初始化 Git 仓库
2. 提交代码变更
3. 创建版本标签
4. 回滚到历史版本
5. 查看历史记录
"""

import subprocess
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class GitCommit(BaseModel):
    """Git 提交信息"""
    hash: str = Field(description="提交哈希")
    message: str = Field(description="提交信息")
    author: str = Field(description="作者")
    date: str = Field(description="提交日期")
    tag: Optional[str] = Field(default=None, description="标签")


class GitUtils:
    """Git 版本管理工具类"""
    
    def __init__(self, repo_path: Path):
        """初始化 Git 工具
        
        Args:
            repo_path: Git 仓库路径
        """
        self.repo_path = Path(repo_path)
    
    def init_repo(self) -> bool:
        """初始化 Git 仓库
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # 检查是否已经是 Git 仓库
            if (self.repo_path / ".git").exists():
                return True
            
            # 初始化仓库
            subprocess.run(
                ["git", "init"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # 配置默认用户信息 (如果没有配置)
            self._ensure_git_config()
            
            return True
        except Exception as e:
            print(f"Git init 失败: {e}")
            return False
    
    def _ensure_git_config(self):
        """确保 Git 配置存在"""
        try:
            # 检查是否有全局配置
            result = subprocess.run(
                ["git", "config", "--global", "user.name"],
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                # 设置默认配置
                subprocess.run(
                    ["git", "config", "--global", "user.name", "Agent Zero"],
                    check=True
                )
                subprocess.run(
                    ["git", "config", "--global", "user.email", "agent@zero.ai"],
                    check=True
                )
        except Exception:
            pass  # 忽略配置错误
    
    def commit(
        self,
        message: str,
        files: Optional[List[str]] = None
    ) -> bool:
        """提交代码变更
        
        Args:
            message: 提交信息
            files: 要提交的文件列表 (None 表示所有文件)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # 添加文件
            if files:
                for file in files:
                    subprocess.run(
                        ["git", "add", file],
                        cwd=self.repo_path,
                        check=True
                    )
            else:
                subprocess.run(
                    ["git", "add", "."],
                    cwd=self.repo_path,
                    check=True
                )
            
            # 提交
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            return True
        except subprocess.CalledProcessError:
            # 可能没有变更
            return False
        except Exception as e:
            print(f"Git commit 失败: {e}")
            return False
    
    def tag(
        self,
        tag_name: str,
        message: Optional[str] = None
    ) -> bool:
        """创建版本标签
        
        Args:
            tag_name: 标签名称
            message: 标签信息 (可选)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if message:
                subprocess.run(
                    ["git", "tag", "-a", tag_name, "-m", message],
                    cwd=self.repo_path,
                    check=True
                )
            else:
                subprocess.run(
                    ["git", "tag", tag_name],
                    cwd=self.repo_path,
                    check=True
                )
            
            return True
        except Exception as e:
            print(f"Git tag 失败: {e}")
            return False
    
    def rollback(
        self,
        commit_hash: Optional[str] = None,
        tag_name: Optional[str] = None
    ) -> bool:
        """回滚到指定版本
        
        Args:
            commit_hash: 提交哈希 (优先)
            tag_name: 标签名称
        
        Returns:
            True if successful, False otherwise
        """
        try:
            target = commit_hash or tag_name
            if not target:
                # 回滚到上一个提交
                target = "HEAD~1"
            
            subprocess.run(
                ["git", "reset", "--hard", target],
                cwd=self.repo_path,
                check=True
            )
            
            return True
        except Exception as e:
            print(f"Git rollback 失败: {e}")
            return False
    
    def get_history(
        self,
        max_count: int = 10
    ) -> List[GitCommit]:
        """获取提交历史
        
        Args:
            max_count: 最多返回的提交数
        
        Returns:
            GitCommit 列表
        """
        try:
            # 获取提交历史
            result = subprocess.run(
                [
                    "git", "log",
                    f"--max-count={max_count}",
                    "--pretty=format:%H|%s|%an|%ai"
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|')
                if len(parts) >= 4:
                    commit = GitCommit(
                        hash=parts[0],
                        message=parts[1],
                        author=parts[2],
                        date=parts[3]
                    )
                    
                    # 检查是否有标签
                    tag = self._get_tag_for_commit(parts[0])
                    if tag:
                        commit.tag = tag
                    
                    commits.append(commit)
            
            return commits
        except Exception as e:
            print(f"Git history 失败: {e}")
            return []
    
    def _get_tag_for_commit(self, commit_hash: str) -> Optional[str]:
        """获取提交的标签
        
        Args:
            commit_hash: 提交哈希
        
        Returns:
            标签名称或 None
        """
        try:
            result = subprocess.run(
                ["git", "tag", "--points-at", commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            tags = result.stdout.strip().split('\n')
            return tags[0] if tags and tags[0] else None
        except Exception:
            return None
    
    def get_current_commit(self) -> Optional[str]:
        """获取当前提交哈希
        
        Returns:
            提交哈希或 None
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            return result.stdout.strip()
        except Exception:
            return None
    
    def has_changes(self) -> bool:
        """检查是否有未提交的变更
        
        Returns:
            True if has changes, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            return bool(result.stdout.strip())
        except Exception:
            return False


# ==================== 辅助函数 ====================

def create_version_tag(iteration: int) -> str:
    """创建版本标签名称
    
    Args:
        iteration: 迭代次数
    
    Returns:
        标签名称 (例如: v1.0.0, v1.0.1)
    """
    return f"v1.0.{iteration}"


def create_commit_message(
    iteration: int,
    test_passed: bool,
    changes: Optional[str] = None
) -> str:
    """创建提交信息
    
    Args:
        iteration: 迭代次数
        test_passed: 测试是否通过
        changes: 变更描述
    
    Returns:
        提交信息
    """
    status = "✅ Tests Passed" if test_passed else "❌ Tests Failed"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"Iteration {iteration}: {status}\n\n"
    message += f"Timestamp: {timestamp}\n"
    
    if changes:
        message += f"\nChanges:\n{changes}"
    
    return message
