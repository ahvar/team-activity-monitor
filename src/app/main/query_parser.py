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
    Enhanced member name extraction with flexible matching.
    """
    lower_question = question.lower()

    # Remove common prefixes/suffixes that might interfere
    clean_question = re.sub(
        r"\b(what|show|tell|me|about|is|has|have|the)\b", " ", lower_question
    )
    clean_question = re.sub(r"\s+", " ", clean_question).strip()

    for member in TEAM_MEMBERS:
        member_lower = member.lower()

        # More specific patterns to avoid false matches
        patterns = [
            # Exact word boundary match
            rf"\b{re.escape(member_lower)}\b",
            # Possessive form: "John's"
            rf"\b{re.escape(member_lower)}'?s\b",
            # Followed by verbs (but not when used as project/thing name)
            rf"\b{re.escape(member_lower)}\s+(is|has|been|working)",
        ]

        for pattern in patterns:
            if re.search(pattern, clean_question):
                # ADDITIONAL CHECK: Avoid matching when used as project/object name
                # Check if preceded by "the", "a", "an" or followed by "project", "team", etc.
                context_pattern = rf"(the|a|an)\s+{re.escape(member_lower)}|{re.escape(member_lower)}\s+(project|team|repository|repo|branch|file|folder|directory)"
                if re.search(context_pattern, lower_question):
                    continue  # Skip this match, it's likely a project name
                return member

    return None


def infer_time_range(question: str) -> TimeRange:
    """Enhanced time range detection with more patterns."""
    q = question.lower()

    # This week patterns
    week_patterns = [
        "this week",
        "current week",
        "week",
        "past week",
        "last 7 days",
        "past 7 days",
        "weekly",
    ]

    # Recent patterns
    recent_patterns = [
        "recent",
        "recently",
        "these days",
        "lately",
        "current",
        "last few days",
        "past few days",
        "now",
        "currently",
    ]

    for pattern in week_patterns:
        if pattern in q:
            return "this_week"

    for pattern in recent_patterns:
        if pattern in q:
            return "recent"

    return "recent"


def infer_intent(question: str) -> Intent:
    """Enhanced intent detection with more flexible patterns."""
    q = question.lower()

    # GitHub Commits patterns (most specific first)
    commit_patterns = [
        "commit",
        "committed",
        "commits",
        "pushed",
        "push",
        "code changes",
        "recent changes",
        "coding",
    ]

    # GitHub Pull Requests patterns
    pr_patterns = [
        "pull request",
        "pull requests",
        "prs",
        "pr ",
        "merge request",
        "merge requests",
        "reviews",
    ]

    # More specific Jira patterns (remove generic "working on")
    jira_patterns = [
        "issue",
        "issues",
        "ticket",
        "tickets",
        "task",
        "tasks",
        "jira",
        "assigned",
        "current work",
    ]

    summary_patterns = [
        "working on",
        "been doing",
        "activity",
        "up to",
        "busy with",
        "focused on",
        "progress",
    ]

    # Check in priority order (most specific first)
    for pattern in commit_patterns:
        if pattern in q:
            return Intent.GITHUB_COMMITS

    for pattern in pr_patterns:
        if pattern in q:
            return Intent.GITHUB_PULL_REQUESTS

    for pattern in jira_patterns:
        if pattern in q:
            return Intent.JIRA_ISSUES

    for pattern in summary_patterns:
        if pattern in q:
            return Intent.MEMBER_ACTIVITY_SUMMARY

    return Intent.MEMBER_ACTIVITY_SUMMARY


def parse_query(question: str) -> ParsedQuery | None:
    """Enhanced query parsing with better error handling."""
    if not question or not question.strip():
        return None

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
