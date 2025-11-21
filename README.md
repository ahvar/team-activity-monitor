# Team Activity Monitor

A lightweight Flask web application that answers natural language questions like "What is John working on these days?" by retrieving data from Jira and GitHub APIs and formatting for chat.

## 📋 Supported Query Types

### General Activity Summary
```
"What is John working on these days?"
"Show me Sarah's recent activity"
"How is Mike doing lately?"
```

### Jira-Specific Queries
```
"What issues is Sarah working on?"
"Show me John's current tickets"
"Mike's assigned tasks"
```

### GitHub Commits
```
"What has Mike committed this week?"
"Sarah's recent code changes"
"Show me John's commits"
```
**Returns**: Recent commits with cleaned commit messages

### Pull Requests
```
"Mike's recent pull requests"
"Show me John's PRs"
"Lisa's merge requests"
```
**Returns**: Recent pull requests with status and titles

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- Jira account with API access
- GitHub account with Personal Access Token

### Quick Start

1. **Clone and install**:
```bash
git clone https://github.com/ahvar/team-activity-monitor.git
cd team-activity-monitor
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your API credentials
```

3. **Set up environment variables**:
```bash
# Required
SECRET_KEY=your-secret-key-here
GITHUB_API_KEY=ghp_your_github_token_here
JIRA_API_KEY=your_jira_api_token_here
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
TEAM_MEMBERS=Sarah,Mike,Lisa,John

# Optional
OPENAI_API_KEY=sk-your-openai-key-here
GITHUB_BASE_URL=https://api.github.com
```

4. **Run the application**:

**Development mode**:
```bash
flask run
# OR
python -m flask run --host=0.0.0.0 --port=5000
```

**Production mode**:
```bash
gunicorn -b 0.0.0.0:5000 --workers 4 --worker-class gevent src.activity_monitor_flask_shell_ctx:app
```

5. **Visit**: http://localhost:5000



## 🚀 Features

### Smart Query Processing
- **Natural language understanding**: Ask questions in plain English
- **Flexible member name matching**: Handles possessive forms, case variations, and context
- **Intent detection**: Automatically routes to Jira issues, GitHub commits, pull requests, or combined summaries
- **Time range parsing**: Understands "this week", "recently", "lately", etc.

### Concurrent API Integration  
- **Async performance**: Simultaneous API calls to Jira and GitHub for fast responses
- **Error resilience**: Graceful handling of API failures with partial results
- **Smart mapping**: Handles different usernames across platforms (e.g., "Arthur" → "ahvar" on GitHub)

### Conversational Interface
- **Clean web chat**: Bootstrap-powered responsive interface with real-time messaging
- **Formatted responses**: Proper line breaks, truncated messages, readable output
- **Example queries**: Built-in suggestions to help users get started
- **CSRF protection**: Secure form handling with Flask-WTF


## 🧪 API Configuration Details

### GitHub API Setup
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Create token with scopes: `repo`, `user:email`, `read:org`
3. Add to `.env` as `GITHUB_API_KEY=ghp_...`

### Jira API Setup  
1. Go to Atlassian Account Settings → Security → API tokens
2. Create new token
3. Add to `.env` with your email:
```bash
JIRA_API_KEY=ATATT3xFfGF0...
JIRA_EMAIL=your-email@company.com
JIRA_BASE_URL=https://yourcompany.atlassian.net
```

### Team Member Mapping
Configure team members in `.env`:
```bash
TEAM_MEMBERS=John,Sarah,Mike,Lisa
```

For members with different usernames across platforms, update the mapping in `src/app/main/async_activity_service.py`:
```python
# Handle username differences
if member.lower() == "john":
    github_user = "john_github"  # GitHub username
    jira_user = "john@company.com"  # Jira email
elif member.lower() == "sarah":
    github_user = "sarah_dev"  # GitHub username  
    jira_user = "sarah@company.com"  # Jira email
else:
    github_user = member
    jira_user = member
```

## 🏗️ Architecture Overview

### Core Components

```
src/
├── app/
│   ├── main/
│   │   ├── routes.py                 # Flask routes & request handling
│   │   ├── query_parser.py           # Natural language processing  
│   │   ├── async_activity_service.py # Orchestrates concurrent API calls
│   │   ├── response_templates.py     # Formats API data into readable responses
│   │   └── forms.py                  # CSRF-protected forms
│   ├── client/
│   │   ├── async_github.py           # Async GitHub API client
│   │   └── async_jira.py             # Async Jira API client
│   └── templates/
│       ├── base.html                 # Bootstrap layout
│       └── index.html                # Chat interface
├── utils/
│   ├── references.py                 # Global configuration
│   └── logging_utils.py              # Custom logging utilities
└── config.py                         # Environment configuration
```

### Request Flow
1. **User Input** → Query parsing (member name, intent, time range)
2. **Concurrent API Calls** → GitHub + Jira APIs called simultaneously  
3. **Response Generation** → Template-based formatting with error handling
4. **Web Interface** → Real-time chat updates with line break preservation

### Performance Features
- **Async/await**: True concurrent API calls using `asyncio.gather()`
- **Connection pooling**: Reused HTTP sessions with `aiohttp`
- **Smart caching**: Optional 5-minute response caching (easily configurable)
- **Error isolation**: One API failure doesn't break the other

## 🧪 Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
pytest

# Run specific test modules
pytest test/app/client/test_async_github_client.py -v
pytest test/app/main/test_query_parser.py -v
pytest test/app/main/test_activity_service.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Test Coverage
- ✅ **Query Parser**: Member name extraction, intent detection, time range parsing
- ✅ **GitHub Client**: API calls, error handling, date filtering
- ✅ **Jira Client**: Authentication, JQL queries, response parsing  
- ✅ **Activity Service**: Concurrent operations, exception handling
- ✅ **Response Templates**: Message formatting, edge cases

## 🚀 Deployment Options

### Option 1: Simple Gunicorn
```bash
gunicorn -b 0.0.0.0:5000 --workers 4 --worker-class gevent src.activity_monitor_flask_shell_ctx:app
```

### Option 2: Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install -e .
COPY src/ ./src/
COPY .env ./
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "gevent", "src.activity_monitor_flask_shell_ctx:app"]
```

### Option 3: As a Python Package
```bash
pip install -e .
team-monitor  # Runs the application
```

## 📝 Example Interactions

**General Activity**:
```
You: What is Arthur working on these days?

Team-Monitor: Here's what Arthur has been working on:

JIRA TICKETS:
• SCRUM-2: Task 2 (In Progress)
• SCRUM-1: Task 1 (To Do)

RECENT COMMITS:
• 9098963: Merge PR #5: develop
• d49ea07: Document integrations and validate member parsing

PULL REQUESTS:
• #4: Document integrations and validate... (closed)
• #3: processing user queries (closed)
```

**Specific Intent**:
```
You: What has Arthur committed this week?

Team-Monitor: Arthur has 5 recent commits:

1. 9098963 - Merge PR #5: develop
2. d49ea07 - Document integrations and validate member parsing  
3. df52e6c - Fixed authentication bug in login
4. 4a27145 - Updated user dashboard with metrics
5. 1bfe26e - Added new response templates

Plus 2 more commits.
```

## 🐛 Troubleshooting

### Common Issues

**"No team member found"**:
- Check `TEAM_MEMBERS` in `.env` matches your query
- Verify member name spelling and capitalization

**"GitHub authentication failed"**:
- Verify `GITHUB_API_KEY` in `.env` 
- Check token has required scopes (`repo`, `user:email`)
- Test token: `curl -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/user`

**"Jira authentication failed"**:
- Verify `JIRA_API_KEY`, `JIRA_EMAIL`, and `JIRA_BASE_URL` in `.env`
- Test token: `curl -u EMAIL:TOKEN https://yourcompany.atlassian.net/rest/api/3/myself`

**Slow responses**:
- Check network connectivity to both APIs
- Monitor logs for timeout errors
- Consider adjusting timeout values in client classes

### Debug Mode
Enable detailed logging:
```bash
export FLASK_ENV=development  
export FLASK_DEBUG=1
flask run
```

Check logs in the console for detailed API call information and error traces.

## 🔮 Future Enhancements

### 🤖 **AI-Powered Response Generation**
- **OpenAI GPT-4/ChatGPT integration**: Replace template-based responses with dynamic AI-generated answers
- **Context-aware responses**: AI that understands team dynamics and project context

### 📈 **Enhanced Functionality**
- **Caching layer**: Redis/memcached for faster repeated queries
- **User authentication**: Multi-tenant support with user-specific API keys  
- **Advanced queries**: Date ranges, project filtering, team summaries
- **Metrics dashboard**: Activity trends and insights
- **CLI interface**: Command-line tool
- **Webhook support**: Real-time updates from Jira/GitHub

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.