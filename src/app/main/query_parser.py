# app/query_parser.py
import re
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Literal


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
    Very naive first pass: assume the first capitalized word
    that's not at the beginning of the sentence is the name.
    In practice you might map against a known list of team members.
    """
    tokens = question.split()
    for i, token in enumerate(tokens):
        # skip first word in case it's "What", "Show", etc.
        if i == 0:
            continue
        # strip punctuation like "Mike?"
        word = re.sub(r"[^\w]", "", token)
        if word and word[0].isupper():
            return word
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
