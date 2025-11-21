import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AsyncGitHubClient:
    """
    Async GitHub API client.
    """

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url or "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",  # TODO: should be stored in a variable somewhere else not hardcoded
        }
        # Timeout configuration for async requests
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def test_connection(self) -> bool:
        """
        COROUTINE: Test if GitHub API is accessible.
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.base_url}/user", headers=self.headers
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"GitHub connection test failed: {str(e)}")
            return False

    async def get_recent_commits(self, author_name: str, time_range: str) -> List[Dict]:
        """
        COROUTINE: Get recent commits by author.
        """
        try:
            # Build the search query
            date_filter = self._get_date_filter(time_range)
            query = f"author:{author_name}"
            if date_filter:
                query += f" committer-date:>={date_filter}"

            url = f"{self.base_url}/search/commits"
            params = {
                "q": query,
                "sort": "committer-date",
                "order": "desc",
                "per_page": 10,  # TODO: this is defined in a config, we should use that value; no hardcoding
            }

            # Special headers for commit search API
            search_headers = self.headers.copy()
            search_headers["Accept"] = "application/vnd.github.cloak-preview+json"

            # ASYNC HTTP REQUEST: This is the key difference from sync code
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # 'await' pauses execution until the HTTP request completes
                async with session.get(
                    url, headers=search_headers, params=params
                ) as response:

                    if response.status == 401:
                        raise Exception("GitHub authentication failed - check API key")
                    elif response.status == 403:
                        raise Exception("GitHub API rate limit exceeded")

                    # response.raise_for_status() equivalent
                    response.raise_for_status()

                    # Parse JSON response asynchronously
                    data = await response.json()

                    # Transform the response to cleaner format
                    commits = []
                    for item in data.get("items", []):
                        commits.append(
                            {
                                "sha": item["sha"],
                                "message": item["commit"]["message"],
                                "date": item["commit"]["author"]["date"],
                                "repository": item.get("repository", {}).get(
                                    "name", "unknown"
                                ),
                            }
                        )

                    return commits

        except aiohttp.ClientError as e:
            logger.error(f"GitHub API error fetching commits: {str(e)}")
            raise Exception(f"Failed to fetch commits from GitHub: {str(e)}")

    async def get_recent_pull_requests(
        self, author_name: str, time_range: str
    ) -> List[Dict]:
        """
        COROUTINE: Get recent pull requests by author.
        """
        try:
            date_filter = self._get_date_filter(time_range)
            query = f"author:{author_name} is:pr"
            if date_filter:
                query += f" updated:>={date_filter}"

            url = f"{self.base_url}/search/issues"  # PRs are searched via issues API
            params = {"q": query, "sort": "updated", "order": "desc", "per_page": 10}

            # Another async HTTP request
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    url, headers=self.headers, params=params
                ) as response:

                    if response.status == 401:
                        raise Exception("GitHub authentication failed - check API key")

                    response.raise_for_status()
                    data = await response.json()

                    # Transform response
                    pull_requests = []
                    for item in data.get("items", []):
                        pull_requests.append(
                            {
                                "number": item["number"],
                                "title": item["title"],
                                "state": item["state"],
                                "created_at": item["created_at"],
                                "updated_at": item["updated_at"],
                                "html_url": item["html_url"],
                            }
                        )

                    return pull_requests

        except aiohttp.ClientError as e:
            logger.error(f"GitHub API error fetching PRs: {str(e)}")
            raise Exception(f"Failed to fetch pull requests from GitHub: {str(e)}")

    def _get_date_filter(self, time_range: str) -> Optional[str]:
        """
        Convert time_range to ISO date string.
        """
        if time_range == "this_week":
            date = datetime.now() - timedelta(days=7)
            return date.strftime("%Y-%m-%d")
        elif time_range == "recent":
            date = datetime.now() - timedelta(days=14)
            return date.strftime("%Y-%m-%d")
        else:
            return None
