import pytest
from src.mcp_servers.github_server import GitHubMCPServer

@pytest.fixture
def github_server():
    return GitHubMCPServer()

def test_fetch_issue(github_server):
    res = github_server.fetch_issue("acme/demo-project", 12)
    assert res["success"] is True
    assert res["issue_id"] == 12
    assert "Authentication token validation" in res["title"]
    assert res["state"] == "open"
    assert "bug" in res["labels"]
    assert len(res["comments"]) > 0

def test_search_repository(github_server):
    res = github_server.search_repository("authentication", "acme/demo-project")
    assert res["success"] is True
    assert res["total_count"] >= 1
    assert any("Fix token" in item["title"] for item in res["items"])
