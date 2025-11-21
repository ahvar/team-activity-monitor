"""
Clean, readable response templates without excessive formatting.
"""


def format_commits_only_response(
    member_name: str, github_commits: list, github_error: str = None
) -> str:
    """Clean commits response with better message formatting."""
    if github_error:
        return f"I couldn't get {member_name}'s recent commits: {github_error}"

    if not github_commits:
        return f"{member_name} hasn't made any recent commits."

    count = len(github_commits)
    intro = f"{member_name} has {count} recent commit{'s' if count != 1 else ''}:"

    lines = [intro, ""]

    for i, commit in enumerate(github_commits[:5], 1):
        short_sha = commit["sha"][:7] if commit.get("sha") else "unknown"
        message = commit.get("message", "No message")

        # ✅ CLEAN UP THE MESSAGE BETTER
        # Remove extra whitespace and newlines
        message = " ".join(message.split())

        # Handle merge commits specially - they're usually verbose
        if message.lower().startswith("merge pull request"):
            # Extract just the PR info: "Merge pull request #123 from user/branch"
            parts = message.split()
            if len(parts) >= 6:  # "Merge pull request #123 from user/branch"
                pr_number = parts[3]  # "#123"
                branch_info = parts[5] if len(parts) > 5 else "unknown"
                # Extract just the feature name from "ahvar/feature-name"
                if "/" in branch_info:
                    feature = branch_info.split("/")[-1]
                    message = f"Merge PR {pr_number}: {feature}"
                else:
                    message = f"Merge PR {pr_number}"

        # Truncate at word boundaries, not mid-word
        if len(message) > 50:
            # Find the last space before position 47 to avoid cutting words
            truncate_pos = message.rfind(" ", 0, 47)
            if truncate_pos > 20:  # Make sure we don't truncate too short
                message = message[:truncate_pos] + "..."
            else:
                message = message[:47] + "..."

        lines.append(f"{i}. {short_sha} - {message}")

    if count > 5:
        lines.append("")
        lines.append(f"Plus {count - 5} more commits.")

    return "\n".join(lines)


def format_jira_only_response(
    member_name: str, jira_issues: list, jira_error: str = None
) -> str:
    """Simple, clean Jira response."""
    if jira_error:
        return f"I couldn't access {member_name}'s Jira tickets: {jira_error}"

    if not jira_issues:
        return f"{member_name} doesn't have any active Jira tickets right now."

    count = len(jira_issues)
    if count == 1:
        intro = f"{member_name} is working on 1 Jira ticket:"
    else:
        intro = f"{member_name} is working on {count} Jira tickets:"

    lines = [intro, ""]

    for i, issue in enumerate(jira_issues[:5], 1):
        lines.append(f"{i}. {issue['key']} - {issue['summary']}")
        lines.append(f"   Status: {issue['status']}")
        lines.append("")  # Space between items

    if count > 5:
        lines.append(f"Plus {count - 5} more tickets.")

    return "\n".join(lines)


def format_prs_only_response(
    member_name: str, github_prs: list, github_error: str = None
) -> str:
    """Clean pull requests response."""
    if github_error:
        return f"I couldn't get {member_name}'s pull requests: {github_error}"

    if not github_prs:
        return f"{member_name} doesn't have any recent pull requests."

    count = len(github_prs)
    intro = f"{member_name} has {count} recent pull request{'s' if count != 1 else ''}:"

    lines = [intro, ""]

    for i, pr in enumerate(github_prs[:5], 1):
        title = pr.get("title", "No title")

        # ✅ CLEAN UP PR TITLES TOO
        title = " ".join(title.split())  # Remove extra whitespace

        # Truncate at word boundaries
        if len(title) > 45:
            truncate_pos = title.rfind(" ", 0, 42)
            if truncate_pos > 15:
                title = title[:truncate_pos] + "..."
            else:
                title = title[:42] + "..."

        state = pr.get("state", "unknown")
        number = pr.get("number", "N/A")

        lines.append(f"{i}. #{number} - {title}")
        lines.append(f"   Status: {state}")
        lines.append("")

    if count > 5:
        lines.append(f"Plus {count - 5} more pull requests.")

    return "\n".join(lines)


def format_activity_summary_response(
    member_name: str,
    jira_issues: list,
    github_commits: list,
    github_prs: list,
    jira_error: str = None,
    github_error: str = None,
) -> str:
    """Clean summary response."""

    # Handle complete failure case
    if jira_error and github_error:
        return f"I'm having trouble accessing both Jira and GitHub data for {member_name} right now. Please try again later."

    # Handle no activity case
    if (
        not jira_issues
        and not jira_error
        and not github_commits
        and not github_error
        and not github_prs
    ):
        return f"{member_name} appears to be having a quiet period - no recent Jira tickets, commits, or pull requests found."

    lines = [f"Here's what {member_name} has been working on:", ""]

    # Jira Issues Section
    lines.append("JIRA TICKETS:")
    if jira_error:
        lines.append(f"  Could not fetch Jira data: {jira_error}")
    elif jira_issues:
        lines.append(
            f"  {len(jira_issues)} active ticket{'s' if len(jira_issues) != 1 else ''}"
        )
        for issue in jira_issues[:3]:
            lines.append(f"  • {issue['key']}: {issue['summary']} ({issue['status']})")
        if len(jira_issues) > 3:
            lines.append(f"  • Plus {len(jira_issues) - 3} more tickets")
    else:
        lines.append("  No active tickets")

    lines.append("")  # Space between sections

    # GitHub Commits Section - USE IMPROVED FORMATTING
    lines.append("RECENT COMMITS:")
    if github_error:
        lines.append(f"  Could not fetch GitHub data: {github_error}")
    elif github_commits:
        lines.append(
            f"  {len(github_commits)} recent commit{'s' if len(github_commits) != 1 else ''}"
        )
        for commit in github_commits[:3]:
            short_sha = commit["sha"][:7] if commit.get("sha") else "unknown"
            message = commit.get("message", "No message")

            # ✅ APPLY SAME CLEANING LOGIC
            message = " ".join(message.split())

            if message.lower().startswith("merge pull request"):
                parts = message.split()
                if len(parts) >= 6:
                    pr_number = parts[3]
                    branch_info = parts[5] if len(parts) > 5 else "unknown"
                    if "/" in branch_info:
                        feature = branch_info.split("/")[-1]
                        message = f"Merge PR {pr_number}: {feature}"
                    else:
                        message = f"Merge PR {pr_number}"

            if len(message) > 40:
                truncate_pos = message.rfind(" ", 0, 37)
                if truncate_pos > 15:
                    message = message[:truncate_pos] + "..."
                else:
                    message = message[:37] + "..."

            lines.append(f"  • {short_sha}: {message}")
        if len(github_commits) > 3:
            lines.append(f"  • Plus {len(github_commits) - 3} more commits")
    else:
        lines.append("  No recent commits")

    lines.append("")  # Space between sections

    # Pull Requests Section
    lines.append("PULL REQUESTS:")
    if github_error:
        lines.append(f"  Could not fetch GitHub data: {github_error}")
    elif github_prs:
        open_prs = [pr for pr in github_prs if pr.get("state") == "open"]
        closed_prs = [pr for pr in github_prs if pr.get("state") == "closed"]

        if open_prs:
            lines.append(f"  {len(open_prs)} open, {len(closed_prs)} recently closed")
        else:
            lines.append(f"  {len(closed_prs)} recently closed")

        for pr in github_prs[:3]:
            title = pr.get("title", "No title")
            title = " ".join(title.split())  # Clean whitespace
            if len(title) > 35:
                truncate_pos = title.rfind(" ", 0, 32)
                if truncate_pos > 15:
                    title = title[:truncate_pos] + "..."
                else:
                    title = title[:32] + "..."
            state = pr.get("state", "unknown")
            lines.append(f"  • #{pr.get('number', '?')}: {title} ({state})")

        if len(github_prs) > 3:
            lines.append(f"  • Plus {len(github_prs) - 3} more pull requests")
    else:
        lines.append("  No recent pull requests")

    return "\n".join(lines)
