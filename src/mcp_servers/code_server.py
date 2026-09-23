import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.config import safe_resolve_path, ALLOWED_DIR

class CodeMCPServer:
    """
    Code MCP Server:
    Exposes tools for searching workspace files, reading source code,
    inspecting AST symbols (classes/functions), and applying validated patches.
    """
    def __init__(self, workspace_dir: Path = None):
        self.workspace_dir = (workspace_dir or ALLOWED_DIR).resolve()

    def search_workspace(
        self,
        query: str,
        file_pattern: str = "*",
        max_matches: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search project files for text or regex patterns.
        Ignores virtual environments, .git, and binary files.
        """
        results = []
        pattern = re.compile(query, re.IGNORECASE)
        skip_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", ".idea", ".vscode", "build", "dist"}

        for root, dirs, files in os.walk(self.workspace_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                # Match file extension/pattern
                if file_pattern != "*" and not Path(file).match(file_pattern):
                    continue

                full_path = Path(root) / file
                rel_path = full_path.relative_to(self.workspace_dir)

                # Skip non-text files or files that cannot be read as utf-8
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_idx, line in enumerate(f, start=1):
                            if pattern.search(line):
                                results.append({
                                    "file": str(rel_path).replace("\\", "/"),
                                    "line_number": line_idx,
                                    "content": line.strip()
                                })
                                if len(results) >= max_matches:
                                    return results
                except Exception:
                    continue

        return results

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Safely reads a file within ALLOWED_DIR.
        """
        resolved_path = safe_resolve_path(file_path, self.workspace_dir)
        if not resolved_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }
        if not resolved_path.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}",
                "file_path": file_path
            }

        with open(resolved_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return {
            "success": True,
            "file_path": str(resolved_path.relative_to(self.workspace_dir)).replace("\\", "/"),
            "content": content,
            "total_lines": len(content.splitlines())
        }

    def inspect_symbol(self, symbol_name: str, file_path: str) -> Dict[str, Any]:
        """
        Uses Python's standard `ast` module to inspect classes or functions.
        Extracts start/end lines, arguments, return type annotations, and docstrings.
        """
        resolved_path = safe_resolve_path(file_path, self.workspace_dir)
        if not resolved_path.exists():
            return {"success": False, "error": f"File '{file_path}' does not exist."}

        with open(resolved_path, "r", encoding="utf-8", errors="replace") as f:
            source_code = f.read()

        try:
            tree = ast.parse(source_code, filename=str(resolved_path))
        except SyntaxError as e:
            return {"success": False, "error": f"Syntax error in {file_path}: {e}"}

        source_lines = source_code.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == symbol_name:
                    docstring = ast.get_docstring(node) or "No docstring provided."
                    start_line = node.lineno
                    end_line = getattr(node, "end_lineno", start_line)

                    # Extract the source snippet
                    code_snippet = "\n".join(source_lines[start_line - 1 : end_line])

                    # Signature info
                    args_list = []
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for arg in node.args.args:
                            args_list.append(arg.arg)

                    return {
                        "success": True,
                        "symbol_name": symbol_name,
                        "type": "class" if isinstance(node, ast.ClassDef) else "function",
                        "start_line": start_line,
                        "end_line": end_line,
                        "arguments": args_list,
                        "docstring": docstring,
                        "code": code_snippet
                    }

        return {
            "success": False,
            "error": f"Symbol '{symbol_name}' not found in '{file_path}'."
        }

    def apply_code_patch(self, target_file: str, patch_diff: str) -> Dict[str, Any]:
        """
        Applies a code change safely.
        Supports unified diff format or full content replacement.
        Validates Python syntax before saving to disk.
        """
        resolved_path = safe_resolve_path(target_file, self.workspace_dir)
        if not resolved_path.exists():
            return {"success": False, "error": f"File '{target_file}' does not exist."}

        with open(resolved_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        new_content = None

        # Check if patch_diff is a unified diff
        if patch_diff.startswith("---") or "@@" in patch_diff:
            # Simple unified diff parser
            orig_lines = original_content.splitlines(keepends=True)
            patched_lines = []
            diff_lines = patch_diff.splitlines()
            
            # Simple direct hunk application or replacement
            # For robustness in LLM output, handle both standard unified diff and target replace
            try:
                import difflib
                # Attempt to apply diff line by line or fallback to smart replace
                patched_lines = self._apply_unified_diff(orig_lines, diff_lines)
                new_content = "".join(patched_lines)
            except Exception:
                new_content = None

        if new_content is None:
            # If not unified diff or diff failed to match exactly, check if patch_diff contains replacement text
            # Format: <<<ORIGINAL\n...\n===\n...\n>>> or whole file
            if "<<<ORIGINAL" in patch_diff and "===" in patch_diff:
                match = re.search(r"<<<ORIGINAL\n(.*?)\n===\n(.*?)\n>>>", patch_diff, re.DOTALL)
                if match:
                    orig_target = match.group(1)
                    replacement = match.group(2)
                    new_content = original_content.replace(orig_target, replacement, 1)
            else:
                # Direct new content if supplied
                new_content = patch_diff

        # Validate syntax for Python files
        if resolved_path.suffix == ".py":
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                return {
                    "success": False,
                    "error": f"Patch rejected: Syntax error would be introduced: {e}"
                }

        # Create backup and write changes
        backup_path = resolved_path.with_suffix(resolved_path.suffix + ".bak")
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original_content)

        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {
            "success": True,
            "target_file": str(resolved_path.relative_to(self.workspace_dir)).replace("\\", "/"),
            "backup_file": str(backup_path.name),
            "message": "Patch successfully applied."
        }

    def _apply_unified_diff(self, orig_lines: List[str], diff_lines: List[str]) -> List[str]:
        """Simple line-based diff applicator"""
        result = []
        i = 0
        diff_idx = 0
        while diff_idx < len(diff_lines):
            line = diff_lines[diff_idx]
            diff_idx += 1
            if line.startswith("@@"):
                continue
            elif line.startswith("---") or line.startswith("+++"):
                continue
            elif line.startswith("-"):
                # Skip original line
                i += 1
            elif line.startswith("+"):
                # Add new line
                result.append(line[1:] + "\n")
            elif line.startswith(" "):
                if i < len(orig_lines):
                    result.append(orig_lines[i])
                    i += 1
            else:
                if i < len(orig_lines):
                    result.append(orig_lines[i])
                    i += 1
        while i < len(orig_lines):
            result.append(orig_lines[i])
            i += 1
        return result
