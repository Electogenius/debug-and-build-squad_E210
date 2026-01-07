import pandas as pd
import numpy as np
import psycopg
import os
import google.generativeai as genai

# -----------------------
# Gemini setup
# -----------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def generate_suggestion(row, team_stats):
    prompt = f"""
You are an engineering manager coach.

Contributor metrics:
- Execution: {row.execution:.2f}
- Impact: {row.impact:.2f}
- Visibility: {row.visibility:.2f}
- Percentile: {row.percentile:.1f}
- Silent Architect: {row.silent_architect}

Team medians:
- Impact median: {team_stats['impact_median']:.2f}
- Visibility median: {team_stats['visibility_median']:.2f}

Give 2–3 concise, actionable improvement suggestions.
Be constructive and practical.
Do NOT mention rankings explicitly.
"""
    response = model.generate_content(prompt)
    return response.text.strip()


# -----------------------
# Read data
# -----------------------
df = pd.read_csv("raw_data.csv")

# -----------------------
# Compute metrics
# -----------------------
df["execution"] = np.log1p(df["additions"] + df["deletions"]) + df["files_changed"]
df["impact"] = df["files_changed"] * 0.7
df["visibility"] = df["comments"] + df["reviews"] * 2

scores = df.groupby("author", as_index=False).sum()

scores["total"] = (
    0.5 * scores["execution"] +
    0.4 * scores["impact"] +
    0.1 * scores["visibility"]
)

scores["percentile"] = scores["total"].rank(pct=True) * 100

impact_75 = scores["impact"].quantile(0.75)
vis_40 = scores["visibility"].quantile(0.4)

scores["silent_architect"] = (
    (scores["impact"] >= impact_75) &
    (scores["visibility"] <= vis_40)
)

# -----------------------
# Team context for Gemini
# -----------------------
team_stats = {
    "impact_median": scores["impact"].median(),
    "visibility_median": scores["visibility"].median()
}

# -----------------------
# Database config
# -----------------------
conn_info = {
    "host": "localhost",
    "port": 5432,
    "dbname": "thirdeye",
    "user": "admin",
    "password": "admin"
}

create_table_sql = """
CREATE TABLE IF NOT EXISTS scores (
  author TEXT PRIMARY KEY,
  execution DOUBLE PRECISION,
  impact DOUBLE PRECISION,
  visibility DOUBLE PRECISION,
  total DOUBLE PRECISION,
  percentile DOUBLE PRECISION,
  silent_architect BOOLEAN,
  improvement_suggestions TEXT
);
"""

upsert_sql = """
INSERT INTO scores (
  author, execution, impact, visibility,
  total, percentile, silent_architect, improvement_suggestions
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (author) DO UPDATE SET
  execution = EXCLUDED.execution,
  impact = EXCLUDED.impact,
  visibility = EXCLUDED.visibility,
  total = EXCLUDED.total,
  percentile = EXCLUDED.percentile,
  silent_architect = EXCLUDED.silent_architect,
  improvement_suggestions = EXCLUDED.improvement_suggestions;
"""

# -----------------------
# Write to DB with Gemini output
# -----------------------
with psycopg.connect(**conn_info) as conn:
    with conn.cursor() as cur:
        cur.execute(create_table_sql)

        for _, row in scores.iterrows():
            suggestion = generate_suggestion(row, team_stats)

            cur.execute(
                upsert_sql,
                (
                    row["author"],
                    float(row["execution"]),
                    float(row["impact"]),
                    float(row["visibility"]),
                    float(row["total"]),
                    float(row["percentile"]),
                    bool(row["silent_architect"]),
                    suggestion
                )
            )

print("Saved scores + AI improvement suggestions to PostgreSQL")
