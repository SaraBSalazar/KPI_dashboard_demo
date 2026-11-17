"""Mtime-keyed st.cache_data wrappers around kpi_data's file readers.

Streamlit reruns the whole page script on every widget interaction, and kpi_data reads the
Excel/CSV files fresh each call -- correct, but it makes every click pay the full file-read
cost (the Add Data page alone re-opens every period workbook six times for its dropdowns).
These wrappers cache each reader keyed on the source file's modification time (`mtime_key`),
so:

  - repeated reruns with unchanged files hit the cache (fast), and
  - any change to a file -- a dashboard save, or editing it directly in Excel -- bumps the
    mtime, which changes the cache key, which transparently reloads. The "edit a file and
    just interact with any control to see the update" behavior is preserved.

Note: parameters named with a leading underscore (like `_periods`) are deliberately
EXCLUDED from the cache key by st.cache_data -- the mtime_key params must NOT start with
an underscore or the cache would never invalidate.

kpi_data itself deliberately stays streamlit-free (the snapshot exporter imports it
headless); only this module and the pages know about st.cache_data.
"""

from pathlib import Path

import streamlit as st

import kpi_data as kd


def _mtime(path):
    try:
        return Path(path).stat().st_mtime
    except OSError:
        return 0.0


def _period_files_key():
    return tuple(sorted((str(f), _mtime(f)) for f in kd.DATA_DIR.glob("KPI*.xlsx")))


@st.cache_data(show_spinner=False)
def _load_timelog(dark, mtime_key):
    return kd.load_timelog(dark=dark)


def load_timelog(dark=False):
    return _load_timelog(dark, _mtime(kd.TIMELOG_PATH))


@st.cache_data(show_spinner=False)
def _discover_periods(mtime_key):
    return kd.discover_periods()


def discover_periods():
    return _discover_periods(_period_files_key())


@st.cache_data(show_spinner=False)
def _load_projects(xlsx_path, sheet_name, mtime_key):
    return kd.load_projects(xlsx_path, sheet_name)


def load_projects(xlsx_path, sheet_name):
    return _load_projects(str(xlsx_path), sheet_name, _mtime(xlsx_path))


@st.cache_data(show_spinner=False)
def _load_meetings(xlsx_path, meetings_sheet, mtime_key):
    return kd.load_meetings(xlsx_path, meetings_sheet)


def load_meetings(xlsx_path, meetings_sheet):
    return _load_meetings(str(xlsx_path), meetings_sheet, _mtime(xlsx_path))


@st.cache_data(show_spinner=False)
def _load_goals(mtime_key):
    return kd.load_goals()


def load_goals():
    return _load_goals(_mtime(kd.GOALS_PATH))


@st.cache_data(show_spinner=False)
def _load_tools(mtime_key):
    return kd.load_tools()


def load_tools():
    return _load_tools(_mtime(kd.TOOLS_PATH))


@st.cache_data(show_spinner=False)
def _load_project_tasks(mtime_key):
    return kd.load_project_tasks()


def load_project_tasks():
    """Cached task checklists. The file lives in a OneDrive-synced folder, where a read can
    block while OneDrive uploads the copy an edit just produced -- so re-reading it several
    times per rerun (and on every rerun that didn't change it) is what made the page stall.
    st.cache_data hands back a copy, so callers can still mutate what they get."""
    return _load_project_tasks(_mtime(kd.TASKS_PATH))


@st.cache_data(show_spinner=False)
def _field_options(col, _periods, mtime_key):
    return kd.project_field_options(_periods, col)


def project_field_options(periods, col):
    return _field_options(col, periods, _period_files_key())


@st.cache_data(show_spinner=False)
def _meeting_field_options(col, _periods, mtime_key):
    return kd.meeting_field_options(_periods, col)


def meeting_field_options(periods, col):
    return _meeting_field_options(col, periods, _period_files_key())
