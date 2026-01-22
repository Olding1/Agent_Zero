"""Environment manager for creating and managing virtual environments."""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class EnvSetupResult(BaseModel):
    """Result of environment setup."""

    success: bool = Field(..., description="Whether setup succeeded")
    venv_path: Path = Field(..., description="Path to virtual environment")
    python_executable: Path = Field(..., description="Path to Python executable")
    error_message: Optional[str] = Field(
        default=None, description="Error message if setup failed"
    )


class EnvManager:
    """Manager for creating and managing isolated Python virtual environments.
    
    Handles venv creation, dependency installation, and environment activation
    without requiring Docker.
    """

    def __init__(self, agent_dir: Path):
        """Initialize environment manager.
        
        Args:
            agent_dir: Path to agent project directory
        """
        self.agent_dir = Path(agent_dir).resolve()  # Convert to absolute path
        self.venv_path = self.agent_dir / ".venv"
        self._python_exe: Optional[Path] = None

    async def setup_environment(self) -> EnvSetupResult:
        """Create virtual environment and install dependencies.
        
        Returns:
            EnvSetupResult with success status and paths
        """
        try:
            # Create venv if it doesn't exist
            if not self.venv_path.exists():
                print(f"Creating virtual environment at {self.venv_path}...")
                await self._create_venv()

            # Get Python executable
            python_exe = self.get_python_executable()

            # Install requirements
            requirements_file = self.agent_dir / "requirements.txt"
            if requirements_file.exists():
                print("Installing dependencies...")
                install_success = await self.install_requirements()
                if not install_success:
                    return EnvSetupResult(
                        success=False,
                        venv_path=self.venv_path,
                        python_executable=python_exe,
                        error_message="Failed to install dependencies",
                    )

            return EnvSetupResult(
                success=True, venv_path=self.venv_path, python_executable=python_exe
            )

        except Exception as e:
            return EnvSetupResult(
                success=False,
                venv_path=self.venv_path,
                python_executable=Path(""),
                error_message=f"Environment setup failed: {str(e)}",
            )

    async def _create_venv(self) -> None:
        """Create virtual environment using venv module."""
        process = await self._run_command(
            [sys.executable, "-m", "venv", str(self.venv_path)], cwd=self.agent_dir
        )

        if process.returncode != 0:
            raise RuntimeError(f"Failed to create venv: {process.stderr}")

    def get_python_executable(self) -> Path:
        """Get path to Python executable in virtual environment.
        
        Returns:
            Path to Python executable
        """
        if self._python_exe is not None:
            return self._python_exe

        # Determine platform-specific path
        if sys.platform == "win32":
            python_exe = self.venv_path / "Scripts" / "python.exe"
        else:
            python_exe = self.venv_path / "bin" / "python"

        if not python_exe.exists():
            raise FileNotFoundError(f"Python executable not found at {python_exe}")

        self._python_exe = python_exe
        return python_exe

    async def install_requirements(self) -> bool:
        """Install dependencies from requirements.txt.
        
        Returns:
            True if installation succeeded, False otherwise
        """
        python_exe = self.get_python_executable()
        requirements_file = self.agent_dir / "requirements.txt"

        if not requirements_file.exists():
            print("No requirements.txt found, skipping installation")
            return True

        # Configure pip to use mirror (for faster installation in China)
        pip_config = self._get_pip_config()

        # Install dependencies
        cmd = [
            str(python_exe),
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_file),
        ]

        # Add mirror configuration
        if pip_config:
            cmd.extend(["-i", pip_config["index_url"]])

        print(f"Running: {' '.join(cmd)}")
        process = await self._run_command(cmd, cwd=self.agent_dir, timeout=300)

        if process.returncode != 0:
            print(f"Installation failed: {process.stderr}")
            return False

        print("Dependencies installed successfully")
        return True

    def _get_pip_config(self) -> Optional[dict]:
        """Get pip mirror configuration.
        
        Returns:
            Dictionary with pip configuration or None
        """
        # Use Tsinghua mirror for faster installation
        return {
            "index_url": "https://pypi.tuna.tsinghua.edu.cn/simple",
            "trusted_host": "pypi.tuna.tsinghua.edu.cn",
        }

    async def _run_command(
        self,
        cmd: list[str],
        cwd: Path,
        timeout: int = 60,
    ) -> subprocess.CompletedProcess:
        """Run command in subprocess.
        
        Args:
            cmd: Command and arguments
            cwd: Working directory
            timeout: Timeout in seconds
            
        Returns:
            CompletedProcess result
        """
        process = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return process

    def cleanup(self) -> None:
        """Remove virtual environment."""
        if self.venv_path.exists():
            import shutil

            shutil.rmtree(self.venv_path)
            print(f"Removed virtual environment at {self.venv_path}")
