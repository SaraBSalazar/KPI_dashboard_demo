"""Generate every fake data file this demo dashboard needs, under Data/.

Everything here is INVENTED: project tags, group names, dates, hours, ratings, tools --
nothing is copied or derived from any real KPI tracker. Shapes (columns, sheet names,
JSON structure) match what Dashboard/kpi_data.py actually reads, so the dashboard opens
with a full year of realistic-looking activity rather than an empty or broken state.

Covers the most recently completed calendar year relative to TODAY below (edit TODAY to
regenerate a different "current" year). Re-run any time to get a fresh random year:

    python generate_demo_data.py

Deliberately does NOT reuse any real project-tag naming (no DNA_/STAT_/CONSULT_-style
codes) -- the fake tags below use different prefixes on purpose, so nothing here can be
mistaken for a real project.
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

import openpyxl
import pandas as pd

random.seed(20250101)  # fixed seed -> reproducible demo data across re-runs

TODAY = date(2026, 11, 17)
YEAR = TODAY.year - 1  # most recently completed calendar year -> 2025
DATA_DIR = Path(__file__).resolve().parent / "Data"
DATA_DIR.mkdir(exist_ok=True)

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

# --- Vocabulary: same categories/major tasks as the real tracker, so the charts and the
# glossary stay meaningful; project tags, groups and people are all invented. -------------
CATEGORIES = ["Projects", "Projects-Development", "Meetings (non-project)", "ADAorg", "Trainning"]
MAJOR_TASKS = ["code", "Tools", "AI Skills", "Internal org", "Internal Meeting", "External Meeting",
               "Meetings/Comms", "ProjectOrg", "Plan/Study", "Burocracy", "Seminar", "Report",
               "Review", "Article Revision", "Trainning"]
USER_TYPES = ["Internal-ADA", "External Research Group", "Facility", "Internal Research Group"]
USER_LOCATIONS = ["Oeiras", "Lisbon", "Coimbra", "Porto"]
PROJECT_TRIGGERS = ["Internal", "Follow-up", "User-Requested", "Proactive Proposal",
                    "Inherited Project", "Outreach-Driven", "Consulting"]
TYPES_OF_DATA = ["MultiOMICS", "Lipidomics", "Metabolomics", "Proteomics", "Transcriptomics", "Other"]
PROJECT_OUTPUTS = ["Pipeline", "Dashboard", "Report", "Figures", "AI Skill", "Consulting note"]
GROUPS = ["Genomics Unit", "Cell Signalling Lab", "Structural Biology Group", "Clinical Research Core",
          "Immunology Facility", "Plant Sciences Group", "Microbiome Lab", "Imaging Facility"]

# Fake project tags: a few different invented naming styles so the gallery doesn't look
# like one template -- underscore-coded (common in the real tracker), and a couple of
# "XX - description" style tags.
FAKE_PROJECT_TAGS = [
    "GEN_014", "GEN_021", "PROT_005", "PROT_011", "LIP_003", "META_008", "META_012",
    "SEQ_019", "SEQ_022", "IMG_006", "IMG_015", "STRUCT_002", "MICR_009",
    "XX - general consulting", "YY - general support", "ZZ - general outreach",
    "CRC_030", "CRC_031", "PLNT_004", "IMMU_017",
]

SHORT_DESCRIPTIONS = {
    "GEN_014": "Variant calling pipeline for a non-model organism.",
    "GEN_021": "RNA-seq differential expression re-analysis.",
    "PROT_005": "Mass-spec proteomics QC and normalization.",
    "PROT_011": "Interaction network from co-IP proteomics.",
    "LIP_003": "Lipidomics profiling across treatment groups.",
    "META_008": "Metabolomics pathway enrichment report.",
    "META_012": "Targeted metabolomics panel, dose-response.",
    "SEQ_019": "Long-read assembly QC for a draft genome.",
    "SEQ_022": "Amplicon sequencing taxonomic classification.",
    "IMG_006": "Image-analysis pipeline for high-content screening.",
    "IMG_015": "Cell segmentation and feature extraction.",
    "STRUCT_002": "Structural model comparison across conditions.",
    "MICR_009": "Microbiome diversity analysis, 16S.",
    "XX - general consulting": "Ad-hoc statistics consulting, no single deliverable.",
    "YY - general support": "Recurring light support across several small requests.",
    "ZZ - general outreach": "Outreach session, no project deliverable attached.",
    "CRC_030": "Clinical cohort summary statistics.",
    "CRC_031": "Survival analysis for a clinical follow-up study.",
    "PLNT_004": "Transcriptomics in a stress-response time course.",
    "IMMU_017": "Flow cytometry panel analysis and figures.",
}

NON_QUANT_OUTPUTS = [
    "", "Presented at group meeting.", "Shared internal how-to guide.",
    "Informal feedback only, no written report.", "Used to shape a later grant application.",
]


def _rand_date(start: date, end: date):
    span = (end - start).days
    return start + timedelta(days=random.randint(0, max(span, 0)))


def _fmt(d):
    return pd.Timestamp(d) if d else None


# --- 1) Project tracker: Data/KPI_<year>.xlsx, sheets "<year>_CALENDAR" + "_meetings" ----
def build_project_tracker():
    year_start, year_end = date(YEAR, 1, 1), date(YEAR, 12, 31)
    rows = []
    for tag in FAKE_PROJECT_TAGS:
        trigger = random.choice(PROJECT_TRIGGERS)
        first_contact = _rand_date(year_start, year_end - timedelta(days=30))
        register = first_contact + timedelta(days=random.randint(0, 10))
        begin = register + timedelta(days=random.randint(0, 21))
        # ~75% of projects are finished within the year; the rest are still running
        finished = random.random() < 0.75
        report_sent = begin + timedelta(days=random.randint(7, 90)) if finished else None
        if report_sent and report_sent > year_end:
            report_sent = None
            finished = False
        # a few finished projects still lack a Closing Day (exercises "needs attention")
        closing = (report_sent + timedelta(days=random.randint(0, 5))
                   if finished and random.random() < 0.8 else None)
        if closing and closing > year_end:
            closing = None
        if trigger == "Inherited Project":
            # inherited work is attributed to when she/they actually picked it up, which can
            # sit a little after the (older) registration date
            begin = register + timedelta(days=random.randint(10, 40))

        rows.append({
            "Project tag": tag,
            "Short Description": SHORT_DESCRIPTIONS.get(tag, ""),
            "User Type": random.choice(USER_TYPES),
            "User Location": random.choice(USER_LOCATIONS),
            "Grupo": random.choice(GROUPS),
            "User": f"User {chr(65 + FAKE_PROJECT_TAGS.index(tag) % 20)}.",
            "Project Outputs": random.choice(PROJECT_OUTPUTS),
            "Type of Data": random.choice(TYPES_OF_DATA),
            "Project Trigger": trigger,
            "First User Meeting/Shared Data": _fmt(first_contact),
            "Register Project": _fmt(register),
            "Begining": _fmt(begin),
            "Lead Time: Request to Project Start": "",
            "Final Report Sent": _fmt(report_sent),
            "Closing Day": _fmt(closing),
            "Hours in Agendo": round(random.uniform(2, 70), 1),
            "Number of Reports": random.randint(0, 3),
            "Number of Meetings": random.randint(0, 6),
            "Price Charged": random.choice([0, 0, 0, 150, 300, 450, 600]),
            "Non-quantifiable outputs": random.choice(NON_QUANT_OUTPUTS),
            "Notas": "",
        })

    projects = pd.DataFrame(rows)

    meetings_rows = []
    for _ in range(14):
        tag = random.choice(FAKE_PROJECT_TAGS)
        meetings_rows.append({
            "Project tag": tag,
            "User Type": random.choice(USER_TYPES),
            "Date": _fmt(_rand_date(year_start, year_end)),
            "User Location": random.choice(USER_LOCATIONS),
            "Grupo": random.choice(GROUPS),
            "User": f"User {chr(65 + FAKE_PROJECT_TAGS.index(tag) % 20)}.",
            "Meeting Outputs": random.choice(
                ["Scope agreed.", "Data shared.", "Results discussed.", "Follow-up planned."]),
            "Time": round(random.uniform(0.5, 2.0), 1),
        })
    meetings = pd.DataFrame(meetings_rows)

    path = DATA_DIR / f"KPI_{YEAR}.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as xl:
        projects.to_excel(xl, sheet_name=f"{YEAR}_CALENDAR", index=False)
        meetings.to_excel(xl, sheet_name=f"{YEAR}_CALENDAR_meetings", index=False)
    print(f"wrote {path} ({len(projects)} projects, {len(meetings)} meetings)")
    return projects


# --- 2) Personal time log: Data/track_time.csv -------------------------------------------
NON_PROJECT_MAJOR_TASKS = {
    "Meetings (non-project)": ["Internal Meeting", "External Meeting"],
    "ADAorg": ["Internal org", "Burocracy", "Seminar"],
    "Trainning": ["Trainning"],
}
PROJECT_MAJOR_TASKS = ["code", "Meetings/Comms", "ProjectOrg", "Report", "Review", "Plan/Study"]


def _week_label(d):
    """('January', '1st January') for the Monday `d` -- the ordinal matches
    kpi_data.week_bounds's own Monday-of-the-month numbering, and only the leading
    digit of the returned label is ever parsed back out of it."""
    month_name = MONTHS[d.month - 1]
    month_start = date(d.year, d.month, 1)
    first_monday_offset = (7 - month_start.weekday()) % 7
    first_monday = month_start + timedelta(days=first_monday_offset)
    ordinal = (d - first_monday).days // 7 + 1 if d >= first_monday else 1
    suffix = "st" if ordinal == 1 else "nd" if ordinal == 2 else "rd" if ordinal == 3 else "th"
    return month_name, f"{ordinal}{suffix} {month_name}"


def build_time_log(projects):
    """Mostly-continuous weekly logging per project across its own Begining -> report/
    today window (an occasional genuine pause, not one scattered into almost every week),
    plus non-project categories spread evenly across the year. Generating hours
    independently-per-week regardless of each project's own active window -- the first
    version of this script did that -- produces a "paused" gap nearly everywhere once fed
    through kpi_data.lead_time_table's gap detector, which doesn't resemble a real time
    log at all."""
    year_start, year_end = date(YEAR, 1, 1), date(YEAR, 12, 31)
    today = date.today()
    rows = []
    entry_id = 1

    def add_entry(monday, category, major_task, tag, hrs, mins):
        nonlocal entry_id
        month_name, week_label = _week_label(monday)
        rows.append({
            "Entry": f"DEMO_{entry_id:03d}", "Agendo updated": random.choice(["Yes", "Yes", "Yes", "No"]),
            "Category": category, "Hours (exact)": hrs + mins / 60, "Major task name (chart)": major_task,
            "Hrs": hrs, "Min": mins, "Month": month_name, "Month and year (chart)": f"{month_name} {YEAR}",
            "Notes": "", "Week": week_label, "Weekly entry name (chart)": tag, "Year": YEAR,
            "Unnamed: 13": "",
        })
        entry_id += 1

    project_windows = {}  # tag -> (begin_d, end_d), reused below to keep dev-side entries
                           # from landing on a project before it's even begun

    for _, p in projects.iterrows():
        begin = p["Begining"]
        if pd.isna(begin):
            continue
        begin_d = begin.date()
        end_raw = p["Final Report Sent"] if pd.notna(p["Final Report Sent"]) else p["Closing Day"]
        end_d = end_raw.date() if pd.notna(end_raw) else min(today, year_end)
        end_d = min(max(end_d, begin_d), year_end)
        project_windows[p["Project tag"]] = (begin_d, end_d)

        monday = begin_d - timedelta(days=begin_d.weekday())
        weeks = []
        while monday <= end_d:
            weeks.append(monday)
            monday += timedelta(days=7)
        if not weeks:
            continue

        # One genuine pause for a minority of long-enough projects -- a real 2-3 week
        # stretch with nothing logged, strictly inside the span -- rather than a gap
        # showing up almost everywhere.
        pause = set()
        if len(weeks) > 6 and random.random() < 0.25:
            pause_len = min(random.randint(2, 3), len(weeks) - 5)
            start_idx = random.randint(2, len(weeks) - pause_len - 2)
            pause = set(range(start_idx, start_idx + pause_len))

        for i, wk in enumerate(weeks):
            if i in pause:
                continue
            if random.random() < 0.05:  # a rare single skipped week -- low enough that two in a
                                         # row (which would itself read as a second "pause") stays rare
                continue
            for _ in range(random.randint(1, 2)):
                hrs, mins = random.choice([1, 2, 2, 3, 4]), random.choice([0, 0, 15, 30])
                add_entry(wk, "Projects", random.choice(PROJECT_MAJOR_TASKS), p["Project tag"], hrs, mins)

    # A handful of Projects-Development entries (tool-building side work). Still tagged to
    # a project tag (so it counts as that project's hours), but only to one already in its
    # active window that week -- an entry logged before a project has even begun, or long
    # after it closed, would read as its own multi-month "pause" either side of it.
    monday = year_start - timedelta(days=year_start.weekday())
    while monday <= year_end:
        active_tags = [t for t, (b, e) in project_windows.items() if b <= monday <= e]
        if active_tags and random.random() < 0.15:
            tag = random.choice(active_tags)
            hrs, mins = random.choice([1, 2, 3, 4]), random.choice([0, 0, 30])
            add_entry(monday, "Projects-Development", random.choice(["Tools", "AI Skills"]), tag, hrs, mins)
        monday += timedelta(days=7)

    # Non-project categories: internal org, non-project meetings, training -- spread
    # fairly evenly across the whole year, independent of any project's lifecycle.
    monday = year_start - timedelta(days=year_start.weekday())
    while monday <= year_end:
        for _ in range(random.randint(1, 3)):
            category = random.choices(list(NON_PROJECT_MAJOR_TASKS), weights=[50, 35, 15])[0]
            major_task = random.choice(NON_PROJECT_MAJOR_TASKS[category])
            hrs, mins = random.choice([0, 1, 1, 2]), random.choice([0, 0, 30])
            add_entry(monday, category, major_task, category, hrs, mins)
        monday += timedelta(days=7)

    df = pd.DataFrame(rows)
    path = DATA_DIR / "track_time.csv"
    df.to_csv(path, sep=";", index=False, encoding="utf-8-sig")
    print(f"wrote {path} ({len(df)} rows across {YEAR})")


# --- 3) Special projects: ratings + task checklists ---------------------------------------
SPECIAL_PROJECTS = [
    ("01 - Reach more research groups", "Shared Pipeline", "Reusable multi-omics pipeline open to any group.",
     "Easy to demo, clear visibility gain.", "Needs a stable place to be hosted.",
     "Could absorb more data types over time.", 2, 3, 1, 4),
    ("01 - Reach more research groups", "Hands-on Workshop", "Recurring workshop on common analysis patterns.",
     "Cheap to run, good word-of-mouth.", "", "Materials can be reused across editions.", 1, 4, 1, 5),
    ("02 - Reduce turnaround time", "Request Triage Tool", "Lightweight intake form that pre-sorts new requests.",
     "Cuts back-and-forth at project start.", "Only helps the intake step, not delivery.",
     "Could auto-suggest the right Project Trigger.", 2, 3, 2, 2),
    ("02 - Reduce turnaround time", "Template Library", "Standard report/figure templates per data type.",
     "Saves repeat setup work on similar projects.", "Templates drift if not kept up to date.",
     "Versioned templates with a changelog.", 1, 3, 2, 2),
    ("03 - Build internal tooling", "OmicsXplorer", "Internal explorer for QC'd multi-omics datasets.",
     "Centralizes what's otherwise scattered notebooks.", "Needs ongoing maintenance as formats change.",
     "Could plug into the pipeline's output directly.", 3, 4, 3, 3),
    ("03 - Build internal tooling", "Snippet Library", "Curated, reusable code snippets for common tasks.",
     "Low effort, immediate reuse value.", "Only useful if people actually contribute back.",
     "Could become a small internal package.", 1, 2, 2, 1),
]


def build_special_projects():
    cols = ["Goal", "Project", "Description", "Advantages", "Limitations", "Future gain",
            "Development", "Impact", "Maintenance", "Visibility"]
    df = pd.DataFrame(SPECIAL_PROJECTS, columns=cols)
    path = DATA_DIR / "Special_Projects_Ratings.xlsx"
    df.to_excel(path, sheet_name="Special Projects Ratings", index=False)
    print(f"wrote {path} ({len(df)} goal/project rows)")

    tasks = {}
    for _, project, *_ in SPECIAL_PROJECTS:
        n_tasks = random.randint(2, 4)
        cursor = date(YEAR, random.randint(1, 6), 1)
        task_list = []
        for i in range(n_tasks):
            start = cursor
            due = start + timedelta(days=random.randint(20, 45))
            task_list.append({
                "id": f"{random.getrandbits(32):08x}",
                "text": f"{project}: milestone {i + 1}",
                "level": 0,
                "done": i == 0,  # first milestone already done, the rest pending
                "start": start.isoformat(),
                "due": due.isoformat(),
            })
            cursor = due + timedelta(days=1)
        tasks[project] = task_list

    tasks_json_path = DATA_DIR / "special_project_tasks.json"
    tasks_json_path.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    print(f"wrote {tasks_json_path}")

    with pd.ExcelWriter(DATA_DIR / "Special_Projects_Tasks.xlsx", engine="openpyxl") as xl:
        for project, task_list in tasks.items():
            pd.DataFrame(task_list).to_excel(xl, sheet_name=project[:31], index=False)
    print(f"wrote {DATA_DIR / 'Special_Projects_Tasks.xlsx'}")


# --- 4) Beyond-projects cards ----------------------------------------------------------------
def build_beyond_projects():
    period_label = f"{YEAR}"
    cards = [
        {"title": "Guest lecture · Summer School", "value": "~16 h in total", "color": "#0B3C49",
         "description": "16 h bioinformatics module for visiting students."},
        {"title": "Pipeline outreach", "value": "2", "color": "#2A9D8F",
         "description": "Pipeline showcased at 2 seminars · opened 1 new project."},
        {"title": "Internal tools", "value": "2", "color": "#E76F51",
         "description": "Two small internal helper scripts (personal use)."},
    ]
    data = {period_label: cards}
    path = DATA_DIR / "beyond_projects.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path}")

    rows = [{"Period": period_label, **c} for c in cards]
    pd.DataFrame(rows).to_excel(DATA_DIR / "Beyond_Projects.xlsx", sheet_name="Beyond projects", index=False)
    print(f"wrote {DATA_DIR / 'Beyond_Projects.xlsx'}")


# --- 5) Tools & AI Skills inventory ------------------------------------------------------
TOOLS = [
    ("QC Dashboard", "Adaptation of the internal pipeline into a facility-specific QC dashboard.",
     "Tool Dashboard", f"{YEAR}", "Facility", "User Project", "", "Could absorb more facility-specific checks."),
    ("motif-finder-skill", "Interactive motif finder letting users pick genes and tweak output figures.",
     "AI Skill", f"{YEAR}", "User", "User Project", "Limited sandbox network access.",
     "Faster deployment across more genome builds."),
    ("metadata-normalizer-agent", "Turns user-submitted sample sheets into pipeline-ready standardized tables.",
     "AI Skill", f"{YEAR}", "ADA", "Internal pipeline tool", "Needs tighter dashboard integration.",
     "Cuts manual cleanup on recurring requests."),
    ("Report Builder", "Generates the standard PDF report from a project's tracked outputs.",
     "Internal Tool", f"{YEAR}", "ADA", "Internal pipeline tool", "", "Could template more report types."),
]


def build_tools():
    cols = ["Name", "Description", "Type of tool", "Built in", "Use", "Project Origin",
            "Limitations", "Future gain"]
    df = pd.DataFrame(TOOLS, columns=cols)
    path = DATA_DIR / "tools.xlsx"
    df.to_excel(path, sheet_name="Tools", index=False)
    print(f"wrote {path} ({len(df)} tools)")


# --- 6) Custom tags (dropdown memory) ------------------------------------------------------
def build_custom_tags():
    data = {"projects": [], "categories": [], "major_tasks": []}
    path = DATA_DIR / "custom_tags.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"wrote {path}")


# --- --empty: a blank starting point for real use, not fake content -----------------------
PROJECT_COLS = [
    "Project tag", "Short Description", "User Type", "User Location", "Grupo", "User",
    "Project Outputs", "Type of Data", "Project Trigger", "First User Meeting/Shared Data",
    "Register Project", "Begining", "Lead Time: Request to Project Start", "Final Report Sent",
    "Closing Day", "Hours in Agendo", "Number of Reports", "Number of Meetings", "Price Charged",
    "Non-quantifiable outputs", "Notas",
]
MEETING_COLS = ["Project tag", "User Type", "Date", "User Location", "Grupo", "User",
                "Meeting Outputs", "Time"]
TIMELOG_COLS = ["Entry", "Agendo updated", "Category", "Hours (exact)", "Major task name (chart)",
                 "Hrs", "Min", "Month", "Month and year (chart)", "Notes", "Week",
                 "Weekly entry name (chart)", "Year", "Unnamed: 13"]
GOALS_COLS = ["Goal", "Project", "Description", "Advantages", "Limitations", "Future gain",
              "Development", "Impact", "Maintenance", "Visibility"]
TOOLS_COLS = ["Name", "Description", "Type of tool", "Built in", "Use", "Project Origin",
              "Limitations", "Future gain"]


def build_empty(year=None):
    """Write every file Dashboard/kpi_data.py needs, with the right columns/sheets but
    ZERO rows of content -- a real starting point instead of fake placeholder activity.
    Some files (the two JSON task/beyond-projects files and their Excel mirrors) have no
    safe "empty but present" state worth writing, since kpi_data.py already creates them
    correctly (empty, or via a small generic seed) the first time it finds them missing --
    see README.md's "Starting fresh with your own data" for exactly which is which."""
    year = year or date.today().year
    print(f"Writing an EMPTY starting point for calendar year {year} (no fake content)...\n")

    path = DATA_DIR / f"KPI_{year}.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as xl:
        pd.DataFrame(columns=PROJECT_COLS).to_excel(xl, sheet_name=f"{year}_CALENDAR", index=False)
        pd.DataFrame(columns=MEETING_COLS).to_excel(xl, sheet_name=f"{year}_CALENDAR_meetings", index=False)
    print(f"wrote {path} (0 projects, 0 meetings)")

    tl_path = DATA_DIR / "track_time.csv"
    pd.DataFrame(columns=TIMELOG_COLS).to_csv(tl_path, sep=";", index=False, encoding="utf-8-sig")
    print(f"wrote {tl_path} (0 rows)")

    pd.DataFrame(columns=GOALS_COLS).to_excel(
        DATA_DIR / "Special_Projects_Ratings.xlsx", sheet_name="Special Projects Ratings", index=False)
    print(f"wrote {DATA_DIR / 'Special_Projects_Ratings.xlsx'} (0 rows)")

    pd.DataFrame(columns=TOOLS_COLS).to_excel(DATA_DIR / "tools.xlsx", sheet_name="Tools", index=False)
    print(f"wrote {DATA_DIR / 'tools.xlsx'} (0 rows)")

    build_custom_tags()  # already writes an empty {"projects": [], ...} unconditionally

    for stray in ("special_project_tasks.json", "Special_Projects_Tasks.xlsx",
                  "beyond_projects.json", "Beyond_Projects.xlsx", "KPI_2025.xlsx"):
        p = DATA_DIR / stray
        if p.exists():
            p.unlink()
            print(f"removed {p} (the app recreates the JSON ones correctly on first use)")

    print(f"\nDone. Data/ is now a blank {year} starting point -- open the dashboard and use "
          "Add Data to fill it in, or edit the Excel/CSV files directly.")


if __name__ == "__main__":
    import sys
    if "--empty" in sys.argv:
        build_empty()
    else:
        projects = build_project_tracker()
        build_time_log(projects)
        build_special_projects()
        build_beyond_projects()
        build_tools()
        build_custom_tags()
        print(f"\nDone. Demo data covers calendar year {YEAR}.")
