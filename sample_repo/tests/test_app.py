import pytest
from sample_repo.auth import authenticate_user, get_session_info
from sample_repo.app import handle_request

def test_valid_authentication():
    assert authenticate_user("alice", "valid_token_abc") is True

def test_empty_credentials():
    assert authenticate_user("", "") is False

def test_get_session_info():
    info = get_session_info("valid_123")
    assert info["is_active"] is True
    assert info["role"] == "developer"

def test_handle_request_success():
    res = handle_request("bob", "valid_token_xyz")
    assert res["status"] == 200
    assert "Welcome bob" in res["message"]
