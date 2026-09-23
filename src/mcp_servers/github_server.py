import os
import httpx
from typing import Dict, Any, Optional
from src.config import GITHUB_TOKEN

class GitHubMCPServer:
    """
    GitHub MCP Server:
    Exposes tools to fetch issues, read issue discussions/comments,
    and search repository items via the GitHub REST API.
    Includes offline mock fallbacks for resilient demos and tests.
    """
    def __init__(self, token: Optional[str] = None):
        self.token = token or GITHUB_TOKEN
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-Developer-Assistant/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def fetch_issue(self, repo_name: str, issue_id: int) -> Dict[str, Any]:
        """
        Retrieves issue title, body, labels, state, and comments.
        Args:
            repo_name: e.g. "octocat/Hello-World" or "sample/project"
            issue_id: integer issue number
        """
        url = f"https://api.github.com/repos/{repo_name}/issues/{issue_id}"
        
        try:
            with httpx.Client(timeout=10.0, headers=self.headers) as client:
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    
                    # Fetch comments
                    comments = []
                    if data.get("comments", 0) > 0:
                        c_res = client.get(f"{url}/comments")
                        if c_res.status_code == 200:
                            for c in c_res.json():
                                comments.append({
                                    "user": c.get("user", {}).get("login"),
                                    "body": c.get("body")
                                })

                    return {
                        "success": True,
                        "repo": repo_name,
                        "issue_id": issue_id,
                        "title": data.get("title"),
                        "state": data.get("state"),
                        "author": data.get("user", {}).get("login"),
                        "labels": [l.get("name") for l in data.get("labels", [])],
                        "body": data.get("body"),
                        "comments": comments,
                        "source": "live_github_api"
                    }
                elif res.status_code in (401, 403, 404):
                    # Graceful fallback to mock demo data if no token or rate-limited
                    return self._mock_issue(repo_name, issue_id, status_code=res.status_code)
        except Exception:
            # Network offline / timeout fallback
            return self._mock_issue(repo_name, issue_id, status_code="offline")

        return self._mock_issue(repo_name, issue_id)

    def search_repository(self, query: str, repo_name: str = "") -> Dict[str, Any]:
        """
        Searches issues or code within a GitHub repository.
        """
        q = f"{query} repo:{repo_name}" if repo_name else query
        url = f"https://api.github.com/search/issues?q={q}"

        try:
            with httpx.Client(timeout=10.0, headers=self.headers) as client:
                res = client.get(url)
                if res.status_code == 200:
                    items = res.json().get("items", [])
                    return {
                        "success": True,
                        "total_count": len(items),
                        "items": [
                            {
                                "number": item.get("number"),
                                "title": item.get("title"),
                                "state": item.get("state"),
                                "html_url": item.get("html_url")
                            }
                            for item in items[:5]
                        ],
                        "source": "live_github_api"
                    }
        except Exception:
            pass

        # Demo fallback
        return {
            "success": True,
            "total_count": 1,
            "items": [
                {
                    "number": 12,
                    "title": f"Bug: Fix token authentication timeout matching '{query}'",
                    "state": "open",
                    "html_url": f"https://github.com/{repo_name or 'demo/repo'}/issues/12"
                }
            ],
            "source": "mock_demo_store"
        }

    def _mock_issue(self, repo_name: str, issue_id: int, status_code: Any = None) -> Dict[str, Any]:
        """Built-in realistic issue for demos, offline mode, and unit tests."""
        return {
            "success": True,
            "repo": repo_name,
            "issue_id": issue_id,
            "title": f"Issue #{issue_id}: Authentication token validation fails on expired sessions",
            "state": "open",
            "author": "dev-user",
            "labels": ["bug", "security", "backend"],
            "body": (
                "When a user attempts to refresh an expired session token, `authenticate_user()` "
                "throws an unhandled ValueError instead of returning False or renewing the token. "
                "Steps to reproduce: call `authenticate_user(token='expired_123')`."
            ),
            "comments": [
                {
                    "user": "senior-engineer",
                    "body": "Confirmed in staging. We need to catch ValueError and return False."
                }
            ],
            "source": "mock_demo_store",
            "note": f"Served via demo store (Status: {status_code})" if status_code else "Demo mock"
        }
