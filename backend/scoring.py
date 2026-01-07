import pandas as pd
import numpy as np
import json

df = pd.read_csv("raw_data.csv")

df["execution"] = np.log1p(df["additions"] + df["deletions"]) + df["files_changed"]
df["impact"] = df["files_changed"] * 0.7
df["visibility"] = df["comments"] + df["reviews"] * 2

scores = df.groupby("author").sum().reset_index()

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

out = scores.to_dict(orient="records")

with open("scores.json", "w") as f:
    json.dump(out, f, indent=2)

print("Saved scores.json")
