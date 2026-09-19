"""
Smoke tests for the /posts resource on JSONPlaceholder.

These are the critical-path tests that verify the API is healthy.
They run fast (< 30 seconds) and cover the most common user journeys.
If any of these fail, the API is considered DOWN.

Run by file:     uv run pytest tests/test_posts_smoke.py -v
Run by marker:   uv run pytest -m smoke -v
"""

import allure
import pytest
from requests import Session


@allure.feature("Posts")
@allure.story("Smoke")
@pytest.mark.smoke
class TestPostsSmoke:
    """Critical-path smoke tests for the /posts resource."""

    def test_list_posts(self, api_session: Session, validate_schema: callable) -> None:
        """GET /posts returns a list of posts (critical read path)."""
        response = api_session.get("/posts")

        assert response.status_code == 200
        posts = response.json()
        validate_schema(posts, "posts_list_schema.json")
        assert len(posts) == 100

    def test_get_single_post(self, api_session: Session, validate_schema: callable) -> None:
        """GET /posts/1 returns a valid post (critical read-by-id path)."""
        response = api_session.get("/posts/1")

        assert response.status_code == 200
        post = response.json()
        validate_schema(post, "post_schema.json")
        assert post["id"] == 1

    def test_create_post(self, api_session: Session, validate_schema: callable) -> None:
        """POST /posts creates a resource (critical write path)."""
        payload = {
            "title": "Smoke Test Post",
            "body": "Created by smoke test",
            "userId": 1,
        }

        response = api_session.post("/posts", json=payload)

        assert response.status_code == 201
        created = response.json()
        validate_schema(created, "post_schema.json")
        assert created["title"] == payload["title"]

    def test_update_post(self, api_session: Session, validate_schema: callable) -> None:
        """PUT /posts/1 replaces the resource (critical update path)."""
        payload = {
            "id": 1,
            "title": "Smoke Updated",
            "body": "Smoke updated body",
            "userId": 1,
        }

        response = api_session.put("/posts/1", json=payload)

        assert response.status_code == 200
        updated = response.json()
        validate_schema(updated, "post_schema.json")
        assert updated["title"] == "Smoke Updated"

    def test_delete_post(self, api_session: Session) -> None:
        """DELETE /posts/1 returns 200 (critical delete path)."""
        response = api_session.delete("/posts/1")

        assert response.status_code == 200
        assert response.json() == {}
