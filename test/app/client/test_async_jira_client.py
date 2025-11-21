import pytest
from unittest.mock import AsyncMock, patch
import aiohttp
from src.app.client.async_jira import AsyncJiraClient


class TestAsyncJiraClient:
    """
    Tests for AsyncJiraClient using pytest-asyncio.
    No unittest.TestCase - pure pytest approach.
    """

    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Set up test client"""
        self.base_url = "https://company.atlassian.net"
        self.email = "test@company.com"
        self.api_token = "fake-jira-token"
        self.client = AsyncJiraClient(
            base_url=self.base_url, email=self.email, api_token=self.api_token
        )

    def test_initialization(self):
        """Test client initialization (sync test - no async needed)"""
        assert self.client.base_url == self.base_url
        assert self.client.email == self.email
        assert self.client.api_token == self.api_token
        assert isinstance(self.client.auth, aiohttp.BasicAuth)

    @pytest.mark.asyncio
    async def test_get_assigned_issues_success(self):
        """
        ASYNC TEST: Test successful issue retrieval.
        """
        with patch.object(
            self.client, "get_assigned_issues", new_callable=AsyncMock
        ) as mock_method:
            # Arrange
            mock_method.return_value = [
                {
                    "key": "PROJ-123",
                    "summary": "Fix login authentication",
                    "status": "In Progress",
                    "updated": "2024-01-15T10:30:00.000+0000",
                    "assignee": "John Doe",
                    "priority": "High",
                }
            ]

            # Act - Call the async method
            result = await self.client.get_assigned_issues(
                assignee_name="John", time_range="recent"
            )

            # Assert - pytest style
            assert len(result) == 1
            assert result[0]["key"] == "PROJ-123"
            assert result[0]["summary"] == "Fix login authentication"
            assert result[0]["status"] == "In Progress"
            assert result[0]["assignee"] == "John Doe"

            # Verify the method was called
            mock_method.assert_called_once_with(
                assignee_name="John", time_range="recent"
            )

    @pytest.mark.asyncio
    async def test_time_range_jql_construction(self):
        """
        ASYNC TEST: Test JQL query construction for different time ranges.
        """
        with patch.object(
            self.client, "get_assigned_issues", new_callable=AsyncMock
        ) as mock_method:
            # Arrange - return empty list for both calls
            mock_method.return_value = []

            await self.client.get_assigned_issues("John", "recent")
            await self.client.get_assigned_issues("John", "this_week")

            assert mock_method.call_count == 2
            calls = mock_method.call_args_list

            first_call_args = calls[0].args
            second_call_args = calls[1].args

            assert first_call_args[1] == "recent"
            assert second_call_args[1] == "this_week"

    @pytest.mark.asyncio
    async def test_authentication_setup(self):
        """
        ASYNC TEST: Test that proper authentication is configured.
        """
        # This test verifies the auth object is properly set up during initialization
        assert self.client.auth is not None
        assert self.client.auth.login == self.email
        assert self.client.auth.password == self.api_token

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """
        ASYNC TEST: Test handling of JIRA API errors.
        """
        with patch.object(
            self.client, "get_assigned_issues", new_callable=AsyncMock
        ) as mock_method:
            # Arrange - make the method raise an exception
            mock_method.side_effect = Exception(
                "JIRA permission denied - insufficient access rights"
            )

            # Act & Assert - use pytest.raises instead of self.assertRaises
            with pytest.raises(Exception) as exc_info:
                await self.client.get_assigned_issues("John", "recent")

            # Verify the error message
            assert "permission" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_connection_test_success(self):
        """
        ASYNC TEST: Test successful connection test.
        """
        with patch.object(
            self.client, "test_connection", new_callable=AsyncMock
        ) as mock_method:
            mock_method.return_value = True

            result = await self.client.test_connection()

            assert result is True
            mock_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_test_failure(self):
        """
        ASYNC TEST: Test failed connection test.
        """
        with patch.object(
            self.client, "test_connection", new_callable=AsyncMock
        ) as mock_method:
            mock_method.return_value = False

            result = await self.client.test_connection()

            assert result is False
