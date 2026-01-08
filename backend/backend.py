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

# -----------------------
# Run server
# -----------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
