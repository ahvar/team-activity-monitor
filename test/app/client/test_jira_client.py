import unittest
import pytest
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from src.app.client.async_jira import AsyncJiraClient  # Fixed import path


class TestAsyncJiraClient(unittest.TestCase):
    """
    Tests for AsyncJiraClient
    """

    def setUp(self):
        """Set up test client"""
        self.base_url = "https://company.atlassian.net"
        self.email = "test@company.com"
        self.api_token = "fake-jira-token"
        self.client = AsyncJiraClient(
            base_url=self.base_url, email=self.email, api_token=self.api_token
        )

    def test_initialization(self):
        """Test client initialization (sync test - no async needed)"""
        self.assertEqual(self.client.base_url, self.base_url)
        self.assertEqual(self.client.email, self.email)
        self.assertEqual(self.client.api_token, self.api_token)
        # Test that auth object is created
        self.assertIsInstance(self.client.auth, aiohttp.BasicAuth)

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_get_assigned_issues_success(self, mock_get):
        """
        ASYNC TEST: Test successful issue retrieval.

        This patches aiohttp instead of requests since we're using async HTTP.
        """
        # Arrange - Mock the aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "key": "PROJ-123",
                    "fields": {
                        "summary": "Fix login authentication",
                        "status": {"name": "In Progress"},
                        "updated": "2024-01-15T10:30:00.000+0000",
                        "assignee": {"displayName": "John Doe"},
                        "priority": {"name": "High"},
                    },
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        # Mock the context manager (__aenter__ and __aexit__)
        mock_get.return_value.__aenter__.return_value = mock_response
        mock_get.return_value.__aexit__.return_value = None

        # Act - Call the async method
        result = await self.client.get_assigned_issues(
            assignee_name="John", time_range="recent"
        )

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["key"], "PROJ-123")
        self.assertEqual(result[0]["summary"], "Fix login authentication")
        self.assertEqual(result[0]["status"], "In Progress")
        self.assertEqual(result[0]["assignee"], "John Doe")

        # Verify the HTTP call was made
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_time_range_jql_construction(self, mock_session):
        """
        ASYNC TEST: Test JQL query construction for different time ranges.
        """
        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"issues": []}
        mock_response.raise_for_status.return_value = None

        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_session_instance.get.return_value.__aexit__.return_value = None
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.__aexit__.return_value = None

        # Test recent time range
        await self.client.get_assigned_issues("John", "recent")
        recent_call_args = mock_session_instance.get.call_args
        recent_params = recent_call_args[1]["params"]

        # Reset mock for second call
        mock_session_instance.reset_mock()

        # Test this_week time range
        await self.client.get_assigned_issues("John", "this_week")
        week_call_args = mock_session_instance.get.call_args
        week_params = week_call_args[1]["params"]

        # Verify different JQL queries were constructed
        self.assertIn("updated >= -14d", recent_params["jql"])  # Recent = 14 days
        self.assertIn("updated >= -7d", week_params["jql"])  # This week = 7 days
        self.assertNotEqual(recent_params["jql"], week_params["jql"])

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_authentication_setup(self, mock_session):
        """
        ASYNC TEST: Test that proper authentication is configured.
        """
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"issues": []}
        mock_response.raise_for_status.return_value = None

        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_session_instance.get.return_value.__aexit__.return_value = None
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.__aexit__.return_value = None

        await self.client.get_assigned_issues("John", "recent")

        # Verify that ClientSession was created with authentication
        mock_session.assert_called()
        session_call_args = mock_session.call_args
        self.assertIn("auth", session_call_args[1])
        self.assertEqual(session_call_args[1]["auth"], self.client.auth)

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_api_error_handling(self, mock_get):
        """
        ASYNC TEST: Test handling of JIRA API errors.
        """
        # Test 403 Forbidden response
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=None, history=None, status=403, message="Forbidden"
        )

        mock_get.return_value.__aenter__.return_value = mock_response
        mock_get.return_value.__aexit__.return_value = None

        # Should raise an exception with permission message
        with self.assertRaises(Exception) as cm:
            await self.client.get_assigned_issues("John", "recent")

        self.assertIn("permission", str(cm.exception).lower())

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_connection_test_success(self, mock_get):
        """
        ASYNC TEST: Test successful connection test.
        """
        mock_response = AsyncMock()
        mock_response.status = 200

        mock_get.return_value.__aenter__.return_value = mock_response
        mock_get.return_value.__aexit__.return_value = None

        result = await self.client.test_connection()

        self.assertTrue(result)
        # Verify it called the /myself endpoint
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0][0]
        self.assertIn("/rest/api/3/myself", call_args)

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_connection_test_failure(self, mock_get):
        """
        ASYNC TEST: Test failed connection test.
        """
        # Mock connection failure
        mock_get.side_effect = aiohttp.ClientConnectorError(
            connection_key=None, os_error=OSError("Connection refused")
        )

        result = await self.client.test_connection()

        self.assertFalse(result)


"""
# Run async tests with pytest
if __name__ == "__main__":
    # For running individual async tests during development
    import asyncio

    async def run_single_test():
        test_instance = TestAsyncJiraClient()
        test_instance.setUp()

        # Example: run a single async test
        await test_instance.test_get_assigned_issues_success()
        print("Test passed!")

    # Use asyncio.run() to execute async test
    # asyncio.run(run_single_test())

    # For running all tests, use: python -m pytest test/app/client/test_jira_client.py -v
    unittest.main()

"""
