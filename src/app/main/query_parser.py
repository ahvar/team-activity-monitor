# app/query_parser.py
from __future__ import annotations
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Literal

from src.utils.references import TEAM_MEMBERS


class Intent(Enum):
    MEMBER_ACTIVITY_SUMMARY = auto()  # Jira + GitHub
    JIRA_ISSUES = auto()  # Jira issues only
    GITHUB_COMMITS = auto()  # GitHub commits only
    GITHUB_PULL_REQUESTS = auto()  # GitHub PRs only


TimeRange = Literal["recent", "this_week", "all_time"]


@dataclass
class ParsedQuery:
    member_name: str
    intent: Intent
    time_range: TimeRange = "recent"


def extract_member_name(question: str) -> str | None:
    """
    Match the question against the known TEAM_MEMBERS list.

    This avoids brittle capitalization heuristics and ensures we only
    respond for explicitly supported users. Falls back to None if no
    known name is present so the caller can surface a friendly error.
    """
    lower_question = question.lower()

    for member in TEAM_MEMBERS:
        pattern = rf"\b{re.escape(member.lower())}\b"
        if re.search(pattern, lower_question):
            return member

    return None


def infer_time_range(question: str) -> TimeRange:
    q = question.lower()
    if "this week" in q or "week" in q:
        return "this_week"
    if "recent" in q or "these days" in q or "lately" in q:
        return "recent"
    return "recent"


def infer_intent(question: str) -> Intent:
    q = question.lower()

    if "commit" in q or "committed" in q:
        return Intent.GITHUB_COMMITS

    if "pull request" in q or "pull requests" in q or "prs" in q:
        return Intent.GITHUB_PULL_REQUESTS

    if "issue" in q or "ticket" in q:
        return Intent.JIRA_ISSUES

    # default to full activity summary
    return Intent.MEMBER_ACTIVITY_SUMMARY


def parse_query(question: str) -> ParsedQuery | None:
    member_name = extract_member_name(question)
    if not member_name:
        return None

    intent = infer_intent(question)
    time_range = infer_time_range(question)

    return ParsedQuery(
        member_name=member_name,
        intent=intent,
        time_range=time_range,
    )
