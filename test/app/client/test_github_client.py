import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from src.app.client.async_github import AsyncGitHubClient


class TestGitHubClient(unittest.TestCase):
    def setUp(self):
        """Set up test client with mock API key"""
        self.api_key = "fake-github-token"
        self.client = GitHubClient(api_key=self.api_key)

    def test_initialization(self):
        """Test client initialization"""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.base_url, "https://api.github.com")
        self.assertIn("Authorization", self.client.headers)
        self.assertEqual(self.client.headers["Authorization"], f"Bearer {self.api_key}")

    @patch("requests.get")
    def test_get_recent_commits_success(self, mock_get):
        """Test successful commit retrieval"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "sha": "abc123",
                    "commit": {
                        "message": "Fix authentication bug",
                        "author": {"date": "2024-01-15T10:30:00Z"},
                    },
                    "repository": {"name": "team-project"},
                }
            ]
        }
        mock_get.return_value = mock_response

        # Act
        result = self.client.get_recent_commits(author_name="John", time_range="recent")

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sha"], "abc123")
        self.assertEqual(result[0]["message"], "Fix authentication bug")

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("search/commits", call_args[0][0])
        self.assertIn("author:John", call_args[0][0])

    @patch("requests.get")
    def test_get_recent_pull_requests_success(self, mock_get):
        """Test successful PR retrieval"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "number": 42,
                    "title": "Add user dashboard feature",
                    "state": "open",
                    "created_at": "2024-01-15T10:30:00Z",
                }
            ]
        }
        mock_get.return_value = mock_response

        # Act
        result = self.client.get_recent_pull_requests(
            author_name="Sarah", time_range="this_week"
        )

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["number"], 42)
        self.assertEqual(result[0]["title"], "Add user dashboard feature")

    @patch("requests.get")
    def test_time_range_filtering(self, mock_get):
        """Test different time range parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        # Test recent (default)
        self.client.get_recent_commits("John", "recent")

        # Test this_week
        self.client.get_recent_commits("John", "this_week")

        # Verify different date filters were used
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.get")
    def test_api_error_handling(self, mock_get):
        """Test handling of API errors"""
        # Test 401 Unauthorized
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "401 Unauthorized"
        )
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as cm:
            self.client.get_recent_commits("John", "recent")

        self.assertIn("authentication", str(cm.exception).lower())

    @patch("requests.get")
    def test_connection_test(self, mock_get):
        """Test connection testing functionality"""
        # Test successful connection
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.client.test_connection()
        self.assertTrue(result)

        # Test failed connection
        mock_get.side_effect = requests.ConnectionError()
        result = self.client.test_connection()
        self.assertFalse(result)
