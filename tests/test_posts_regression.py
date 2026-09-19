"""
Regression tests for the /posts resource on JSONPlaceholder.

These tests cover edge cases, negative scenarios, boundary values, and
mock-API quirks. They should run nightly or before releases — not on
every commit — because they are more exhaustive and slower.

Run by file:     uv run pytest tests/test_posts_regression.py -v
Run by marker:   uv run pytest -m regression -v
"""

import allure
import pytest
from requests import Session


@allure.feature("Posts")
@allure.story("Read - Regression")
@pytest.mark.regression
class TestReadPostsRegression:
    """Exhaustive read coverage for /posts."""

    @pytest.mark.parametrize("post_id", [1, 50, 100])
    def test_get_valid_post_by_id(
        self, api_session: Session, validate_schema: callable, post_id: int
    ) -> None:
        """GET /posts/{id} returns a post matching the schema."""
        response = api_session.get(f"/posts/{post_id}")

        assert response.status_code == 200
        post = response.json()
        validate_schema(post, "post_schema.json")
        assert post["id"] == post_id

    @pytest.mark.parametrize("post_id", [9999, 0, -1])
    def test_get_invalid_post_returns_404(self, api_session: Session, post_id: int) -> None:
        """GET /posts/{id} with invalid IDs returns 404 with empty body."""
        response = api_session.get(f"/posts/{post_id}")

        assert response.status_code == 404
        assert response.json() == {}

    @pytest.mark.parametrize(
        "query_filter",
        [
            {"userId": 1},
            {"userId": 5},
        ],
    )
    def test_get_posts_filtered_by_user(
        self,
        api_session: Session,
        validate_schema: callable,
        query_filter: dict,
    ) -> None:
        """GET /posts?userId={id} returns only that user's posts."""
        response = api_session.get("/posts", params=query_filter)

        assert response.status_code == 200
        posts = response.json()
        validate_schema(posts, "posts_list_schema.json")
        assert len(posts) > 0
        assert all(p["userId"] == query_filter["userId"] for p in posts)


@allure.feature("Posts")
@allure.story("Create - Regression")
@pytest.mark.regression
class TestCreatePostRegression:
    """Edge-case create coverage for /posts."""

    def test_create_post_with_empty_body(self, api_session: Session) -> None:
        """POST /posts with empty body returns 201 (documented mock behavior)."""
        response = api_session.post("/posts", json={})

        assert response.status_code == 201
        # Document mock behavior: server does not validate input
        assert "id" in response.json()


@allure.feature("Posts")
@allure.story("Update - Regression")
@pytest.mark.regression
class TestUpdatePostRegression:
    """Edge-case update coverage for /posts."""

    def test_patch_partially_updates_post(self, api_session: Session) -> None:
        """PATCH /posts/1 updates only the provided fields."""
        response = api_session.patch("/posts/1", json={"title": "Patched"})

        assert response.status_code == 200
        patched = response.json()
        assert patched["title"] == "Patched"
        assert "id" in patched

    @pytest.mark.parametrize("bad_id", [9999, 0])
    def test_put_nonexistent_post_returns_500(self, api_session: Session, bad_id: int) -> None:
        """
        PUT /posts/{id} on a nonexistent resource returns 500.

        Known JSONPlaceholder behavior — NOT REST-compliant (should be 404),
        but it's the actual behavior of the mock API. Documented here to
        prevent false failures in CI.
        """
        response = api_session.put(
            f"/posts/{bad_id}",
            json={"title": "X", "body": "Y", "userId": 1},
        )

        assert response.status_code == 500


@allure.feature("Posts")
@allure.story("Delete - Regression")
@pytest.mark.regression
class TestDeletePostRegression:
    """Edge-case delete coverage for /posts."""

    @pytest.mark.parametrize("post_id", [9999, 0])
    def test_delete_nonexistent_post(self, api_session: Session, post_id: int) -> None:
        """DELETE /posts/{id} on nonexistent resources returns 200 (mock)."""
        response = api_session.delete(f"/posts/{post_id}")

        assert response.status_code == 200
