# app/activity_service.py
from typing import Any, Dict
from src.app.main.query_parser import ParsedQuery, Intent


class ActivityService:
    """
    Orchestrates calls to Jira + GitHub based on parsed intent.
    """

    def __init__(self, jira_client, github_client):
        self.jira = jira_client
        self.github = github_client

    def handle_intent(self, parsed: ParsedQuery) -> Dict[str, Any]:
        """
        Returns a dictionary with data that the response generator
        can turn into natural language.
        """
        member = parsed.member_name
        time_range = parsed.time_range

        result: Dict[str, Any] = {
            "member_name": member,
            "time_range": time_range,
            "intent": parsed.intent.name,
            "jira": {},
            "github": {},
        }

        if parsed.intent == Intent.MEMBER_ACTIVITY_SUMMARY:
            # both systems
            result["jira"]["issues"] = self.jira.get_assigned_issues(
                assignee_name=member,
                time_range=time_range,
            )
            result["github"]["commits"] = self.github.get_recent_commits(
                author_name=member,
                time_range=time_range,
            )
            result["github"]["pull_requests"] = self.github.get_recent_pull_requests(
                author_name=member,
                time_range=time_range,
            )

        elif parsed.intent == Intent.JIRA_ISSUES:
            result["jira"]["issues"] = self.jira.get_assigned_issues(
                assignee_name=member,
                time_range=time_range,
            )

        elif parsed.intent == Intent.GITHUB_COMMITS:
            result["github"]["commits"] = self.github.get_recent_commits(
                author_name=member,
                time_range=time_range,
            )

        elif parsed.intent == Intent.GITHUB_PULL_REQUESTS:
            result["github"]["pull_requests"] = self.github.get_recent_pull_requests(
                author_name=member,
                time_range=time_range,
            )

        return result
