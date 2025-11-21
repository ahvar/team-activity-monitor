# team-activity-monitor

A lightweight Flask prototype that answers questions like “What is John working
on these days?” by aggregating Jira and GitHub activity and letting an OpenAI
model summarize the results.

## Natural-language query handling

- Queries are parsed with `src/app/main/query_parser.py`, which now anchors on
  a validated list of supported team members (see `TEAM_MEMBERS` in
  `src/utils/references.py`). This avoids false positives from capitalized
  words and makes “user not found” errors predictable.
- Intent detection is keyword-based (`commit`, `pull request`, `issue/ticket`)
  and falls back to a combined activity summary. Time ranges default to
  “recent” unless phrases like “this week” appear.

## Jira integration plan

- **Authentication**: HTTP basic auth with email + API token (token in
  `JIRA_API_KEY`).
- **Assigned issues**: `GET /rest/api/3/search` with a JQL such as
  `assignee = "<name>" AND statusCategory != Done ORDER BY updated DESC`.
- **Issue details**: Optionally enrich via `GET /rest/api/3/issue/{issueIdOrKey}`
  for fields like status, summary, priority, and updated timestamp.
- **Recent updates**: Filter the search JQL with `updated >= -7d` (or similar)
  when the time range is “this week/recent.”

Example user questions handled:
- “What Jira tickets is John working on?” → `Intent.JIRA_ISSUES` with time
  range inferred from wording.
- “Show me Sarah’s current issues” → same flow; returns assigned, non-done
  issues.

## GitHub integration plan

- **Authentication**: Personal Access Token in `GITHUB_API_KEY` sent via
  `Authorization: Bearer <token>` with the `application/vnd.github+json`
  Accept header.
- **Recent commits**: `GET /search/commits?q=author:<username>+committer-date:>=<ISO-date>`
  (requires the `application/vnd.github.cloak-preview` Accept header for commit
  search).
- **Active pull requests**: `GET /search/issues?q=author:<username>+is:pr+state:open`
  (adjust `state` for merged/closed history as needed).
- **Recent repositories contributed to**: use the events feed
  `GET /users/<username>/events` and collect repositories from push and
  pull_request events, or query `/users/<username>/repos` for owned work.

Example user questions handled:
- “What has Mike committed this week?” → commit search filtered to 7 days.
- “Show me Lisa’s recent pull requests” → PR search sorted by `updated`.

## AI response generation

- Use the OpenAI **Chat Completions API** (e.g., `gpt-4o-mini`) to summarize
  Jira and GitHub payloads into conversational answers.
- Provide guardrails: if `parse_query` cannot match a name, return a clear
  “user not found” response; if both integrations return empty lists, explain
  there is no recent activity.
- Keep prompts concise; include the member name, time window, and bulletized
  Jira/GitHub items. Templates are acceptable for the MVP if the OpenAI API is
  unavailable.
