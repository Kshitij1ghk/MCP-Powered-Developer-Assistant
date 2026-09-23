import os
import subprocess
import shlex
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from src.config import ALLOWED_DIR

class TestMCPServer:
    """
    Test MCP Server:
    Executes controlled pytest runs with strict sandboxing and timeouts.
    Never exposes an arbitrary shell.
    """
    def __init__(self, workspace_dir: Path = None):
        self.workspace_dir = (workspace_dir or ALLOWED_DIR).resolve()

    def run_test_suite(
        self,
        test_command: str = "pytest",
        target_test: str = "",
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """
        Runs a controlled pytest command.
        
        Args:
            test_command: Must be 'pytest' or 'python -m pytest'
            target_test: Optional path to specific test file or directory
            timeout_seconds: Subprocess execution timeout
        """
        # Security validation: reject anything that isn't pytest
        cmd_parts = shlex.split(test_command)
        if not cmd_parts:
            cmd_parts = ["pytest"]

        base_bin = Path(cmd_parts[0]).name.lower()
        if "pytest" not in base_bin and "python" not in base_bin:
            return {
                "success": False,
                "error": f"Security Violation: Command '{test_command}' rejected. Only pytest is permitted."
            }

        # Build clean command array
        # Use sys.executable -m pytest to guarantee same virtual environment
        exec_cmd = [sys.executable, "-m", "pytest"]
        
        # Add verbosity or target test
        if target_test:
            exec_cmd.append(target_test)
        elif (self.workspace_dir / "sample_repo" / "tests").exists():
            exec_cmd.append(str(Path("sample_repo/tests")))

        try:
            result = subprocess.run(
                exec_cmd,
                cwd=str(self.workspace_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds
            )

            # Analyze output
            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode

            # Determine pass/fail count heuristics
            passed = "passed" in stdout
            failed = "failed" in stdout or exit_code != 0

            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "summary": "All tests passed" if exit_code == 0 else "Tests failed or errors occurred",
                "command_executed": " ".join(exec_cmd)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "error": f"Test suite timed out after {timeout_seconds} seconds."
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "error": f"Execution error: {str(e)}"
            }
