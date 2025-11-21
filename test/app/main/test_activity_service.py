import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from src.app.main.async_activity_service import AsyncActivityService
from src.app.main.query_parser import ParsedQuery, Intent


class TestAsyncActivityService:
    """
    Async test class using pytest-asyncio.

    Key differences from sync tests:
    1. Use @pytest.mark.asyncio decorator for async test methods
    2. Use AsyncMock instead of Mock for async methods
    3. Use 'await' when calling async methods
    """

    @pytest.fixture
    def mock_clients(self):
        """
        Fixture that creates AsyncMock objects for testing.

        AsyncMock is like Mock but for async functions - it can be awaited.
        """
        jira_client = AsyncMock()
        github_client = AsyncMock()
        return jira_client, github_client

    @pytest.mark.asyncio  # This decorator tells pytest this test is async
    async def test_concurrent_api_calls(self, mock_clients):
        """
        ASYNC TEST: Test that API calls happen concurrently.

        This test method is a coroutine (async def) because it needs to
        await the async service methods.
        """
        jira_client, github_client = mock_clients

        # Configure mock return values for async methods
        jira_client.get_assigned_issues.return_value = [{"key": "PROJ-123"}]
        github_client.get_recent_commits.return_value = [{"sha": "abc123"}]
        github_client.get_recent_pull_requests.return_value = [{"number": 42}]

        service = AsyncActivityService(jira_client, github_client)
        parsed_query = ParsedQuery(
            member_name="John",
            intent=Intent.MEMBER_ACTIVITY_SUMMARY,
            time_range="recent",
        )

        # Measure execution time to verify concurrency
        import time

        start_time = time.time()

        # AWAIT the async method - this pauses until the coroutine completes
        result = await service.handle_intent(parsed_query)

        execution_time = time.time() - start_time

        # Verify all async methods were called
        jira_client.get_assigned_issues.assert_called_once_with("John", "recent")
        github_client.get_recent_commits.assert_called_once_with("John", "recent")
        github_client.get_recent_pull_requests.assert_called_once_with("John", "recent")

        # Verify results
        assert result["jira"]["issues"] == [{"key": "PROJ-123"}]
        assert result["github"]["commits"] == [{"sha": "abc123"}]
        assert result["github"]["pull_requests"] == [{"number": 42}]

        # Execution should be fast (concurrent, not sequential)
        assert execution_time < 1.0

    @pytest.mark.asyncio
    async def test_exception_handling(self, mock_clients):
        """
        ASYNC TEST: Test that exceptions are handled gracefully.
        """
        jira_client, github_client = mock_clients

        # Make one client raise an exception
        jira_client.get_assigned_issues.side_effect = Exception("JIRA API down")
        github_client.get_recent_commits.return_value = [{"sha": "abc123"}]
        github_client.get_recent_pull_requests.return_value = [{"number": 42}]

        service = AsyncActivityService(jira_client, github_client)
        parsed_query = ParsedQuery(
            member_name="John",
            intent=Intent.MEMBER_ACTIVITY_SUMMARY,
            time_range="recent",
        )

        # Even with JIRA failing, the method should complete
        result = await service.handle_intent(parsed_query)

        # JIRA should have empty results and error message
        assert result["jira"]["issues"] == []
        assert "JIRA API down" in result["jira"]["error"]

        # GitHub should still work
        assert result["github"]["commits"] == [{"sha": "abc123"}]
        assert result["github"]["pull_requests"] == [{"number": 42}]

    @pytest.mark.asyncio
    async def test_jira_only_intent(self, mock_clients):
        """
        ASYNC TEST: Test single API call for JIRA-only queries.
        """
        jira_client, github_client = mock_clients
        jira_client.get_assigned_issues.return_value = [{"key": "PROJ-456"}]

        service = AsyncActivityService(jira_client, github_client)
        parsed_query = ParsedQuery(
            member_name="Sarah",
            intent=Intent.JIRA_ISSUES,  # Only JIRA
            time_range="this_week",
        )

        result = await service.handle_intent(parsed_query)

        # Only JIRA should be called
        jira_client.get_assigned_issues.assert_called_once_with("Sarah", "this_week")
        github_client.get_recent_commits.assert_not_called()
        github_client.get_recent_pull_requests.assert_not_called()

        # Only JIRA results should be populated
        assert result["jira"]["issues"] == [{"key": "PROJ-456"}]
        assert result["github"] == {}


"""
# Example of how to run async tests
if __name__ == "__main__":
    # You can run async tests directly with asyncio.run()
    async def run_test():
        test_instance = TestAsyncActivityService()
        mock_clients = test_instance.mock_clients()
        await test_instance.test_concurrent_api_calls(mock_clients)

    # asyncio.run() is the entry point for running async code
    asyncio.run(run_test())
"""
