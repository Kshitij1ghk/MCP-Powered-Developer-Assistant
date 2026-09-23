import pytest
from src.agent.orchestrator import AgentOrchestrator
from src.config import ALLOWED_DIR

def test_agent_multi_step_search_inspect():
    orchestrator = AgentOrchestrator(workspace_dir=ALLOWED_DIR)
    response = orchestrator.run("Where is authentication handled?")
    
    assert response is not None
    assert len(response.tool_records) >= 2
    assert response.tool_records[0].tool_name == "search_workspace"
    assert response.tool_records[1].tool_name == "inspect_symbol"
    assert "authenticate_user" in response.final_answer
    assert "auth.py" in response.final_answer

def test_agent_symbol_inspection():
    orchestrator = AgentOrchestrator(workspace_dir=ALLOWED_DIR)
    response = orchestrator.run("Inspect authenticate_user in sample_repo/auth.py")
    
    assert len(response.tool_records) == 1
    assert response.tool_records[0].tool_name == "inspect_symbol"
    assert "Lines:" in response.final_answer
    assert "def authenticate_user" in response.final_answer

def test_agent_read_file():
    orchestrator = AgentOrchestrator(workspace_dir=ALLOWED_DIR)
    response = orchestrator.run("Read sample_repo/auth.py")
    
    assert len(response.tool_records) == 1
    assert response.tool_records[0].tool_name == "read_file"
    assert "authenticate_user" in response.final_answer

def test_agent_github_issue():
    orchestrator = AgentOrchestrator(workspace_dir=ALLOWED_DIR)
    response = orchestrator.run("Check GitHub issue #12")
    
    assert len(response.tool_records) == 1
    assert response.tool_records[0].tool_name == "fetch_issue"
    assert "Issue #12" in response.final_answer
    assert "Authentication token validation" in response.final_answer

def test_agent_patch_approval_granted():
    # Callback always approves (returns True)
    approved_callback = lambda target, diff: True
    orchestrator = AgentOrchestrator(workspace_dir=ALLOWED_DIR, approval_callback=approved_callback)
    
    response = orchestrator.run("Fix this small bug in authentication")
    assert response.requires_approval is True
    assert response.approval_granted is True
    assert "Patch Applied Successfully" in response.final_answer

def test_agent_patch_approval_rejected():
    # Callback always rejects (returns False)
    rejected_callback = lambda target, diff: False
    orchestrator = AgentOrchestrator(workspace_dir=ALLOWED_DIR, approval_callback=rejected_callback)
    
    response = orchestrator.run("Fix this small bug in authentication")
    assert response.requires_approval is True
    assert response.approval_granted is False
    assert "Patch rejected by user" in response.final_answer

def test_agent_run_tests():
    orchestrator = AgentOrchestrator(workspace_dir=ALLOWED_DIR)
    response = orchestrator.run("Run pytest")
    
    assert len(response.tool_records) == 1
    assert response.tool_records[0].tool_name == "run_test_suite"
    assert "Pytest Execution Results" in response.final_answer
