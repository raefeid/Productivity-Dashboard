"""
Normalized data models shared across Clockify and Azure DevOps sources.

These dataclasses define the canonical shapes that every downstream consumer
(logic/, ui/, app_v2.py) can rely on, regardless of which API produced them.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════
# TEAM MEMBER
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class TeamMember:
    """One person on the team, combining Clockify + DevOps identity."""
    name: str                          # Display name used as primary key
    email: Optional[str] = None
    full_time: bool = False
    expected_hours: float = 0.0        # 0 for part-timers
    clockify_id: Optional[str] = None  # Clockify user ID
    ado_display_name: Optional[str] = None  # Azure DevOps display name (may differ)


# ═══════════════════════════════════════════════════════════════════════════
# TIME ENTRY  (source: Clockify)
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class TimeEntry:
    """A single Clockify time entry."""
    user: str            # Clockify display name
    date: str            # ISO date YYYY-MM-DD
    hours: float
    description: str = ""
    project: str = ""
    client: str = ""
    work_type: str = "Unknown"  # Feature / Bug Fix / Support / Meeting / Unknown
    billable: bool = False


# ═══════════════════════════════════════════════════════════════════════════
# USER SUMMARY  (aggregated from TimeEntry)
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class UserSummary:
    """Aggregated hours for one user in a given period."""
    name: str
    dev_hours: float = 0.0
    mtg_hours: float = 0.0
    total_hours: float = 0.0
    full_time: bool = False
    expected_hours: float = 0.0
    by_client: dict = field(default_factory=dict)   # {client: hours}
    by_product: dict = field(default_factory=dict)   # {product: hours}
    by_work_type: dict = field(default_factory=dict) # {work_type: hours}
    entry_count: int = 0


# ═══════════════════════════════════════════════════════════════════════════
# TICKET  (source: Azure DevOps work items)
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class Ticket:
    """A single Azure DevOps work item (Bug, Task, Feature, etc.)."""
    id: int
    title: str
    work_item_type: str = ""          # Bug / Task / Feature / User Story / Issue
    state: str = ""                    # Closed / Active / etc.
    assigned_to: Optional[str] = None  # Current assignee display name
    attributed_to: Optional[str] = None  # Developer credited (post-QA-flow logic)
    project: str = ""
    sprint: str = ""
    created_date: Optional[str] = None
    closed_date: Optional[str] = None
    cycle_time_days: Optional[float] = None
    went_through_qa: bool = False
    assignment_chain: list = field(default_factory=list)  # Ordered list of assignees
    is_standup: bool = False           # True if excluded as standup/meeting ticket


# ═══════════════════════════════════════════════════════════════════════════
# PR  (source: Azure DevOps Git)
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class PullRequest:
    """A single merged pull request from Azure DevOps."""
    id: int
    title: str
    repo: str = ""
    project: str = ""
    author: str = ""
    author_email: Optional[str] = None
    closed_date: Optional[str] = None
    reviewers: list = field(default_factory=list)  # [{'name': str, 'vote': int}]


# ═══════════════════════════════════════════════════════════════════════════
# ATTRIBUTION SUMMARY  (aggregated from Ticket + PR)
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class AttributionSummary:
    """DevOps contribution summary for one developer."""
    name: str
    display_name: str = ""
    total_tickets: int = 0
    qa_flow: int = 0
    inferred: int = 0
    by_type: dict = field(default_factory=dict)    # {type: count}
    by_sprint: dict = field(default_factory=dict)  # {sprint: count}
    avg_cycle_time: Optional[float] = None
    prs_authored: int = 0
    prs_reviewed: int = 0
    data_source: str = "static"   # 'static' | 'live' | 'live-only'


# ═══════════════════════════════════════════════════════════════════════════
# TEAM ROSTER  (canonical full-time / part-time classification)
# ═══════════════════════════════════════════════════════════════════════════

EXPECTED_HOURS_PER_MONTH = 119.5  # Ramadan-adjusted: 13d × 5.5h + 6d × 7h

FULL_TIMERS = [
    "Yousef Eid", "Nour Helal", "Engy Ahmed", "Deema",
    "Daniel Lewis", "Omar Mohamed", "Sameh Amnoun",
    "Aesha H.", "Ijaz Ahmed", "Muzamil S.", "Farah Eid",
]

# Map: Clockify display name → Azure DevOps display name
NAME_MAP_CK_TO_ADO = {
    "Deema": "Deema Ayman",
    "Aesha H.": "Aesha Hassen",
    "Muzamil S.": "Muzamil Siddiqui",
    "Ibrahim A.": "Ibrahim Amer",
    "Thejaswini N.": "Thejaswini.Nagaraju@infasme.com",
    "Jihad M.": "Jihad.Mejdoub infasme.com",
    "Prajwal S.": "Prajwal Shetty",
    "Mohamed M.": "Mohamed Moiniddin",
    "Nagwa": "Nagwa T.",
}

# QA gate people — excluded from ticket attribution
QA_GATE = ["aesha", "ijaz", "farah"]

# Standup/meeting ticket title regex (excluded from Omar Alaa's count)
STANDUP_REGEX = r"^meeting|^standup|^stand-up|_meeting|^v3 merge meeting|^det meeting"
