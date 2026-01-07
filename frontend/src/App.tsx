import React, { useEffect, useState } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from "recharts";
import AuthPage from "./AuthPage";
import { getUser, logout, getRole } from "./auth";

type Evidence = {
  files_changed: number;
  additions: number;
  deletions: number;
  reviews: number;
  comments: number;
};

type Person = {
  author: string;
  impact: number;
  visibility: number;
  silent_architect: boolean;
  pr_count: number;
  evidence: Evidence[];
};

export default function App() {
  const [data, setData] = useState<Person[]>([]);
  const [selected, setSelected] = useState<Person | null>(null);
  const [user, setUser] = useState<any | null>(getUser());

  useEffect(() => {
    fetch("http://10.12.80.125:8000/scores")
      .then(res => res.json())
      .then(json => {
        // Ensure data is an array
        const arr = Array.isArray(json) ? json : json.scores;
        // Normalize each person: ensure evidence and pr_count exist
        const normalized: Person[] = arr.map((person: any) => ({
          author: person.author || "Unknown",
          impact: person.impact || 0,
          visibility: person.visibility || 0,
          silent_architect: person.silent_architect || false,
          pr_count: person.pr_count || 0,
          evidence: Array.isArray(person.evidence) ? person.evidence : []
        }));
        setData(normalized);
      })
      .catch(err => console.error("Fetch error:", err));
  }, []);

  function handleLogout() {
    logout();
    setUser(null);
  }

  if (!user) {
    return <AuthPage onLogin={() => setUser(getUser())} />;
  }

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h1>ThirdEye — Impact vs Visibility</h1>
        <div>
          <span style={{ marginRight: 12 }}>Signed in as <b>{user.username}</b> ({getRole()})</span>
          <button onClick={handleLogout}>Sign out</button>
        </div>
      </div>
      <div style={{ display: "flex", padding: 10 }}>
        {/* Chart */}
        <div>
          <p>🔴 Red dots = Silent Architects</p>

          <ScatterChart
            width={700}
            height={500}
            margin={{ top: 20, right: 30, bottom: 60, left: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis
              type="number"
              dataKey="visibility"
              name="Visibility"
              label={{
                value: "Visibility (Reviews + Comments)",
                position: "bottom",
                offset: 30
              }}
              domain={[0, "dataMax + 10"]}
            />

            <YAxis
              type="number"
              dataKey="impact"
              name="Impact"
              label={{
                value: "Engineering Impact",
                angle: -90,
                position: "left",
                offset: 40
              }}
              domain={[0, "dataMax + 10"]}
            />

            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              formatter={(value, name) => [
                typeof value === "number" ? value.toFixed(1) : value,
                name
              ]}
              labelFormatter={() => "Contributor"}
            />

            <Scatter
              data={data.filter(d => !d.silent_architect)}
              fill="#8884d8"
              onClick={(d) => setSelected(d as Person)}
            />

            <Scatter
              data={data.filter(d => d.silent_architect)}
              fill="red"
              onClick={(d) => setSelected(d as Person)}
            />
          </ScatterChart>
        </div>

        {/* Evidence Panel */}
        {selected && (
          <div style={{
            marginLeft: 30,
            padding: 20,
            width: 350,
            border: "1px solid #ccc",
            borderRadius: 8
          }}>
            <h2>{selected.author}</h2>

            {selected.silent_architect && (
              <p style={{ color: "red", fontWeight: "bold" }}>
                Silent Architect 🧠
              </p>
            )}

            <p><b>PRs:</b> {selected.pr_count}</p>
            <p><b>Impact:</b> {selected.impact.toFixed(1)}</p>
            <p><b>Visibility:</b> {selected.visibility.toFixed(1)}</p>

            <hr />

            <h3>Evidence</h3>

            {(selected.evidence || []).slice(0, 5).map((e, i) => (
              <div key={i} style={{ marginBottom: 10 }}>
                <p>
                  🧩 Files: {e.files_changed} <br />
                  ➕ +{e.additions} / ➖ -{e.deletions} <br />
                  💬 Reviews: {e.reviews}, Comments: {e.comments}
                </p>
              </div>
            ))}

            <button onClick={() => setSelected(null)}>
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
