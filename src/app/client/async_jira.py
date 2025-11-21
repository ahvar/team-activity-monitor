# app/jira_client.py (interface sketch)
import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class AsyncJiraClient:
    """
    Async JIRA API client
    """

    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        # aiohttp.BasicAuth handles the authentication
        self.auth = aiohttp.BasicAuth(email, api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        # Timeout configuration for async requests
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def test_connection(self) -> bool:
        """
        COROUTINE: Test if JIRA API is accessible with current credentials.
        """
        try:
            async with aiohttp.ClientSession(
                auth=self.auth, timeout=self.timeout
            ) as session:
                async with session.get(
                    f"{self.base_url}/rest/api/3/myself", headers=self.headers
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"JIRA connection test failed: {str(e)}")
            return False

    async def get_assigned_issues(
        self, assignee_name: str, time_range: str
    ) -> List[Dict]:
        """
        COROUTINE: Get issues assigned to a user.
        params: assignee_name: JIRA username or display name
        params: time_range: "recent", "this_week", or "all_time"
        returns: List of issue dictionaries with key, summary, status, etc.
        """
        try:
            # Build JQL (JIRA Query Language) query
            jql = f'assignee = "{assignee_name}" AND statusCategory != Done'

            # Add time filter if specified
            time_filter = self._get_time_filter(time_range)
            if time_filter:
                jql += f" AND updated >= {time_filter}"

            jql += " ORDER BY updated DESC"

            url = f"{self.base_url}/rest/api/3/search"
            params = {
                "jql": jql,
                "maxResults": 20,
                "fields": "key,summary,status,updated,assignee,priority",
            }
            async with aiohttp.ClientSession(
                auth=self.auth, timeout=self.timeout
            ) as session:
                # 'await' pauses execution until the HTTP request completes
                async with session.get(
                    url, headers=self.headers, params=params
                ) as response:

                    if response.status == 401:
                        raise Exception(
                            "JIRA authentication failed - check email/API token"
                        )
                    elif response.status == 403:
                        raise Exception(
                            "JIRA permission denied - insufficient access rights"
                        )
                    elif response.status == 400:
                        # JQL syntax error or invalid parameters
                        error_text = await response.text()
                        raise Exception(f"JIRA query error: {error_text}")

                    # Raise exception for other HTTP errors
                    response.raise_for_status()

                    # Parse JSON response asynchronously
                    data = await response.json()

                    # Transform response to cleaner format
                    issues = []
                    for issue in data.get("issues", []):
                        fields = issue["fields"]
                        issues.append(
                            {
                                "key": issue["key"],
                                "summary": fields["summary"],
                                "status": fields["status"]["name"],
                                "updated": fields["updated"],
                                "assignee": fields.get("assignee", {}).get(
                                    "displayName", "Unassigned"
                                ),
                                "priority": fields.get("priority", {}).get(
                                    "name", "None"
                                ),
                            }
                        )

                    return issues

        except aiohttp.ClientError as e:
            logger.error(f"JIRA API error fetching issues: {str(e)}")
            raise Exception(f"Failed to fetch issues from JIRA: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in JIRA client: {str(e)}")
            raise

    def _get_time_filter(self, time_range: str) -> Optional[str]:
        """
        Convert time_range to JIRA time format.
        params: time_range: "recent", "this_week", or "all_time"
        returns: JIRA-compatible time string like "-7d" or None
        """
        if time_range == "this_week":
            return "-7d"  # JIRA format: last 7 days
        elif time_range == "recent":
            return "-14d"  # JIRA format: last 14 days
        else:
            return None  # No time filter for "all_time"
