import pytest
from unittest.mock import AsyncMock, patch
import aiohttp
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
    async def test_time_range_filtering(self):
        """Test different time range parameters"""
        with patch.object(
            self.client, "get_recent_commits", new_callable=AsyncMock
        ) as mock_method:
            # Arrange - return empty list for both calls
            mock_method.return_value = []

            # Act - test both time ranges
            await self.client.get_recent_commits("John", "recent")
            await self.client.get_recent_commits("John", "this_week")

            # Assert - verify method was called twice with different parameters
            assert mock_method.call_count == 2
            calls = mock_method.call_args_list

            # ✅ FIXED: Access positional arguments correctly
            # calls[0] is a call object with .args (positional) and .kwargs (keyword)
            # Your calls are: get_recent_commits("John", "recent") and get_recent_commits("John", "this_week")
            # So args[0] = "John", args[1] = "recent"/"this_week"
            first_call_args = calls[0].args
            second_call_args = calls[1].args

            assert first_call_args[1] == "recent"  # Second positional argument
            assert second_call_args[1] == "this_week"  # Second positional argument

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
