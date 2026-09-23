import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Base project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Allowed workspace directory for path sandboxing (defaults to PROJECT_ROOT / sample_repo or PROJECT_ROOT)
# Can be overridden by WORKSPACE_DIR environment variable
ALLOWED_DIR = Path(os.getenv("WORKSPACE_DIR", str(PROJECT_ROOT))).resolve()

# GitHub and LLM API Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").strip().lower()

def safe_resolve_path(target_path: str, base_dir: Path = None) -> Path:
    """
    Workspace Jail Security Function:
    Resolves relative and absolute file paths against ALLOWED_DIR.
    Prevents path traversal attacks (e.g., '../../etc/passwd' or system file access).
    
    Raises:
        PermissionError: If target path escapes ALLOWED_DIR.
        FileNotFoundError: If path resolution fails unexpectedly.
    """
    root = (base_dir or ALLOWED_DIR).resolve()
    
    candidate = Path(target_path)
    if not candidate.is_absolute():
        resolved = (root / candidate).resolve()
    else:
        resolved = candidate.resolve()
        
    # Verify that the resolved path is within root
    try:
        resolved.relative_to(root)
    except ValueError:
        raise PermissionError(
            f"Security Violation: Path '{target_path}' resolves to '{resolved}', "
            f"which is outside the permitted workspace jail '{root}'."
        )
        
    return resolved
