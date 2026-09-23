"""
Sample Core Application
"""
from sample_repo.auth import authenticate_user, get_session_info

def handle_request(username: str, token: str) -> dict:
    """
    Processes incoming developer API request.
    """
    is_authenticated = authenticate_user(username, token)
    if not is_authenticated:
        return {"status": 401, "error": "Unauthorized"}
    
    session = get_session_info(token)
    return {"status": 200, "message": f"Welcome {username}", "session": session}
