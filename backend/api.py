from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg
import os

app = FastAPI()

# Allow React frontend to fetch
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hackathon use only
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB connection info from env (set PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE)
# or rely on individual env vars and psycopg will pick them up

@app.get("/scores")
def get_scores():
    # Query Postgres and return list of dicts (FastAPI will JSON-serialize)
    query = "SELECT * FROM scores"

    # Use a short-lived connection per request (safe for simple apps)
    conn_info = {
		"host": "localhost",
		"port": 5432,
		"dbname": "thirdeye",
		"user": "admin",
		"password": "admin"
	}
    conn = psycopg.connect(**conn_info)

    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(query)
            rows = cur.fetchall()  # list of dict-like Row objects
            # Convert rows to plain dicts (Row respects mapping but convert explicitly)
            result = [dict(r) for r in rows]
    finally:
        conn.close()

    return result
