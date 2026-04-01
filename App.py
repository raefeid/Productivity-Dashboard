import streamlit as st

import pandas as pd

import plotly.graph_objects as go

import plotly.express as px

from datetime import datetime, timedelta

import json

import requests

from functools import lru_cache

import base64
 
# ═══════════════════════════════════════════════════════════════════════════

# STREAMLIT CONFIG

# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(

    page_title="Team Time Dashboard",

    page_icon="📊",

    layout="wide",

    initial_sidebar_state="collapsed"

)
 
# ═══════════════════════════════════════════════════════════════════════════

# HARDCODED DATA (Fallback / Current)

# ═══════════════════════════════════════════════════════════════════════════

USERS_DATA = {

    'Deema': {'dev': 114.14, 'mtg': 17.7, 'total': 131.84, 'full': True},

    'Engy Ahmed': {'dev': 75.84, 'mtg': 55.59, 'total': 131.43, 'full': True},

    'Omar Mohamed': {'dev': 121.98, 'mtg': 8.72, 'total': 130.7, 'full': True},

    'Yousef Eid': {'dev': 126.0, 'mtg': 0.0, 'total': 126.0, 'full': False},

    'Sameh Amnoun': {'dev': 75.57, 'mtg': 36.65, 'total': 112.22, 'full': True},

    'Omar Alaa': {'dev': 103.55, 'mtg': 7.1, 'total': 110.65, 'full': True},

    'Daniel Lewis': {'dev': 86.17, 'mtg': 24.33, 'total': 110.5, 'full': True},

    'Aesha H.': {'dev': 98.41, 'mtg': 0.0, 'total': 98.41, 'full': True},

    'Nour Helal': {'dev': 80.25, 'mtg': 13.5, 'total': 93.75, 'full': True},

    'Mohammed Y.': {'dev': 68.04, 'mtg': 6.99, 'total': 75.03, 'full': True},

    'Nancy A.': {'dev': 73.75, 'mtg': 0.0, 'total': 73.75, 'full': True},

    'Ali Murtaza': {'dev': 51.17, 'mtg': 4.0, 'total': 55.17, 'full': True},

    'Jumana Yasser': {'dev': 50.63, 'mtg': 0.0, 'total': 50.63, 'full': False},

    'AbdulRahman S.': {'dev': 33.84, 'mtg': 7.8, 'total': 41.64, 'full': False},

    'Ibrahim A.': {'dev': 36.51, 'mtg': 1.55, 'total': 38.06, 'full': False},

    'Nagwa': {'dev': 24.3, 'mtg': 0.0, 'total': 24.3, 'full': False},

    'Ahmed Abouzaid': {'dev': 12.59, 'mtg': 10.13, 'total': 22.72, 'full': False},

    'Jihad M.': {'dev': 19.5, 'mtg': 2.75, 'total': 22.25, 'full': False},

    'Ahmed Alaa': {'dev': 5.0, 'mtg': 0.0, 'total': 5.0, 'full': False},

    'Thejaswini N.': {'dev': 2.86, 'mtg': 0.0, 'total': 2.86, 'full': False},

}
 
ATTRIBUTION_DATA = {

    'Omar Alaa': {'total': 62, 'qaFlow': 4, 'reviewed': 0, 'authored': 14},

    'Daniel Lewis': {'total': 26, 'qaFlow': 22, 'reviewed': 0, 'authored': 8},

    'Sameh Amnoun': {'total': 24, 'qaFlow': 23, 'reviewed': 49, 'authored': 0},

    'Muzamil S.': {'total': 15, 'qaFlow': 6, 'reviewed': 16, 'authored': 16},

    'Thejaswini N.': {'total': 7, 'qaFlow': 0, 'reviewed': 0, 'authored': 5},

    'Deema': {'total': 5, 'qaFlow': 5, 'reviewed': 0, 'authored': 9},

    'Omar Mohamed': {'total': 2, 'qaFlow': 0, 'reviewed': 0, 'authored': 4},

    'Jihad M.': {'total': 1, 'qaFlow': 0, 'reviewed': 0, 'authored': 3},

    'Ibrahim A.': {'total': 1, 'qaFlow': 1, 'reviewed': 0, 'authored': 16},

    'Engy Ahmed': {'total': 1, 'qaFlow': 0, 'reviewed': 1, 'authored': 1},

    'Nour Helal': {'total': 0, 'qaFlow': 0, 'reviewed': 4, 'authored': 3},

    'Yousef Eid': {'total': 0, 'qaFlow': 0, 'reviewed': 3, 'authored': 4},

}
 
EXPECTED_HOURS = 119.5

FULL_TIMERS = [k for k, v in USERS_DATA.items() if v['full']]

CAP = {k: EXPECTED_HOURS for k in FULL_TIMERS}
 
# ═══════════════════════════════════════════════════════════════════════════

# HEADER

# ═══════════════════════════════════════════════════════════════════════════

st.markdown("# 📊 Team Time Dashboard")

st.markdown("**Nourhan Hosny's Workspace** · 20 members · 800 entries · 172 tickets · 85 PRs · Updated 31/03/2026")
 
# ═══════════════════════════════════════════════════════════════════════════

# LAYOUT: TABS

# ═══════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs(["🏢 Overview", "⚡ Utilization", "🛠️ DevOps"])
 
# ═══════════════════════════════════════════════════════════════════════════

# TAB 1: OVERVIEW

# ═══════════════════════════════════════════════════════════════════════════

with tab1:

    # Top KPIs

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric("Total Hours", "1,457", "20 members")

    with col2:

        st.metric("Dev Hours", "1,260", "86% of time")

    with col3:

        st.metric("Meeting Hours", "197", "13% of time")

    with col4:

        st.metric("Dev Efficiency", "86%", "↑ from 83%")
 
    st.divider()
 
    # Dev/Meeting Donut

    col1, col2 = st.columns(2)

    with col1:

        fig = go.Figure(data=[go.Pie(

            labels=['Development', 'Meetings'],

            values=[1260, 197],

            hole=0.4,

            marker=dict(colors=['#4f46e5', '#f59e0b'])

        )])

        fig.update_layout(height=300, showlegend=True, margin=dict(l=0, r=0, t=0, b=0))

        st.plotly_chart(fig, use_container_width=True)
 
    # Work type breakdown

    with col2:

        work_types = {

            'Feature': 318,

            'Bug Fix': 181,

            'Support': 144,

            'Unknown': 618

        }

        fig = go.Figure(data=[go.Pie(

            labels=list(work_types.keys()),

            values=list(work_types.values()),

            hole=0.4,

            marker=dict(colors=['#10b981', '#ef4444', '#3b82f6', '#94a3b8'])

        )])

        fig.update_layout(height=300, showlegend=True, margin=dict(l=0, r=0, t=0, b=0))

        st.plotly_chart(fig, use_container_width=True)
 
    st.divider()
 
    # Work type details

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric("Feature Work", "318h", "106 entries")

    with col2:

        st.metric("Bug Fixes", "181h", "103 entries")

    with col3:

        st.metric("Support", "144h", "102 entries")

    with col4:

        st.metric("Unclassified", "618h", "253 entries")
 
    st.divider()
 
    # All Team Members Table

    st.subheader("👥 All Team Members")
 
    members_list = []

    for name, data in USERS_DATA.items():

        tickets = ATTRIBUTION_DATA.get(name, {}).get('total', 0)

        prs = ATTRIBUTION_DATA.get(name, {}).get('authored', 0)

        expected = CAP.get(name, '—')

        delta = data['total'] - expected if isinstance(expected, (int, float)) else None

        delta_str = f"{delta:+.1f}h" if delta is not None else "—"

        delta_color = "🟢" if delta and delta >= 0 else "🔴" if delta and delta < 0 else ""
 
        members_list.append({

            'Name': name,

            'Dev': f"{data['dev']:.1f}h",

            'Meetings': f"{data['mtg']:.1f}h",

            'Total': f"{data['total']:.1f}h",

            'Expected': f"{expected}h" if isinstance(expected, (int, float)) else "—",

            'Δ': f"{delta_color} {delta_str}",

            'Tickets': tickets,

            'PRs': prs,

        })
 
    df_members = pd.DataFrame(members_list)

    st.dataframe(df_members, use_container_width=True, hide_index=True)
 
    st.divider()
 
    # PR Reviewers

    st.subheader("👀 PR Reviewers")

    reviewers_list = []

    for name, data in ATTRIBUTION_DATA.items():

        if data['reviewed'] > 0:

            badge = "🏆" if data['reviewed'] >= 40 else "👀"

            reviewers_list.append({

                'Name': name,

                'Reviews': data['reviewed'],

                'Role': badge + (" Lead Reviewer" if data['reviewed'] >= 40 else " Active Reviewer")

            })
 
    df_reviewers = pd.DataFrame(sorted(reviewers_list, key=lambda x: x['Reviews'], reverse=True))

    st.dataframe(df_reviewers, use_container_width=True, hide_index=True)
 
# ═══════════════════════════════════════════════════════════════════════════

# TAB 2: UTILIZATION

# ═══════════════════════════════════════════════════════════════════════════

with tab2:

    # Expected capacity KPIs

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:

        st.metric("Expected Capacity", "119.5h", "Per full-timer")

    with col2:

        full_timer_hours = sum(USERS_DATA[n]['total'] for n in FULL_TIMERS)

        avg_util = (full_timer_hours / (len(FULL_TIMERS) * EXPECTED_HOURS) * 100)

        st.metric("Avg Utilization", f"{avg_util:.0f}%", "Full-timers only")

    with col3:

        avg_logged = full_timer_hours / len(FULL_TIMERS)

        st.metric("Avg Hours Logged", f"{avg_logged:.1f}h", "Full-timers only")
 
    # Above/Below Expected

    above = [n for n in FULL_TIMERS if USERS_DATA[n]['total'] > EXPECTED_HOURS]

    below = [n for n in FULL_TIMERS if USERS_DATA[n]['total'] < EXPECTED_HOURS]
 
    with col4:

        st.metric("Above Expected", len(above), ", ".join(above[:2]))

    with col5:

        st.metric("Below Expected", len(below), ", ".join(below[:2]))

    with col6:

        st.metric("Ramadan Adj.", "5.5h", "Mar 1–18 · 7h after")
 
    st.divider()
 
    # Hours vs Expected Chart

    util_data = []

    for name in FULL_TIMERS:

        util_data.append({

            'Name': name,

            'Logged': USERS_DATA[name]['total'],

            'Expected': EXPECTED_HOURS

        })
 
    df_util = pd.DataFrame(util_data).sort_values('Logged', ascending=False)
 
    fig = go.Figure()

    fig.add_trace(go.Bar(x=df_util['Name'], y=df_util['Logged'], name='Logged Hours', marker_color='#4f46e5'))

    fig.add_hline(y=EXPECTED_HOURS, line_dash="dash", line_color="#ef4444", annotation_text="Expected")

    fig.update_layout(

        title="Hours vs Expected Capacity",

        xaxis_title="Team Member",

        yaxis_title="Hours",

        height=400,

        showlegend=False,

        hovermode='x unified'

    )

    st.plotly_chart(fig, use_container_width=True)
 
    st.divider()
 
    # Full Utilization Table

    st.subheader("⚡ Full-Timer Utilization")

    util_table = []

    for name in sorted(FULL_TIMERS, key=lambda x: USERS_DATA[x]['total'], reverse=True):

        logged = USERS_DATA[name]['total']

        util_pct = (logged / EXPECTED_HOURS * 100)

        delta = logged - EXPECTED_HOURS

        delta_str = f"{delta:+.1f}h"
 
        util_table.append({

            'Name': name,

            'Expected': f"{EXPECTED_HOURS}h",

            'Logged': f"{logged:.1f}h",

            'Δ': delta_str,

            'Dev': f"{USERS_DATA[name]['dev']:.1f}h",

            'Meetings': f"{USERS_DATA[name]['mtg']:.1f}h",

            'Util %': f"{util_pct:.0f}%"

        })
 
    df_util_table = pd.DataFrame(util_table)

    st.dataframe(df_util_table, use_container_width=True, hide_index=True)
 
# ═══════════════════════════════════════════════════════════════════════════

# TAB 3: DEVOPS

# ═══════════════════════════════════════════════════════════════════════════

with tab3:

    st.subheader("🎯 DevOps Metrics")

    st.markdown("**172 closed tickets · 85 merged PRs** (15 standup/meeting tickets excluded from Omar Alaa)")
 
    # Attribution KPIs

    col1, col2, col3, col4, col5, col6 = st.columns(6)
 
    total_tix = sum(d['total'] for d in ATTRIBUTION_DATA.values())

    qa_flow_tix = sum(d['qaFlow'] for d in ATTRIBUTION_DATA.values())
 
    with col1:

        st.metric("Attributed Tickets", total_tix, "March 2026")

    with col2:

        st.metric("Via QA Flow", qa_flow_tix, "Confirmed handoff")

    with col3:

        st.metric("Inferred", total_tix - qa_flow_tix, "Most-recent assignee")

    with col4:

        qa_conf = (qa_flow_tix / total_tix * 100) if total_tix > 0 else 0

        st.metric("QA Confidence", f"{qa_conf:.0f}%", "Via confirmed flow")

    with col5:

        total_auth = sum(d['authored'] for d in ATTRIBUTION_DATA.values())

        st.metric("PRs Authored", total_auth, "Delivery ownership")

    with col6:

        st.metric("Avg Cycle Time", "8.7d", "Activated → Closed")
 
    st.divider()
 
    # Attribution Table

    st.subheader("🏗️ Attribution by Developer")
 
    attr_list = []

    for name, data in ATTRIBUTION_DATA.items():

        if data['total'] > 0 or data['authored'] > 0 or data['reviewed'] > 0:

            qa_pct = (data['qaFlow'] / data['total'] * 100) if data['total'] > 0 else 0

            attr_list.append({

                'Developer': name,

                'Tickets': data['total'],

                'QA Flow': f"{data['qaFlow']} ({qa_pct:.0f}%)",

                'Authored': data['authored'],

                'Reviewed': data['reviewed'],

                'Role': 'Delivery' if data['total'] >= 20 else 'Reviews' if data['reviewed'] >= 10 else 'Support'

            })
 
    df_attr = pd.DataFrame(sorted(attr_list, key=lambda x: x['Tickets'], reverse=True))

    st.dataframe(df_attr, use_container_width=True, hide_index=True)
 
    st.divider()
 
    # Tickets vs PRs comparison

    col1, col2 = st.columns(2)
 
    with col1:

        dev_names = [n for n in ATTRIBUTION_DATA.keys() if ATTRIBUTION_DATA[n]['total'] > 0]

        dev_tickets = [ATTRIBUTION_DATA[n]['total'] for n in dev_names]
 
        fig = go.Figure(data=[go.Bar(

            y=dev_names,

            x=dev_tickets,

            orientation='h',

            marker_color='#4f46e5'

        )])

        fig.update_layout(

            title="Tickets Closed (Top Developers)",

            xaxis_title="Count",

            height=350,

            margin=dict(l=150)

        )

        st.plotly_chart(fig, use_container_width=True)
 
    with col2:

        author_names = [n for n in ATTRIBUTION_DATA.keys() if ATTRIBUTION_DATA[n]['authored'] > 0]

        author_prs = [ATTRIBUTION_DATA[n]['authored'] for n in author_names]
 
        fig = go.Figure(data=[go.Bar(

            y=author_names,

            x=author_prs,

            orientation='h',

            marker_color='#10b981'

        )])

        fig.update_layout(

            title="PRs Authored (Top Developers)",

            xaxis_title="Count",

            height=350,

            margin=dict(l=150)

        )

        st.plotly_chart(fig, use_container_width=True)
 
# ═══════════════════════════════════════════════════════════════════════════

# FOOTER

# ═══════════════════════════════════════════════════════════════════════════

st.divider()

st.markdown("""
<div style="text-align:center; color:#718096; font-size:0.85rem; margin-top:20px;">

    Data refreshed: 31/03/2026 · Clockify API · Azure DevOps API
</div>

""", unsafe_allow_html=True)
 
 

