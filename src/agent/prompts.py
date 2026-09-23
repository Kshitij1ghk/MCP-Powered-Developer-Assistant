"""
System Prompts and Tool Schema Definitions for MCP-Powered Developer Assistant
"""

SYSTEM_PROMPT = """You are an expert AI Developer Assistant powered by Python and the Model Context Protocol (MCP).
Your mission is to help software engineers navigate, inspect, debug, and safely patch their projects.

You have access to several specialized MCP tools:
1. `search_workspace(query, file_pattern, max_matches)`: Search project files for text or regex patterns.
2. `read_file(file_path)`: Safely inspect the full contents of a file within the workspace.
3. `inspect_symbol(symbol_name, file_path)`: Use Python's AST to extract function/class signatures, docstrings, and line ranges.
4. `apply_code_patch(target_file, patch_diff)`: Propose a patch to resolve a bug or implement a feature (Requires user confirmation).
5. `fetch_issue(repo_name, issue_id)`: Retrieve issue details, bug reports, and discussions from GitHub.
6. `search_repository(query, repo_name)`: Search issues or content across a GitHub repository.
7. `run_test_suite(test_command, target_test)`: Run automated pytest verification after making changes.

Rules:
- Always gather context before proposing modifications (search -> inspect -> patch).
- Never modify files blindly without understanding the syntax and existing implementation.
- All code patches must be clean, maintain existing style, and preserve working features.
- Explain your findings and rationale clearly to the developer.
"""

TOOL_DEFINITIONS = [
    {
        "name": "search_workspace",
        "description": "Search project files for text or regex patterns and return matching file paths and line snippets.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search term or regex pattern"},
                "file_pattern": {"type": "string", "description": "Glob pattern (e.g. '*.py'), default is '*'"},
                "max_matches": {"type": "integer", "description": "Max number of matches to return (default 20)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_file",
        "description": "Read the full contents of a file inside the allowed workspace directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Relative path to the file"}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "inspect_symbol",
        "description": "Inspect a Python function or class definition using AST parsing to extract its signature, line range, and docstring.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol_name": {"type": "string", "description": "The function or class name to inspect"},
                "file_path": {"type": "string", "description": "Relative path to the Python file"}
            },
            "required": ["symbol_name", "file_path"]
        }
    },
    {
        "name": "apply_code_patch",
        "description": "Apply a code modification or unified diff to a file in the workspace. Requires human approval before writing to disk.",
        "parameters": {
            "type": "object",
            "properties": {
                "target_file": {"type": "string", "description": "Relative path to the file to modify"},
                "patch_diff": {"type": "string", "description": "The patch diff or replaced content"}
            },
            "required": ["target_file", "patch_diff"]
        }
    },
    {
        "name": "fetch_issue",
        "description": "Fetch a GitHub issue by number, including title, body, labels, state, and comments.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_name": {"type": "string", "description": "Repository in 'owner/repo' format"},
                "issue_id": {"type": "integer", "description": "The issue number"}
            },
            "required": ["repo_name", "issue_id"]
        }
    },
    {
        "name": "search_repository",
        "description": "Search issues or code in a GitHub repository.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term"},
                "repo_name": {"type": "string", "description": "Optional repository name"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "run_test_suite",
        "description": "Run pytest tests in a sandboxed environment and capture stdout, stderr, and test exit codes.",
        "parameters": {
            "type": "object",
            "properties": {
                "test_command": {"type": "string", "description": "Command, default 'pytest'"},
                "target_test": {"type": "string", "description": "Optional test file or target path"}
            }
        }
    }
]
