import pytest
from pathlib import Path
from src.mcp_servers.code_server import CodeMCPServer
from src.config import safe_resolve_path, ALLOWED_DIR

@pytest.fixture
def code_server():
    return CodeMCPServer(ALLOWED_DIR)

def test_search_workspace(code_server):
    results = code_server.search_workspace(query="authenticate_user", file_pattern="*.py")
    assert len(results) > 0
    assert any("auth.py" in r["file"] for r in results)
    assert any(r["line_number"] > 0 for r in results)

def test_read_file_safe(code_server):
    res = code_server.read_file("sample_repo/auth.py")
    assert res["success"] is True
    assert "def authenticate_user" in res["content"]
    assert res["total_lines"] > 5

def test_read_file_nonexistent(code_server):
    res = code_server.read_file("sample_repo/nonexistent_file_xyz.py")
    assert res["success"] is False
    assert "File not found" in res["error"]

def test_inspect_symbol_ast(code_server):
    res = code_server.inspect_symbol("authenticate_user", "sample_repo/auth.py")
    assert res["success"] is True
    assert res["type"] == "function"
    assert "username" in res["arguments"]
    assert "token" in res["arguments"]
    assert "Authenticate a user by username" in res["docstring"]
    assert res["start_line"] > 0

def test_inspect_symbol_not_found(code_server):
    res = code_server.inspect_symbol("fake_symbol_123", "sample_repo/auth.py")
    assert res["success"] is False
    assert "not found" in res["error"]

def test_workspace_jail_path_traversal():
    """Verify that path traversal attempts raise PermissionError."""
    with pytest.raises(PermissionError) as exc_info:
        safe_resolve_path("../../etc/passwd", ALLOWED_DIR)
    assert "Security Violation" in str(exc_info.value)

def test_apply_code_patch(code_server, tmp_path):
    # Test patch on a temporary file
    test_file = ALLOWED_DIR / "sample_repo" / "temp_test_patch.py"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("def hello():\n    return 'old'\n")

    try:
        patch = (
            "<<<ORIGINAL\n"
            "    return 'old'\n"
            "===\n"
            "    return 'new'\n"
            ">>>"
        )
        res = code_server.apply_code_patch("sample_repo/temp_test_patch.py", patch)
        assert res["success"] is True
        
        # Verify content was updated
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "return 'new'" in content
    finally:
        # Cleanup temp file and backup
        if test_file.exists():
            test_file.unlink()
        bak = test_file.with_suffix(".py.bak")
        if bak.exists():
            bak.unlink()
