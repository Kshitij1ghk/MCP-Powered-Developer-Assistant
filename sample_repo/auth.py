"""
Authentication Module for Demo Application
Handles user credential verification and session token checks.
"""

def authenticate_user(username: str, token: str) -> bool:
    """
    Authenticate a user by username and session token.
    Returns True if authentication succeeds, False otherwise.
    
    Known Bug (Issue #12):
    Throws an unhandled ValueError when receiving an expired token.
    """
    if not username or not token:
        return False

    # Simulate token expiration check
    if token == "expired_123":
        raise ValueError("Token expired")

    # Valid session
    if token.startswith("valid_"):
        return True

    return False

def get_session_info(token: str) -> dict:
    """
    Retrieve user session metadata.
    """
    return {
        "token": token,
        "is_active": token.startswith("valid_"),
        "role": "developer"
    }
