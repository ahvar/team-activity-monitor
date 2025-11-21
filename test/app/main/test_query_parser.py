import unittest
from unittest.mock import patch
from src.app.main.query_parser import (
    extract_member_name,
    infer_time_range,
    infer_intent,
    parse_query,
    Intent,
    ParsedQuery,
)


class TestQueryParser(unittest.TestCase):

    def setUp(self):
        """Set up test data"""
        # Mock TEAM_MEMBERS for consistent testing
        self.mock_team_members = ["John", "Sarah", "Mike", "Lisa", "David", "Emma"]

    @patch("src.app.main.query_parser.TEAM_MEMBERS")
    def test_extract_member_name_valid_names(self, mock_team_members):
        """Test extraction of valid team member names"""
        mock_team_members.__iter__.return_value = self.mock_team_members

        test_cases = [
            ("What is John working on these days?", "John"),
            ("Show me Sarah's recent activity", "Sarah"),
            ("What has Mike been working on this week?", "Mike"),
            ("lisa's pull requests", "Lisa"),  # Test case insensitive
            ("Recent commits by DAVID", "David"),  # Test uppercase
            (
                "emma committed something yesterday",
                "Emma",
            ),  # Test lowercase in sentence
        ]

        for query, expected_name in test_cases:
            with self.subTest(query=query):
                result = extract_member_name(query)
                self.assertEqual(result, expected_name)

    @patch("src.app.main.query_parser.TEAM_MEMBERS")
    def test_extract_member_name_no_match(self, mock_team_members):
        """Test queries with no valid team member names"""
        mock_team_members.__iter__.return_value = self.mock_team_members

        test_cases = [
            "What is Bob working on?",  # Unknown name
            "Show me the team activity",  # No specific name
            "What are the recent commits?",  # No name
            "How is the project going?",  # Generic question
            "",  # Empty string
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = extract_member_name(query)
                self.assertIsNone(result)

    @patch("src.app.main.query_parser.TEAM_MEMBERS")
    def test_extract_member_name_partial_matches(self, mock_team_members):
        """Test that partial matches don't trigger false positives"""
        mock_team_members.__iter__.return_value = ["John", "Johnson"]

        test_cases = [
            ("What about Johnson's work?", "Johnson"),  # Should match Johnson, not John
            ("John is working hard", "John"),  # Should match John specifically
            ("The johnstone project", None),  # Should not match John
        ]

        for query, expected in test_cases:
            with self.subTest(query=query):
                result = extract_member_name(query)
                self.assertEqual(result, expected)

    def test_infer_time_range_this_week(self):
        """Test time range detection for 'this week'"""
        test_cases = [
            "What has John committed this week?",
            "Show me Sarah's work from this week",
            "Mike's activity for the week",
            "What did Lisa do this week?",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_time_range(query)
                self.assertEqual(result, "this_week")

    def test_infer_time_range_recent(self):
        """Test time range detection for 'recent'"""
        test_cases = [
            "What is John working on these days?",
            "Show me Sarah's recent activity",
            "What has Mike been doing lately?",
            "Lisa's recent commits",
            "David's activity recently",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_time_range(query)
                self.assertEqual(result, "recent")

    def test_infer_time_range_default(self):
        """Test default time range when no specific time mentioned"""
        test_cases = [
            "What is John working on?",
            "Show me Sarah's activity",
            "Mike's current tasks",
            "Lisa's assignments",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_time_range(query)
                self.assertEqual(result, "recent")  # Default should be recent

    def test_infer_intent_github_commits(self):
        """Test intent detection for GitHub commits"""
        test_cases = [
            "What has John committed this week?",
            "Show me Sarah's recent commits",
            "Mike's commits from yesterday",
            "What did Lisa commit?",
            "David committed what recently?",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_intent(query)
                self.assertEqual(result, Intent.GITHUB_COMMITS)

    def test_infer_intent_github_pull_requests(self):
        """Test intent detection for GitHub pull requests"""
        test_cases = [
            "Show me John's pull requests",
            "What pull requests has Sarah created?",
            "Mike's recent PRs",
            "Lisa's pull request activity",
            "David's open pull requests",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_intent(query)
                self.assertEqual(result, Intent.GITHUB_PULL_REQUESTS)

    def test_infer_intent_jira_issues(self):
        """Test intent detection for JIRA issues"""
        test_cases = [
            "What issues is John working on?",
            "Show me Sarah's JIRA tickets",
            "Mike's current issues",
            "Lisa's assigned tickets",
            "What tickets does David have?",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_intent(query)
                self.assertEqual(result, Intent.JIRA_ISSUES)

    def test_infer_intent_member_activity_summary(self):
        """Test intent detection for general activity summary"""
        test_cases = [
            "What is John working on these days?",
            "Show me Sarah's recent activity",
            "What has Mike been doing?",
            "Lisa's current work",
            "David's recent activity",
            "How is Emma doing?",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_intent(query)
                self.assertEqual(result, Intent.MEMBER_ACTIVITY_SUMMARY)

    @patch("src.app.main.query_parser.TEAM_MEMBERS")
    def test_parse_query_complete_parsing(self, mock_team_members):
        """Test complete query parsing with all components"""
        mock_team_members.__iter__.return_value = self.mock_team_members

        test_cases = [
            {
                "query": "What is John working on these days?",
                "expected": ParsedQuery(
                    member_name="John",
                    intent=Intent.MEMBER_ACTIVITY_SUMMARY,
                    time_range="recent",
                ),
            },
            {
                "query": "Show me Sarah's commits this week",
                "expected": ParsedQuery(
                    member_name="Sarah",
                    intent=Intent.GITHUB_COMMITS,
                    time_range="this_week",
                ),
            },
            {
                "query": "Mike's JIRA issues lately",
                "expected": ParsedQuery(
                    member_name="Mike", intent=Intent.JIRA_ISSUES, time_range="recent"
                ),
            },
            {
                "query": "Lisa's pull requests this week",
                "expected": ParsedQuery(
                    member_name="Lisa",
                    intent=Intent.GITHUB_PULL_REQUESTS,
                    time_range="this_week",
                ),
            },
        ]

        for test_case in test_cases:
            with self.subTest(query=test_case["query"]):
                result = parse_query(test_case["query"])
                expected = test_case["expected"]

                self.assertIsNotNone(result)
                self.assertEqual(result.member_name, expected.member_name)
                self.assertEqual(result.intent, expected.intent)
                self.assertEqual(result.time_range, expected.time_range)

    @patch("src.app.main.query_parser.TEAM_MEMBERS")
    def test_parse_query_no_member_found(self, mock_team_members):
        """Test parsing when no team member is found"""
        mock_team_members.__iter__.return_value = self.mock_team_members

        test_cases = [
            "What is Bob working on?",  # Unknown member
            "Show me the team activity",  # No specific member
            "How is the project going?",  # Generic question
            "",  # Empty string
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = parse_query(query)
                self.assertIsNone(result)

    def test_complex_queries_with_multiple_keywords(self):
        """Test queries that might contain multiple intent keywords"""
        with patch("src.app.main.query_parser.TEAM_MEMBERS", self.mock_team_members):
            test_cases = [
                {
                    "query": "Did John commit any tickets this week?",
                    "expected_intent": Intent.GITHUB_COMMITS,  # "commit" should take precedence
                    "expected_time": "this_week",
                },
                {
                    "query": "Show me Sarah's pull request issues",
                    "expected_intent": Intent.GITHUB_PULL_REQUESTS,  # First match wins
                    "expected_time": "recent",
                },
            ]

            for test_case in test_cases:
                with self.subTest(query=test_case["query"]):
                    result = parse_query(test_case["query"])
                    self.assertIsNotNone(result)
                    self.assertEqual(result.intent, test_case["expected_intent"])
                    self.assertEqual(result.time_range, test_case["expected_time"])

    def test_case_insensitive_parsing(self):
        """Test that parsing works regardless of case"""
        with patch("src.app.main.query_parser.TEAM_MEMBERS", ["John", "Sarah"]):
            test_cases = [
                "what is JOHN working on?",
                "SHOW ME sarah's COMMITS",
                "John's PULL REQUESTS this WEEK",
                "sarah committed SOMETHING recently",
            ]

            for query in test_cases:
                with self.subTest(query=query):
                    result = parse_query(query)
                    self.assertIsNotNone(result, f"Failed to parse: {query}")
                    self.assertIn(result.member_name, ["John", "Sarah"])

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        with patch("src.app.main.query_parser.TEAM_MEMBERS", ["John"]):
            test_cases = [
                ("", None),  # Empty string
                ("   ", None),  # Whitespace only
                ("What?", None),  # No member name
                (
                    "John",
                    ParsedQuery("John", Intent.MEMBER_ACTIVITY_SUMMARY, "recent"),
                ),  # Just name
                (
                    "JOHN JOHN JOHN",
                    ParsedQuery("John", Intent.MEMBER_ACTIVITY_SUMMARY, "recent"),
                ),  # Repeated name
            ]

            for query, expected in test_cases:
                with self.subTest(query=repr(query)):
                    result = parse_query(query)
                    if expected is None:
                        self.assertIsNone(result)
                    else:
                        self.assertEqual(result.member_name, expected.member_name)
                        self.assertEqual(result.intent, expected.intent)
                        self.assertEqual(result.time_range, expected.time_range)
