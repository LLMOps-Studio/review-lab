from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from review_lab.api import app

# Initialize FastAPI Test Client
client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "review-lab"}


def test_review_missing_code_snippet_returns_422():
    """The request body requires code_snippet; omitting it should fail validation, not 500."""
    response = client.post("/review", json={})
    assert response.status_code == 422


@patch("review_lab.api.review_graph.invoke")
def test_review_pipeline_failure_returns_500(mock_invoke):
    """If the LangGraph pipeline raises, the API should surface a 500 with the error detail, not crash."""
    mock_invoke.side_effect = RuntimeError("agent routing exploded")

    response = client.post("/review", json={"code_snippet": "print(1)"})

    assert response.status_code == 500
    assert "agent routing exploded" in response.json()["detail"]


def test_webhook_ignores_non_opened_events():
    """Only newly-opened PRs should trigger a review; other actions must be a no-op, not an error."""
    payload = {"action": "closed", "pull_request": {}}

    response = client.post("/webhook/github", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ignored",
        "message": "Not an opened PR event.",
    }


def test_webhook_missing_pull_request_is_ignored():
    """A payload with no pull_request key (e.g. a non-PR webhook event) must also be a no-op."""
    response = client.post("/webhook/github", json={"action": "opened"})

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


@patch("review_lab.api.post_github_comment")
@patch("review_lab.api.review_graph.invoke")
@patch("review_lab.api.requests.get")
def test_webhook_opened_pr_queues_review(mock_get, mock_invoke, mock_post_comment):
    """An opened-PR webhook should fetch the diff, queue the review, and respond immediately (202-style accept)."""
    mock_diff_response = MagicMock()
    mock_diff_response.text = "diff --git a/foo.py b/foo.py"
    mock_get.return_value = mock_diff_response
    mock_invoke.return_value = {"final_review": "Looks fine."}

    payload = {
        "action": "opened",
        "pull_request": {
            "diff_url": "https://api.github.com/repos/x/y/pulls/1.diff",
            "comments_url": "https://api.github.com/repos/x/y/issues/1/comments",
        },
    }

    response = client.post("/webhook/github", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted",
        "message": "PR review task queued.",
    }
    # The background task runs synchronously under TestClient, so by the
    # time the request returns, the diff was fetched and the pipeline ran.
    mock_get.assert_called_once_with("https://api.github.com/repos/x/y/pulls/1.diff")
    mock_invoke.assert_called_once()
    mock_post_comment.assert_called_once()
