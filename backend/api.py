from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# Allow React frontend to fetch
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hackathon use only
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to scores.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCORES_FILE = os.path.join(BASE_DIR, "scores.json")

@app.get("/scores")
def get_scores():
    # Load JSON and return Python list (FastAPI serializes automatically)
    with open(SCORES_FILE) as f:
        scores = json.load(f)
    return scores
