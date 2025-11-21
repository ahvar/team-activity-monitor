"""
Useful variables for later reference
"""

from typing import Any
from dataclasses import dataclass, field

__version__ = "0.1.0"
__Application__ = "TEAM_ACTIVITY_MONITOR"

MONITOR_LOG_CLI = f"{__Application__}_{__version__}_cli"
MONITOR_LOG_BACKEND = f"{__Application__}_{__version__}_frontend"

summary_styles = ["json", "txt"]
openai_models = ["gpt-3.5-turbo"]

# Team members are now loaded from configuration
# This will be set by the app initialization
TEAM_MEMBERS = []


def set_team_members(members):
    """Set team members from configuration"""
    global TEAM_MEMBERS
    TEAM_MEMBERS = members
