import pandas as pd
import numpy as np
import psycopg

# read data
df = pd.read_csv("raw_data.csv")

# compute metrics
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

# prepare DB connection parameters
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
  silent_architect BOOLEAN
);
"""

# Upsert statement (Postgres ON CONFLICT)
upsert_sql = """
INSERT INTO scores (author, execution, impact, visibility, total, percentile, silent_architect)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (author) DO UPDATE SET
  execution = EXCLUDED.execution,
  impact = EXCLUDED.impact,
  visibility = EXCLUDED.visibility,
  total = EXCLUDED.total,
  percentile = EXCLUDED.percentile,
  silent_architect = EXCLUDED.silent_architect;
"""

# write to DB
with psycopg.connect(**conn_info) as conn:
    with conn.cursor() as cur:
        cur.execute(create_table_sql)
        # insert rows
        for _, row in scores.iterrows():
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
                )
            )

print("Saved scores to PostgreSQL table 'scores'")
