"""
Clockify API integration layer.

Responsibilities:
  - Fetch time entries for a date range via Clockify Reports API
  - Classify entries by work type (Feature / Bug Fix / Support / Meeting / Unknown)
  - Aggregate per-user summaries (dev hours, meeting hours, by client/product)
  - Cache results with @st.cache_data to avoid redundant API calls
  - Fall back to static data if the API is unreachable or key is missing

Environment variable:
  CLOCKIFY_API_KEY   – Clockify API key (or set via st.secrets["CLOCKIFY_API_KEY"])
  CLOCKIFY_WORKSPACE – Workspace ID        (or set via st.secrets["CLOCKIFY_WORKSPACE"])
"""

from __future__ import annotations

import os
import re
import logging
from datetime import datetime, timedelta
from typing import Optional

import requests
import streamlit as st

from models import (
    TimeEntry, UserSummary,
    FULL_TIMERS, EXPECTED_HOURS_PER_MONTH,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════
BASE_URL = "https://reports.api.clockify.me/v1"
USER_URL = "https://api.clockify.me/api/v1"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Work-type keyword lists
_FEATURE_KW = ['feature', 'new', 'implement', 'add', 'creat', 'develop',
               'build', 'integrat', 'enhance', 'redesign', 'refactor', 'migrat']
_BUG_KW     = ['bug', 'fix', 'issue', 'error', 'crash', 'fail', 'broken',
               'defect', 'patch', 'hotfix', 'resolve', 'revert']
_SUPPORT_KW = ['support', 'deploy', 'release', 'review', 'monitor', 'maintain',
               'upgrade', 'update', 'config', 'document', 'analys', 'investigat', 'research']
_MTG_KW     = ['meeting', 'standup', 'stand-up', 'sync', 'demo', 'call',
               'interview', 'onboard', 'training', 'workshop']


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def _get_api_key() -> Optional[str]:
    """Retrieve Clockify API key from env or Streamlit secrets."""
    key = os.environ.get("CLOCKIFY_API_KEY")
    if not key:
        try:
            key = st.secrets.get("CLOCKIFY_API_KEY")
        except Exception:
            pass
    return key


def _get_workspace_id() -> Optional[str]:
    """Retrieve Clockify workspace ID from env or Streamlit secrets."""
    ws = os.environ.get("CLOCKIFY_WORKSPACE")
    if not ws:
        try:
            ws = st.secrets.get("CLOCKIFY_WORKSPACE")
        except Exception:
            pass
    return ws


def classify_work_type(description: str) -> str:
    """Classify a time entry description into a work type."""
    d = description.lower()
    if any(k in d for k in _MTG_KW):
        return "Meeting"
    if any(k in d for k in _BUG_KW):
        return "Bug Fix"
    if any(k in d for k in _FEATURE_KW):
        return "Feature"
    if any(k in d for k in _SUPPORT_KW):
        return "Support"
    return "Unknown"


def _api_request(method: str, url: str, api_key: str,
                 json_body: dict = None, retries: int = MAX_RETRIES) -> Optional[dict]:
    """Make a Clockify API request with retry logic."""
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    for attempt in range(retries):
        try:
            if method == "GET":
                resp = requests.get(url, headers=headers, timeout=30)
            else:
                resp = requests.post(url, headers=headers, json=json_body, timeout=30)

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                import time
                wait = RETRY_DELAY * (attempt + 1)
                logger.warning(f"Clockify rate limit hit, waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                logger.error(f"Clockify API {resp.status_code}: {resp.text[:200]}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Clockify request error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                import time
                time.sleep(RETRY_DELAY)
    return None


# ═══════════════════════════════════════════════════════════════════════════
# LIVE DATA FETCHING
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner="Fetching Clockify data...")
def fetch_time_entries(start_date: str, end_date: str) -> list[TimeEntry]:
    """
    Fetch all time entries from Clockify for the given date range.

    Uses the Detailed Report endpoint (POST /workspaces/{id}/reports/detailed).
    Returns a list of TimeEntry dataclasses.

    Falls back to empty list if API is unreachable.
    """
    api_key = _get_api_key()
    workspace = _get_workspace_id()

    if not api_key or not workspace:
        logger.warning("Clockify credentials missing — returning empty list")
        return []

    entries: list[TimeEntry] = []
    page = 1
    page_size = 200

    while True:
        body = {
            "dateRangeStart": f"{start_date}T00:00:00.000Z",
            "dateRangeEnd": f"{end_date}T23:59:59.999Z",
            "detailedFilter": {"page": page, "pageSize": page_size},
            "sortColumn": "DATE",
            "sortOrder": "ASCENDING",
            "exportType": "JSON",
        }

        url = f"{BASE_URL}/workspaces/{workspace}/reports/detailed"
        data = _api_request("POST", url, api_key, json_body=body)

        if not data or "timeentries" not in data:
            break

        for row in data["timeentries"]:
            desc = row.get("description", "") or ""
            user = row.get("userName", "") or ""
            project = row.get("projectName", "") or ""
            client = row.get("clientName", "") or ""
            dur_secs = row.get("timeInterval", {}).get("duration", 0) or 0
            hours = dur_secs / 3600.0 if isinstance(dur_secs, (int, float)) else 0.0
            date_str = (row.get("timeInterval", {}).get("start", "") or "")[:10]
            billable = row.get("billable", False)

            entries.append(TimeEntry(
                user=user,
                date=date_str,
                hours=round(hours, 2),
                description=desc,
                project=project,
                client=client,
                work_type=classify_work_type(desc),
                billable=billable,
            ))

        # Pagination: stop when we get fewer than page_size
        if len(data["timeentries"]) < page_size:
            break
        page += 1

    logger.info(f"Clockify: fetched {len(entries)} entries ({start_date} → {end_date})")
    return entries


# ═══════════════════════════════════════════════════════════════════════════
# AGGREGATION
# ═══════════════════════════════════════════════════════════════════════════
def aggregate_users(entries: list[TimeEntry]) -> dict[str, UserSummary]:
    """
    Aggregate a list of TimeEntry into per-user UserSummary dicts.

    Returns {display_name: UserSummary}.
    """
    users: dict[str, UserSummary] = {}

    for e in entries:
        if e.user not in users:
            is_ft = e.user in FULL_TIMERS
            users[e.user] = UserSummary(
                name=e.user,
                full_time=is_ft,
                expected_hours=EXPECTED_HOURS_PER_MONTH if is_ft else 0.0,
            )

        u = users[e.user]
        u.total_hours += e.hours
        u.entry_count += 1

        if e.work_type == "Meeting":
            u.mtg_hours += e.hours
        else:
            u.dev_hours += e.hours

        # By client
        u.by_client[e.client] = u.by_client.get(e.client, 0) + e.hours
        # By product (use project as proxy)
        u.by_product[e.project] = u.by_product.get(e.project, 0) + e.hours
        # By work type
        u.by_work_type[e.work_type] = u.by_work_type.get(e.work_type, 0) + e.hours

    # Round all values
    for u in users.values():
        u.dev_hours = round(u.dev_hours, 2)
        u.mtg_hours = round(u.mtg_hours, 2)
        u.total_hours = round(u.total_hours, 2)

    return users


# ═══════════════════════════════════════════════════════════════════════════
# STATIC FALLBACK DATA
# ═══════════════════════════════════════════════════════════════════════════
def get_static_users() -> dict[str, UserSummary]:
    """
    Return hardcoded user data from the March 31 2026 Clockify export.
    Used when SAFE_MODE=True or when the API is unreachable.
    """
    raw = {
        'Deema':           {'dev': 114.14, 'mtg': 17.7,  'total': 131.84, 'full': True,  'entries': 68},
        'Engy Ahmed':      {'dev': 75.84,  'mtg': 55.59, 'total': 131.43, 'full': True,  'entries': 55},
        'Omar Mohamed':    {'dev': 121.98, 'mtg': 8.72,  'total': 130.7,  'full': True,  'entries': 52},
        'Yousef Eid':      {'dev': 126.0,  'mtg': 0.0,   'total': 126.0,  'full': True,  'entries': 21},
        'Sameh Amnoun':    {'dev': 75.57,  'mtg': 36.65, 'total': 112.22, 'full': True,  'entries': 62},
        'Omar Alaa':       {'dev': 103.55, 'mtg': 7.1,   'total': 110.65, 'full': False, 'entries': 49},
        'Daniel Lewis':    {'dev': 86.17,  'mtg': 24.33, 'total': 110.5,  'full': True,  'entries': 58},
        'Aesha H.':        {'dev': 98.41,  'mtg': 0.0,   'total': 98.41,  'full': True,  'entries': 42},
        'Nour Helal':      {'dev': 80.25,  'mtg': 13.5,  'total': 93.75,  'full': True,  'entries': 50},
        'Mohammed Y.':     {'dev': 68.04,  'mtg': 6.99,  'total': 75.03,  'full': False, 'entries': 41},
        'Nancy A.':        {'dev': 73.75,  'mtg': 0.0,   'total': 73.75,  'full': False, 'entries': 30},
        'Ali Murtaza':     {'dev': 51.17,  'mtg': 4.0,   'total': 55.17,  'full': False, 'entries': 33},
        'Jumana Yasser':   {'dev': 50.63,  'mtg': 0.0,   'total': 50.63,  'full': False, 'entries': 22},
        'AbdulRahman S.':  {'dev': 33.84,  'mtg': 7.8,   'total': 41.64,  'full': False, 'entries': 28},
        'Ibrahim A.':      {'dev': 36.51,  'mtg': 1.55,  'total': 38.06,  'full': False, 'entries': 25},
        'Nagwa':           {'dev': 24.3,   'mtg': 0.0,   'total': 24.3,   'full': False, 'entries': 18},
        'Ahmed Abouzaid':  {'dev': 12.59,  'mtg': 10.13, 'total': 22.72,  'full': False, 'entries': 15},
        'Jihad M.':        {'dev': 19.5,   'mtg': 2.75,  'total': 22.25,  'full': False, 'entries': 20},
        'Ahmed Alaa':      {'dev': 5.0,    'mtg': 0.0,   'total': 5.0,    'full': False, 'entries': 3},
        'Thejaswini N.':   {'dev': 2.86,   'mtg': 0.0,   'total': 2.86,   'full': False, 'entries': 22},
    }

    users = {}
    for name, d in raw.items():
        is_ft = name in FULL_TIMERS
        users[name] = UserSummary(
            name=name,
            dev_hours=d['dev'],
            mtg_hours=d['mtg'],
            total_hours=d['total'],
            full_time=is_ft,
            expected_hours=EXPECTED_HOURS_PER_MONTH if is_ft else 0.0,
            entry_count=d['entries'],
        )
    return users


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC INTERFACE
# ═══════════════════════════════════════════════════════════════════════════
def get_users(safe_mode: bool = True,
              start_date: str = "2026-03-01",
              end_date: str = "2026-03-31") -> dict[str, UserSummary]:
    """
    Main entry point. Returns user summaries.

    If safe_mode=True  → always returns static data (no API calls).
    If safe_mode=False → tries live API, falls back to static on failure.
    """
    if safe_mode:
        return get_static_users()

    try:
        entries = fetch_time_entries(start_date, end_date)
        if entries:
            return aggregate_users(entries)
        else:
            logger.warning("Clockify returned no entries — falling back to static")
            return get_static_users()
    except Exception as e:
        logger.error(f"Clockify fetch failed: {e} — falling back to static")
        return get_static_users()
