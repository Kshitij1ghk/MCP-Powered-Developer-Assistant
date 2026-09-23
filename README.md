# MCP-Powered Developer Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Protocol MCP](https://img.shields.io/badge/protocol-MCP%201.0-teal.svg)](https://modelcontextprotocol.io/)
[![VCS Integration](https://img.shields.io/badge/integration-GitHub%20API-orange.svg)](https://docs.github.com/en/rest)
[![Tests Passing](https://img.shields.io/badge/tests-16%20passed-green.svg)](tests/)

An AI-powered command-line developer assistant built with Python and Anthropic's **Model Context Protocol (MCP)**. The assistant inspects codebases, parses AST symbols, triages GitHub issues, proposes validated patches with interactive human approval gates, and executes regression test suites inside secure sandboxes.

---

## Architecture Topology

```
+-------------------------------------------------------------+
|                     USER DEVELOPER CLI                      |
|                   (Rich Terminal Interface)                 |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|              AI AGENT ORCHESTRATOR (MCP Client)             |
|  - Dynamic Tool Discovery                                   |
|  - Multi-Step Reasoning Loop                                |
|  - Human-in-the-Loop Confirmation Gate                      |
+------------------------------+------------------------------+
                               |
                               | JSON-RPC 2.0 / MCP Protocol
            +------------------+------------------+
            |                                     |
            v                                     v
+---------------------------+       +---------------------------+
|      CODE MCP SERVER      |       |     GITHUB MCP SERVER     |
| - search_workspace        |       | - fetch_issue             |
| - read_file (safe jail)   |       | - search_repository       |
| - inspect_symbol (AST)    |       |                           |
| - apply_code_patch (diff) |       |                           |
+---------------------------+       +---------------------------+
            |                                     |
            v                                     v
+---------------------------+       +---------------------------+
|     TEST MCP SERVER       |       |       REMOTE CLOUD        |
| - run_test_suite (pytest) |       |     GitHub REST / GraphQL |
| - Subprocess & Timeout    |       +---------------------------+
+---------------------------+
```

---

## Core MVP Features

| Feature | MCP Tool | Description |
| :--- | :--- | :--- |
| **Code Search** | `search_workspace` | Scans project files by text or regex, returning file paths and matching lines. |
| **Safe File Reading** | `read_file` | Reads source files strictly confined inside the `ALLOWED_DIR` workspace jail. |
| **AST Symbol Inspection** | `inspect_symbol` | Parses Python code with Python's standard `ast` module to extract classes, functions, arguments, docstrings, and line ranges. |
| **GitHub Issue Lookup** | `fetch_issue` | Fetches issue title, body, labels, state, and thread comments with offline demo fallback. |
| **Human Approval Patching**| `apply_code_patch` | Shows syntax-highlighted diffs and halts for explicit `[Y/N]` developer confirmation before applying disk changes. |
| **Automated Testing** | `run_test_suite` | Executes sandboxed `pytest` commands with timeouts to verify patches. |

---

## Getting Started

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/mcp-developer-assistant.git
cd mcp-developer-assistant

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup (Optional)

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Configure your keys if connecting to live cloud APIs:
- `GITHUB_TOKEN`: GitHub Personal Access Token for live repository lookups.
- `OPENAI_API_KEY`: API key for GPT-4o function calling (If omitted, the assistant seamlessly runs in zero-cost offline heuristic mode).

---

## Usage

### Interactive Developer REPL
Launch the assistant in interactive mode:
```bash
python -m src.cli
```

### One-Off Command Queries
You can also ask direct developer questions:

```bash
# Locate code
python -m src.cli "Where is authentication handled?"

# Inspect an AST function
python -m src.cli "Inspect authenticate_user in sample_repo/auth.py"

# Triage a GitHub issue
python -m src.cli "Check GitHub issue #12"

# Safe bug fixing workflow
python -m src.cli "Fix this small bug in authentication"

# Run tests
python -m src.cli "Run pytest"
```

---

## Security Guardrails & Safety Model

1. **Workspace Path Jailing (`safe_resolve_path`):** All file operations normalize paths with `pathlib.Path.resolve()`. Any path escaping `ALLOWED_DIR` (e.g. `../../etc/passwd`) immediately raises a `PermissionError`.
2. **Human-in-the-Loop Confirmation:** Destructive file modifications (`apply_code_patch`) cannot execute silently. The CLI halts, renders a colorized diff preview, and requires `y/N` input.
3. **Execution Containment:** The test server strictly restricts execution to `pytest` under a timeout window, rejecting arbitrary shell injections.
4. **Zero Secret Leakage:** Tokens and API credentials are kept exclusively inside `.env` and are never injected into LLM prompt histories.

---

## Automated Test Suite

Run the full pytest suite:
```bash
python -m pytest tests -v
```

All 16 unit and integration tests verify:
- Code search, file reading, and AST symbol extraction.
- Workspace jail defense against path traversal.
- Patch generation, syntax parsing, and backup creation.
- GitHub issue fetching and repository search.
- Multi-step agent flows and human approval/rejection branches.

---

## Repository Structure

```
mcp-developer-assistant/
|-- src/
|   |-- config.py                    # Environment settings & workspace jail
|   |-- cli.py                       # Rich terminal interface
|   |-- agent/
|   |   |-- orchestrator.py          # Cognitive ReAct loop & MCP client
|   |   +-- prompts.py               # System prompts & tool definitions
|   +-- mcp_servers/
|       |-- code_server.py           # Filesystem, AST symbols, patch engine
|       |-- github_server.py         # GitHub API client (issues, search)
|       +-- test_server.py           # Sandboxed pytest execution
|-- sample_repo/                     # Demo playground project
|   |-- app.py
|   |-- auth.py
|   +-- tests/test_app.py
|-- tests/
|   |-- test_agent.py
|   |-- test_code_server.py
|   +-- test_github_server.py
|-- .env.example
|-- requirements.txt
+-- README.md
```
