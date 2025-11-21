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
        self.mock_team_members = ["Arthur", "Alice", "Bob", "Charlie", "John", "Sarah"]

    @patch("src.app.main.query_parser.TEAM_MEMBERS")
    def test_extract_member_name_valid_names(self, mock_team_members):
        """Test extraction of valid team member names"""
        mock_team_members.__iter__.return_value = self.mock_team_members

        test_cases = [
            ("What is Arthur working on these days?", "Arthur"),
            ("Show me Alice's recent activity", "Alice"),
            ("What has Bob been working on this week?", "Bob"),
            ("charlie's pull requests", "Charlie"),  # Test case insensitive
            ("Recent commits by JOHN", "John"),  # Test uppercase
            (
                "sarah committed something yesterday",
                "Sarah",
            ),  # Test lowercase in sentence
            ("Arthur's recent work", "Arthur"),  # Possessive form
            ("What is Arthur working on?", "Arthur"),  # Followed by verb
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
            "What is Mike working on?",  # Unknown name (not in current team)
            "Show me the team activity",  # No specific name
            "What are the recent commits?",  # No name
            "How is the project going?",  # Generic question
            "",  # Empty string
            "   ",  # Whitespace only
            "What about the Arthur project?",  # Arthur as project name, not person
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = extract_member_name(query)
                self.assertIsNone(result)

    @patch("src.app.main.query_parser.TEAM_MEMBERS")
    def test_extract_member_name_partial_matches(self, mock_team_members):
        """Test that partial matches don't trigger false positives"""
        mock_team_members.__iter__.return_value = ["Bob", "Bobby"]

        test_cases = [
            ("What about Bobby's work?", "Bobby"),  # Should match Bobby, not Bob
            ("Bob is working hard", "Bob"),  # Should match Bob specifically
            ("The bobcat project", None),  # Should not match Bob
            ("robbie's contribution", None),  # Should not match Bob
        ]

        for query, expected in test_cases:
            with self.subTest(query=query):
                result = extract_member_name(query)
                self.assertEqual(result, expected)

    @patch("src.app.main.query_parser.TEAM_MEMBERS")
    def test_extract_member_name_enhanced_patterns(self, mock_team_members):
        """Test the enhanced matching patterns"""
        mock_team_members.__iter__.return_value = ["Arthur"]

        test_cases = [
            ("Arthur's commits", "Arthur"),  # Possessive form
            ("Arthur is working on", "Arthur"),  # Followed by "is working"
            ("Arthur has been coding", "Arthur"),  # Followed by "has been"
            ("Show Arthur working", "Arthur"),  # Followed by "working"
            ("What is Arthur working on?", "Arthur"),  # Complex sentence
        ]

        for query, expected in test_cases:
            with self.subTest(query=query):
                result = extract_member_name(query)
                self.assertEqual(result, expected)

    def test_infer_time_range_this_week(self):
        """Test time range detection for 'this week'"""
        test_cases = [
            "What has Arthur committed this week?",
            "Show me Alice's work from this week",
            "Bob's activity for the week",
            "What did Charlie do this week?",
            "Current week activity for Arthur",
            "Past week commits by Alice",
            "Last 7 days of work by Bob",
            "Weekly summary for Charlie",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_time_range(query)
                self.assertEqual(result, "this_week")

    def test_infer_time_range_recent(self):
        """Test time range detection for 'recent'"""
        test_cases = [
            "What is Arthur working on these days?",
            "Show me Alice's recent activity",
            "What has Bob been doing lately?",
            "Charlie's recent commits",
            "Arthur's activity recently",
            "Current work by Alice",
            "Last few days of commits by Bob",
            "What is Charlie currently working on?",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_time_range(query)
                self.assertEqual(result, "recent")

    def test_infer_time_range_default(self):
        """Test default time range when no specific time mentioned"""
        test_cases = [
            "What is Arthur working on?",
            "Show me Alice's activity",
            "Bob's current tasks",
            "Charlie's assignments",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_time_range(query)
                self.assertEqual(result, "recent")  # Default should be recent

    def test_infer_intent_github_commits(self):
        """Test intent detection for GitHub commits"""
        test_cases = [
            "What has Arthur committed this week?",
            "Show me Alice's recent commits",
            "Bob's commits from yesterday",
            "What did Charlie commit?",
            "Arthur committed what recently?",
            "Alice's recent code changes",
            "What has Bob pushed lately?",
            "Charlie's coding activity",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_intent(query)
                self.assertEqual(result, Intent.GITHUB_COMMITS)

    def test_infer_intent_github_pull_requests(self):
        """Test intent detection for GitHub pull requests"""
        test_cases = [
            "Show me Arthur's pull requests",
            "What pull requests has Alice created?",
            "Bob's recent PRs",
            "Charlie's pull request activity",
            "Arthur's open pull requests",
            "Alice's merge requests",
            "Bob's recent reviews",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_intent(query)
                self.assertEqual(result, Intent.GITHUB_PULL_REQUESTS)

    def test_infer_intent_jira_issues(self):
        """Test intent detection for JIRA issues"""
        test_cases = [
            "What issues is Arthur working on?",
            "Show me Alice's JIRA tickets",
            "Bob's current issues",
            "Charlie's assigned tickets",
            "What tickets does Arthur have?",
            "Alice's current tasks",
            "Bob's assigned work",
            "Charlie's Jira issues",
            "Charlie's current work",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_intent(query)
                self.assertEqual(result, Intent.JIRA_ISSUES)

    def test_infer_intent_member_activity_summary(self):
        """Test intent detection for general activity summary"""
        test_cases = [
            "What is Arthur working on these days?",
            "Show me Alice's recent activity",
            "What has Bob been doing?",
            "Arthur's recent activity",
            "How is Alice doing?",
            "What's Bob up to?",
            "Charlie's recent progress",
            "Alice's focus areas",
            "Bob's general activity",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                result = infer_intent(query)
                self.assertEqual(result, Intent.MEMBER_ACTIVITY_SUMMARY)

    def test_infer_intent_priority_order(self):
        """Test that intent detection follows priority order correctly"""
        test_cases = [
            # Commits should take priority over general "working on"
            ("Arthur committed on this issue", Intent.GITHUB_COMMITS),
            # PR patterns should take priority over issue patterns
            ("Alice's pull request issues", Intent.GITHUB_PULL_REQUESTS),
            # Specific patterns should take priority over general ones
            ("Bob's ticket commits", Intent.GITHUB_COMMITS),
        ]

        for query, expected_intent in test_cases:
            with self.subTest(query=query):
                result = infer_intent(query)
                self.assertEqual(result, expected_intent)

    @patch("src.app.main.query_parser.TEAM_MEMBERS")
    def test_parse_query_complete_parsing(self, mock_team_members):
        """Test complete query parsing with all components"""
        mock_team_members.__iter__.return_value = self.mock_team_members

        test_cases = [
            {
                "query": "What is Arthur working on these days?",
                "expected": ParsedQuery(
                    member_name="Arthur",
                    intent=Intent.MEMBER_ACTIVITY_SUMMARY,
                    time_range="recent",
                ),
            },
            {
                "query": "Show me Alice's commits this week",
                "expected": ParsedQuery(
                    member_name="Alice",
                    intent=Intent.GITHUB_COMMITS,
                    time_range="this_week",
                ),
            },
            {
                "query": "Bob's JIRA issues lately",
                "expected": ParsedQuery(
                    member_name="Bob", intent=Intent.JIRA_ISSUES, time_range="recent"
                ),
            },
            {
                "query": "Charlie's pull requests this week",
                "expected": ParsedQuery(
                    member_name="Charlie",
                    intent=Intent.GITHUB_PULL_REQUESTS,
                    time_range="this_week",
                ),
            },
            {
                "query": "What has Arthur committed recently?",
                "expected": ParsedQuery(
                    member_name="Arthur",
                    intent=Intent.GITHUB_COMMITS,
                    time_range="recent",
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
            "What is Mike working on?",  # Unknown member (Mike not in team)
            "Show me the team activity",  # No specific member
            "How is the project going?",  # Generic question
            "",  # Empty string
            "   ",  # Whitespace only
            "What are the commits?",  # No member mentioned
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
                    "query": "Did Arthur commit any tickets this week?",
                    "expected_intent": Intent.GITHUB_COMMITS,  # "commit" should take precedence
                    "expected_time": "this_week",
                },
                {
                    "query": "Show me Alice's pull request issues",
                    "expected_intent": Intent.GITHUB_PULL_REQUESTS,  # PR should take precedence
                    "expected_time": "recent",
                },
                {
                    "query": "Bob's ticket and commit activity",
                    "expected_intent": Intent.GITHUB_COMMITS,  # "commit" comes first in priority
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
        with patch("src.app.main.query_parser.TEAM_MEMBERS", ["Arthur", "Alice"]):
            test_cases = [
                "what is ARTHUR working on?",
                "SHOW ME alice's COMMITS",
                "Arthur's PULL REQUESTS this WEEK",
                "alice committed SOMETHING recently",
                "ARTHUR IS WORKING on tickets",
                "alice's recent ACTIVITY",
            ]

            for query in test_cases:
                with self.subTest(query=query):
                    result = parse_query(query)
                    self.assertIsNotNone(result, f"Failed to parse: {query}")
                    self.assertIn(result.member_name, ["Arthur", "Alice"])

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        with patch("src.app.main.query_parser.TEAM_MEMBERS", ["Arthur"]):
            test_cases = [
                ("", None),  # Empty string
                ("   ", None),  # Whitespace only
                ("What?", None),  # No member name
                (
                    "Arthur",
                    ParsedQuery("Arthur", Intent.MEMBER_ACTIVITY_SUMMARY, "recent"),
                ),  # Just name
                (
                    "ARTHUR ARTHUR ARTHUR",
                    ParsedQuery("Arthur", Intent.MEMBER_ACTIVITY_SUMMARY, "recent"),
                ),  # Repeated name
                (
                    "Arthur working",
                    ParsedQuery("Arthur", Intent.MEMBER_ACTIVITY_SUMMARY, "recent"),
                ),  # Simple phrase
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

    def test_real_world_queries(self):
        """Test queries that match your actual team configuration"""
        with patch(
            "src.app.main.query_parser.TEAM_MEMBERS",
            ["Arthur", "Alice", "Bob", "Charlie"],
        ):
            test_cases = [
                # These should work with your actual team
                (
                    "What is Arthur working on?",
                    "Arthur",
                    Intent.MEMBER_ACTIVITY_SUMMARY,
                ),
                ("Show me Arthur's current issues", "Arthur", Intent.JIRA_ISSUES),
                (
                    "What has Arthur committed this week?",
                    "Arthur",
                    Intent.GITHUB_COMMITS,
                ),
                (
                    "Arthur's recent pull requests",
                    "Arthur",
                    Intent.GITHUB_PULL_REQUESTS,
                ),
                ("Alice's recent activity", "Alice", Intent.MEMBER_ACTIVITY_SUMMARY),
                ("Bob's commits lately", "Bob", Intent.GITHUB_COMMITS),
                ("Charlie's tickets", "Charlie", Intent.JIRA_ISSUES),
            ]

            for query, expected_member, expected_intent in test_cases:
                with self.subTest(query=query):
                    result = parse_query(query)
                    self.assertIsNotNone(result, f"Failed to parse: {query}")
                    self.assertEqual(result.member_name, expected_member)
                    self.assertEqual(result.intent, expected_intent)

    def test_enhanced_error_handling(self):
        """Test the enhanced error handling"""
        with patch("src.app.main.query_parser.TEAM_MEMBERS", []):
            # Empty team members list
            result = parse_query("What is Arthur working on?")
            self.assertIsNone(result)

        # Test with None input (should not crash)
        result = parse_query(None)
        self.assertIsNone(result)
