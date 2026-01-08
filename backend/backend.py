# backend.py
import pandas as pd
import numpy as np
import psycopg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn
import psycopg

app = FastAPI()

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL connection info
conn_info = {
    "host": "localhost",
    "port": 5432,
    "dbname": "thirdeye",
    "user": "admin",
    "password": "admin"
}

# -----------------------
# Load & process CSV
# -----------------------
import numpy as np
import pandas as pd
from weight_config import *

def calculate_scores(team: str = None):
    df = pd.read_csv("raw_data.csv")  # author, files_changed, additions, deletions, reviews, comments

    if team:
        df = df[df["author"].isin(team.split(","))]

    # --- PR metrics ---
    # code_leverage = log1p(additions + deletions) * log1p(files_changed)
    df["code_leverage"] = np.log1p(df["additions"] + df["deletions"]) * np.log1p(df["files_changed"])

    # review influence
    df["review_influence"] = df["reviews"] * REVIEW_INFLUENCE_MULTIPLIER

    # impact_pr = weighted sum of code_leverage and review_influence
    df["impact_pr"] = (
        IMPACT_PR_WEIGHT_CODE_LEVERAGE * df["code_leverage"] +
        IMPACT_PR_WEIGHT_REVIEW_INFLUENCE * df["review_influence"]
    )

    # visibility_pr = reviews + 0.5 * comments (weights pulled out)
    df["visibility_pr"] = (
        VISIBILITY_PR_WEIGHT_REVIEW * df["review_influence"] +
        VISIBILITY_PR_WEIGHT_COMMENTS * df["comments"]
    )

    # --- Slack metrics ---
    df["decision_proxy"] = (df["reviews"] >= REVIEWS_DECISION_PROXY_THRESHOLD).astype(int)
    df["unblock_proxy"] = (
        (df["files_changed"] <= UNBLOCK_FILES_CHANGED_MAX) &
        (df["deletions"] > df["additions"])
    ).astype(int)
    df["ownership_proxy"] = (df["files_changed"] >= OWNERSHIP_FILES_CHANGED_THRESHOLD).astype(int)

    df["impact_slack"] = (
        IMPACT_SLACK_WEIGHT_UNBLOCK * df["unblock_proxy"] +
        IMPACT_SLACK_WEIGHT_OWNERSHIP * df["ownership_proxy"]
    )
    df["visibility_slack"] = (
        VISIBILITY_SLACK_WEIGHT_DECISION * df["decision_proxy"] +
        VISIBILITY_SLACK_WEIGHT_COMMENTS * df["comments"]
    )

    # --- Aggregate per author ---
    scores = df.groupby("author", as_index=False).agg({
        "impact_pr": "sum",
        "visibility_pr": "sum",
        "impact_slack": "sum",
        "visibility_slack": "sum",
        "files_changed": "sum",
        "additions": "sum",
        "deletions": "sum",
        "reviews": "sum",
        "comments": "sum"
    })

    # --- Combined metrics ---
    scores["impact_combined"] = scores["impact_pr"] + scores["impact_slack"]
    scores["visibility_combined"] = scores["visibility_pr"] + scores["visibility_slack"]

    # --- Execution / total / percentile ---
    scores["execution"] = np.log1p(scores["additions"] + scores["deletions"]) + scores["files_changed"]

    scores["total"] = (
        TOTAL_WEIGHT_EXECUTION * scores["execution"] +
        TOTAL_WEIGHT_IMPACT_COMBINED * scores["impact_combined"] +
        TOTAL_WEIGHT_VISIBILITY_COMBINED * scores["visibility_combined"]
    )

    scores["percentile"] = scores["total"].rank(pct=True) * PERCENTILE_SCALE

    # --- Silent architect ---
    impact_75 = scores["impact_combined"].quantile(SILENT_ARCHITECT_IMPACT_QUANTILE)
    vis_40 = scores["visibility_combined"].quantile(SILENT_ARCHITECT_VISIBILITY_QUANTILE)
    scores["silent_architect"] = (
        (scores["impact_combined"] >= impact_75) &
        (scores["visibility_combined"] <= vis_40)
    )

    impact_50 = scores["impact_combined"].quantile(LOUD_EXECUTOR_IMPACT_QUANTILE)
    vis_75 = scores["visibility_combined"].quantile(LOUD_EXECUTOR_VISIBILITY_QUANTILE)
    scores["loud_executor"] = (
        (scores["impact_combined"] <= impact_50) &
        (scores["visibility_combined"] >= vis_75)
    )

    # --- Improvement suggestions ---
    def simple_suggestion(row):
        suggestions = []
        if row["impact_combined"] < scores["impact_combined"].median():
            suggestions.append("Prioritize high-leverage tasks.")
        if row["visibility_combined"] < scores["visibility_combined"].median():
            suggestions.append("Increase reviews and comments to boost visibility.")
        if row["execution"] < scores["execution"].median():
            suggestions.append("Focus on completing impactful code changes.")
        if not suggestions:
            suggestions.append("Maintain current balanced performance.")
        return " • ".join(suggestions)

    scores["improvement_suggestions"] = scores.apply(simple_suggestion, axis=1)
    return scores


# -----------------------
# Write to PostgreSQL
# -----------------------
def write_to_db(scores):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS scores (
        author TEXT PRIMARY KEY,
        execution DOUBLE PRECISION,
        impact_pr DOUBLE PRECISION,
        visibility_pr DOUBLE PRECISION,
        impact_slack DOUBLE PRECISION,
        visibility_slack DOUBLE PRECISION,
        impact_combined DOUBLE PRECISION,
        visibility_combined DOUBLE PRECISION,
        total DOUBLE PRECISION,
        percentile DOUBLE PRECISION,
        silent_architect BOOLEAN,
        improvement_suggestions TEXT,
        loud_executor BOOLEAN
    );
    """
    upsert_sql = """
    INSERT INTO scores (
        author, execution, impact_pr, visibility_pr,
        impact_slack, visibility_slack, impact_combined, visibility_combined,
        total, percentile, silent_architect, improvement_suggestions, loud_executor
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (author) DO UPDATE SET
        execution = EXCLUDED.execution,
        impact_pr = EXCLUDED.impact_pr,
        visibility_pr = EXCLUDED.visibility_pr,
        impact_slack = EXCLUDED.impact_slack,
        visibility_slack = EXCLUDED.visibility_slack,
        impact_combined = EXCLUDED.impact_combined,
        visibility_combined = EXCLUDED.visibility_combined,
        total = EXCLUDED.total,
        percentile = EXCLUDED.percentile,
        silent_architect = EXCLUDED.silent_architect,
        improvement_suggestions = EXCLUDED.improvement_suggestions;
    """
    with psycopg.connect(**conn_info) as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_sql)
            for _, row in scores.iterrows():
                cur.execute(
                    upsert_sql,
                    (
                        row["author"],
                        float(row["execution"]),
                        float(row["impact_pr"]),
                        float(row["visibility_pr"]),
                        float(row["impact_slack"]),
                        float(row["visibility_slack"]),
                        float(row["impact_combined"]),
                        float(row["visibility_combined"]),
                        float(row["total"]),
                        float(row["percentile"]),
                        bool(row["silent_architect"]),
                        row["improvement_suggestions"],
                        bool(row["loud_executor"])
                    )
                )

def get_team(team_lead):
    if not team_lead:
        return None
    SQL = "SELECT members FROM teams WHERE team_lead = %s;"
    with psycopg.connect(**conn_info) as conn:
        with conn.cursor() as cur:
            cur.execute(SQL, (team_lead,))
            row = cur.fetchone()
            if not row:
                return ""
            members_text = row[0]  # single column
    # split on commas, strip whitespace, filter out empty strings
    return members_text

# -----------------------
# API endpoint
# -----------------------
@app.get("/scores")
def get_scores(team_lead = None):
    scores = calculate_scores(get_team(team_lead))
    write_to_db(scores)
    # Convert to list of dicts for JSON
    return scores.to_dict(orient="records")

def average_team_scores(team_lead: str):
    # Get member list string from DB and compute scores for those members
    members_text = get_team(team_lead)
    if not members_text:
        return []

    # members_text is expected as comma-separated names; reuse calculate_scores by passing team string
    scores = calculate_scores(members_text)
    if scores.empty:
        return []

    # Numeric columns to average (keep same keys as scores table)
    avg_row = {}

    # For boolean and text fields we will pick aggregated sensible defaults:
    # - For boolean flags (silent_architect, loud_executor) use any() -> True if any member has it.
    # - For improvement_suggestions concatenate unique suggestions separated by " • ".
    numeric_cols = [
        "execution", "impact_pr", "visibility_pr", "impact_slack", "visibility_slack",
        "impact_combined", "visibility_combined", "total", "percentile",
        "files_changed", "additions", "deletions", "reviews", "comments"
    ]

    # Some of these numeric cols may not exist in the aggregated scores frame (files_changed etc. were dropped earlier).
    for c in numeric_cols:
        if c in scores.columns:
            if c in 'files_changed additions deletions reviews comments'.split():
                avg_row[c] = float(scores[c].sum())
            else:
                avg_row[c] = float(scores[c].mean())
        else:
            # skip missing columns
            pass

    # Booleans
    for b in ["silent_architect", "loud_executor"]:
        if b in scores.columns:
            avg_row[b] = bool(scores[b].any())

    # For author, use team_lead as identifier or "team:{lead}"
    avg_row["author"] = f"team:{team_lead}"

    # improvement_suggestions: unique concatenation
    # if "improvement_suggestions" in scores.columns:
    #     uniques = [s for s in scores["improvement_suggestions"].unique() if s and isinstance(s, str)]
    #     avg_row["improvement_suggestions"] = " • ".join(uniques) if uniques else ""

    # Ensure all keys expected by DB/table are present (set defaults when missing)
    expected_keys = [
        "author", "execution", "impact_pr", "visibility_pr",
        "impact_slack", "visibility_slack", "impact_combined", "visibility_combined",
        "total", "percentile", "silent_architect", "improvement_suggestions", "loud_executor"
    ]
    for k in expected_keys:
        if k not in avg_row:
            # sensible defaults
            if k in ["silent_architect", "loud_executor"]:
                avg_row[k] = False
            elif k == "author":
                avg_row[k] = f"team:{team_lead}"
            elif k == "improvement_suggestions":
                avg_row[k] = ""
            else:
                avg_row[k] = 0.0

    # Return as list with single dict to match scores.to_dict(orient="records")
    return [avg_row]


@app.get("/team_average")
def get_team_average(team_lead: str = None):
    if not team_lead:
        return []

    avg = average_team_scores(team_lead)
    return avg


def list_team_leads():
    """Return a list of team_lead names from the teams table."""
    SQL = "SELECT DISTINCT team_lead FROM teams;"
    leads = []
    with psycopg.connect(**conn_info) as conn:
        with conn.cursor() as cur:
            cur.execute(SQL)
            rows = cur.fetchall()
            if rows:
                leads = [r[0] for r in rows if r[0] is not None]
    return leads

@app.get("/team_leads")
def get_team_leads():
    return list_team_leads()


# -----------------------
# Run server
# -----------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
