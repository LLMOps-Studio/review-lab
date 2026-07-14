import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from review_lab.api import app

# Initialize FastAPI Test Client
client = TestClient(app)

@pytest.fixture
def mock_graph_result():
    """Provides a fake successful review from the multi-agent system."""
    return {
        "final_review": "### Security\nNo issues.\n### Style\nFix indentation.\n### Performance\nOptimize loop."
    }

# FIX: Removed '.src' from the patch path. The module is strictly 'review_lab.api'.
@patch("review_lab.api.review_graph.invoke")
def test_direct_review_endpoint(mock_invoke, mock_graph_result):
    """
    Tests the /review endpoint with mocked LangGraph execution.
    Ensures CI/CD environments do not require a GPU or Ollama instance.
    """
    # 1. Setup the mock to return the predefined agent review
    mock_invoke.return_value = mock_graph_result
    
    # 2. Execute the request against the FastAPI endpoint
    payload = {
        "code_snippet": "def bad_func():\n  pass"
    }
    response = client.post("/review", json=payload)
    
    # 3. Validate the response (Smoke Tests)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    
    data = response.json()
    assert data.get("status") == "success", "Expected status to be 'success'"
    assert "Fix indentation" in data.get("review", ""), "Expected specific review content is missing"
    
    # 4. Verify the underlying graph was called exactly once
    mock_invoke.assert_called_once()