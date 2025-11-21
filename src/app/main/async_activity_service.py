# app/activity_service.py
import asyncio
import logging
from typing import Any, Dict
from src.app.main.query_parser import ParsedQuery, Intent

logger = logging.getLogger(__name__)


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
        """
        member = parsed.member_name
        time_range = parsed.time_range

        logger.info(
            f"Processing request for member: {member}, intent: {parsed.intent.name}, time_range: {time_range}"
        )

        result: Dict[str, Any] = {
            "member_name": member,
            "time_range": time_range,
            "intent": parsed.intent.name,
            "jira": {},
            "github": {},
        }

        if parsed.intent == Intent.MEMBER_ACTIVITY_SUMMARY:
            try:
                logger.info("Starting concurrent API calls...")

                if member.lower() == "arthur":  # my use case
                    jira_task = self.jira.get_assigned_issues(
                        "arthurvargasdev@gmail.com", time_range
                    )
                    github_commits_task = self.github.get_recent_commits(
                        "ahvar", time_range
                    )
                    github_prs_task = self.github.get_recent_pull_requests(
                        "ahvar", time_range
                    )
                else:
                    # Standard base cases: John, Sarah, Mike, Lisa
                    jira_task = self.jira.get_assigned_issues(member, time_range)
                    github_commits_task = self.github.get_recent_commits(
                        member, time_range
                    )
                    github_prs_task = self.github.get_recent_pull_requests(
                        member, time_range
                    )

                jira_issues, github_commits, github_prs = await asyncio.gather(
                    jira_task,
                    github_commits_task,
                    github_prs_task,
                    return_exceptions=True,
                )

                logger.info("API call results:")
                logger.info(
                    f"  Jira: {len(jira_issues) if isinstance(jira_issues, list) else f'ERROR: {jira_issues}'}"
                )
                logger.info(
                    f"  GitHub commits: {len(github_commits) if isinstance(github_commits, list) else f'ERROR: {github_commits}'}"
                )
                logger.info(
                    f"  GitHub PRs: {len(github_prs) if isinstance(github_prs, list) else f'ERROR: {github_prs}'}"
                )

                # Handle results
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
                logger.error(f"Error in concurrent API calls: {e}")
                result["jira"]["issues"] = []
                result["github"]["commits"] = []
                result["github"]["pull_requests"] = []
                result["error"] = f"Failed to fetch data: {str(e)}"

        elif parsed.intent == Intent.JIRA_ISSUES:
            try:
                # Handle your case for Jira-only queries
                jira_user = (
                    "arthurvargasdev@gmail.com"
                    if member.lower() == "arthur"
                    else member
                )
                result["jira"]["issues"] = await self.jira.get_assigned_issues(
                    jira_user, time_range
                )
            except Exception as e:
                result["jira"]["issues"] = []
                result["jira"]["error"] = str(e)

        elif parsed.intent == Intent.GITHUB_COMMITS:
            try:
                # Handle your case for GitHub-only queries
                github_user = "ahvar" if member.lower() == "arthur" else member
                result["github"]["commits"] = await self.github.get_recent_commits(
                    github_user, time_range
                )
            except Exception as e:
                result["github"]["commits"] = []
                result["github"]["error"] = str(e)

        elif parsed.intent == Intent.GITHUB_PULL_REQUESTS:
            try:
                # Handle your case for PR-only queries
                github_user = "ahvar" if member.lower() == "arthur" else member
                result["github"]["pull_requests"] = (
                    await self.github.get_recent_pull_requests(github_user, time_range)
                )
            except Exception as e:
                result["github"]["pull_requests"] = []
                result["github"]["error"] = str(e)

        return result
