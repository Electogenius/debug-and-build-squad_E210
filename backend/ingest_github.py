from github import Github
from github import Auth
import pandas as pd
import os

auth = Auth.Token(os.getenv("GITHUB_TOKEN"))

g = Github(auth=auth)

REPO = "fastapi/fastapi"

repo = g.get_repo(REPO)

rows = []

for pr in repo.get_pulls(state="closed")[:50]:
    if not pr.merged or not pr.user:
        continue

    rows.append({
        "author": pr.user.login,
        "files_changed": pr.changed_files,
        "additions": pr.additions,
        "deletions": pr.deletions,
        "reviews": pr.get_reviews().totalCount,
        "comments": pr.comments
    })

df = pd.DataFrame(rows)
df.to_csv("raw_data.csv", index=False)
print("Saved raw_data.csv")
