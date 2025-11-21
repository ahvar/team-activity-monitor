# app/activity_service.py
import asyncio
from typing import Any, Dict
from src.app.main.query_parser import ParsedQuery, Intent


class AsyncActivityService:
    """
    Async orchestrator for API calls.
    """

    def __init__(self, jira_client, github_client):
        self.jira = jira_client
        self.github = github_client

    async def handle_intent(self, parsed: ParsedQuery) -> Dict[str, Any]:
        """
        COROUTINE: Returns a dictionary with data from concurrent API calls.

        Args:
            parsed: ParsedQuery containing member name, intent, and time range

        Returns:
            Dictionary with jira and github data
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
            # CONCURRENT EXECUTION: All three API calls happen simultaneously
            # instead of one after another (sequential)
            try:
                # Create coroutine objects (these don't execute yet)
                jira_task = self.jira.get_assigned_issues(member, time_range)
                github_commits_task = self.github.get_recent_commits(member, time_range)
                github_prs_task = self.github.get_recent_pull_requests(
                    member, time_range
                )

                # asyncio.gather() runs all tasks concurrently and waits for ALL to complete
                # return_exceptions=True means if one fails, others still complete
                jira_issues, github_commits, github_prs = await asyncio.gather(
                    jira_task,
                    github_commits_task,
                    github_prs_task,
                    return_exceptions=True,  # Don't fail entire request if one API fails
                )

                # Handle results - check if any returned exceptions
                if isinstance(jira_issues, Exception):
                    result["jira"]["issues"] = []
                    result["jira"]["error"] = str(jira_issues)
                else:
                    result["jira"]["issues"] = jira_issues

                if isinstance(github_commits, Exception):
                    result["github"]["commits"] = []
                    result["github"]["error"] = str(github_commits)
                else:
                    result["github"]["commits"] = github_commits

                if isinstance(github_prs, Exception):
                    result["github"]["pull_requests"] = []
                    result["github"]["error"] = str(github_prs)
                else:
                    result["github"]["pull_requests"] = github_prs

            except Exception as e:
                # This catches any errors in the gather() operation itself
                result["jira"]["issues"] = []
                result["github"]["commits"] = []
                result["github"]["pull_requests"] = []
                result["error"] = f"Failed to fetch data: {str(e)}"

        elif parsed.intent == Intent.JIRA_ISSUES:
            # Single async call - still need to await it
            try:
                result["jira"]["issues"] = await self.jira.get_assigned_issues(
                    member, time_range
                )
            except Exception as e:
                result["jira"]["issues"] = []
                result["jira"]["error"] = str(e)

        elif parsed.intent == Intent.GITHUB_COMMITS:
            # Single async call for commits only
            try:
                result["github"]["commits"] = await self.github.get_recent_commits(
                    member, time_range
                )
            except Exception as e:
                result["github"]["commits"] = []
                result["github"]["error"] = str(e)

        elif parsed.intent == Intent.GITHUB_PULL_REQUESTS:
            # Single async call for PRs only
            try:
                result["github"]["pull_requests"] = (
                    await self.github.get_recent_pull_requests(member, time_range)
                )
            except Exception as e:
                result["github"]["pull_requests"] = []
                result["github"]["error"] = str(e)

        return result
