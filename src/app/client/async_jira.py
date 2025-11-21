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
            # ✅ IMPROVED: Handle different assignee name formats
            # Try different JQL formats for assignee
            if assignee_name.lower() in ["me", "currentuser", "current"]:
                base_jql = "assignee = currentUser()"
            else:
                base_jql = f'assignee = "{assignee_name}"'

            # Add time filter if specified
            time_filter = self._get_time_filter(time_range)
            if time_filter:
                jql = f"{base_jql} AND updated >= {time_filter} ORDER BY updated DESC"
            else:
                jql = f"{base_jql} ORDER BY updated DESC"

            # ✅ USE THE CORRECT ENDPOINT
            url = f"{self.base_url}/rest/api/3/search/jql"
            params = {
                "jql": jql,
                "maxResults": 20,
                "fields": "key,summary,status,updated,assignee,priority,issuetype",
            }

            logger.info(f"Searching Jira with JQL: {jql}")

            # ASYNC HTTP REQUEST
            async with aiohttp.ClientSession(
                auth=self.auth, timeout=self.timeout
            ) as session:
                # ✅ Use GET method with params for JQL endpoint
                async with session.get(
                    url, headers=self.headers, params=params
                ) as response:

                    if response.status == 401:
                        raise Exception(
                            "JIRA authentication failed - check credentials"
                        )
                    elif response.status == 400:
                        error_text = await response.text()
                        logger.error(f"JQL query failed: {jql}")
                        logger.error(f"Error response: {error_text}")
                        raise Exception(f"Invalid JQL query: {error_text}")
                    elif response.status == 403:
                        raise Exception("JIRA API access forbidden - check permissions")

                    response.raise_for_status()

                    # Parse JSON response asynchronously
                    data = await response.json()

                    # Transform response to cleaner format
                    issues = []
                    for issue in data.get("issues", []):
                        fields = issue["fields"]

                        # ✅ SAFE FIELD ACCESS - handle None values properly
                        assignee = fields.get("assignee")
                        assignee_name = (
                            assignee.get("displayName", "Unassigned")
                            if assignee
                            else "Unassigned"
                        )

                        priority = fields.get("priority")
                        priority_name = (
                            priority.get("name", "None") if priority else "None"
                        )

                        status = fields.get("status", {})
                        status_name = (
                            status.get("name", "Unknown") if status else "Unknown"
                        )

                        issuetype = fields.get("issuetype", {})
                        type_name = (
                            issuetype.get("name", "Unknown") if issuetype else "Unknown"
                        )

                        issues.append(
                            {
                                "key": issue["key"],
                                "summary": fields.get("summary", "No summary"),
                                "status": status_name,
                                "updated": fields.get("updated", "Unknown"),
                                "assignee": assignee_name,
                                "priority": priority_name,
                                "issue_type": type_name,
                            }
                        )

                    logger.info(f"Found {len(issues)} issues for {assignee_name}")
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
