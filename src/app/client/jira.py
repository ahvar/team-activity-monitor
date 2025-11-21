# app/jira_client.py (interface sketch)
class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str): ...

    def get_assigned_issues(self, assignee_name: str, time_range: str):
        """
        Return a list of issues (dicts) assigned to this user, optionally
        filtered by time_range (e.g. updated this week).
        """
        ...
