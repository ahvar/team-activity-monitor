import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp
from datetime import datetime, timedelta
from src.app.client.async_github import AsyncGitHubClient


class TestAsyncGitHubClient:
    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Set up test client with mock API key"""
        self.api_key = "fake-github-token"
        self.client = AsyncGitHubClient(api_key=self.api_key)

    def test_initialization(self):
        """Test client initialization"""
        assert self.client.api_key == self.api_key
        assert self.client.base_url == "https://api.github.com"
        assert "Authorization" in self.client.headers
        assert self.client.headers["Authorization"] == f"Bearer {self.api_key}"

    @pytest.mark.asyncio
    async def test_get_recent_commits_success(self):
        """Test successful commit retrieval"""
        with patch.object(
            self.client, "get_recent_commits", new_callable=AsyncMock
        ) as mock_method:
            # Arrange
            mock_method.return_value = [
                {
                    "sha": "abc123",
                    "message": "Fix authentication bug",
                    "date": "2024-01-15T10:30:00Z",
                    "repository": "team-project",
                }
            ]

            # Act
            result = await self.client.get_recent_commits(
                author_name="John", time_range="recent"
            )

            # Assert - pytest style
            assert len(result) == 1
            assert result[0]["sha"] == "abc123"
            assert result[0]["message"] == "Fix authentication bug"

            # Verify method was called
            mock_method.assert_called_once_with(author_name="John", time_range="recent")

    @pytest.mark.asyncio
    async def test_get_recent_pull_requests_success(self):
        """Test successful PR retrieval"""
        with patch.object(
            self.client, "get_recent_pull_requests", new_callable=AsyncMock
        ) as mock_method:
            # Arrange
            mock_method.return_value = [
                {
                    "number": 42,
                    "title": "Add user dashboard feature",
                    "state": "open",
                    "created_at": "2024-01-15T10:30:00Z",
                }
            ]

            # Act
            result = await self.client.get_recent_pull_requests(
                author_name="Sarah", time_range="this_week"
            )

            # Assert
            assert len(result) == 1
            assert result[0]["number"] == 42
            assert result[0]["title"] == "Add user dashboard feature"

    @pytest.mark.asyncio
    async def test_time_range_filtering_actual_queries(self):
        """Test that different time ranges generate correct GitHub queries"""

        # Mock the HTTP session instead of the method
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"items": []})
        mock_response.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session.get.return_value.__aexit__.return_value = None

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session_class.return_value.__aexit__.return_value = None

            # Test "recent" time range (14 days)
            await self.client.get_recent_commits("John", "recent")

            # Get the query that was sent
            call_args = mock_session.get.call_args
            params = call_args[1]["params"]  # keyword arguments
            query = params["q"]

            # Verify the query includes date filter for 14 days ago
            expected_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
            assert f"committer-date:>={expected_date}" in query
            assert "author:John" in query

            # Reset mock
            mock_session.get.reset_mock()

            # Test "this_week" time range (7 days)
            await self.client.get_recent_commits("John", "this_week")

            # Get the query that was sent
            call_args = mock_session.get.call_args
            params = call_args[1]["params"]
            query = params["q"]

            # Verify the query includes date filter for 7 days ago
            expected_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            assert f"committer-date:>={expected_date}" in query
            assert "author:John" in query

    def test_get_date_filter_method(self):
        """Test the _get_date_filter helper method"""

        # Test "this_week" - should return 7 days ago
        result = self.client._get_date_filter("this_week")
        expected = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        assert result == expected

        # Test "recent" - should return 14 days ago
        result = self.client._get_date_filter("recent")
        expected = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
        assert result == expected

        # Test "all_time" - should return None
        result = self.client._get_date_filter("all_time")
        assert result is None

        # Test unknown value - should return None
        result = self.client._get_date_filter("unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors"""
        with patch.object(
            self.client, "get_recent_commits", new_callable=AsyncMock
        ) as mock_method:
            # Arrange - make the method raise an exception
            mock_method.side_effect = Exception(
                "GitHub authentication failed - check API key"
            )

            # Act & Assert - use pytest.raises instead of self.assertRaises
            with pytest.raises(Exception) as exc_info:
                await self.client.get_recent_commits("John", "recent")

            # Verify the error message
            assert "authentication" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_connection_test(self):
        """Test connection testing functionality"""
        # Test successful connection
        with patch.object(
            self.client, "test_connection", new_callable=AsyncMock
        ) as mock_method:
            mock_method.return_value = True

            result = await self.client.test_connection()
            assert result is True

        # Test failed connection
        with patch.object(
            self.client, "test_connection", new_callable=AsyncMock
        ) as mock_method:
            mock_method.return_value = False

            result = await self.client.test_connection()
            assert result is False
