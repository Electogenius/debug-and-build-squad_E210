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

/* =======================
   Types
======================= */

type Evidence = {
  files_changed: number;
  additions: number;
  deletions: number;
  reviews: number;
  comments: number;
};

type Person = {
  author: string;
  execution?: number;
  impact: number;
  visibility: number;
  total?: number;
  percentile?: number;
  silent_architect: boolean;
  improvement_suggestions?: string;
  evidence: Evidence[];
};

/* =======================
   App
======================= */

export default function App() {
  const [data, setData] = useState<Person[]>([]);
  const [selected, setSelected] = useState<Person | null>(null);
  const [user, setUser] = useState<any | null>(getUser());

  /* =======================
     Fetch data
  ======================= */

  useEffect(() => {
    fetch("http://10.12.80.125:8000/scores")
      .then(res => res.json())
      .then(json => {
        const arr = Array.isArray(json) ? json : json.scores;

        const normalized: Person[] = arr.map((p: any) => ({
          author: p.author || "Unknown",
          execution: p.execution,
          impact: p.impact ?? 0,
          visibility: p.visibility ?? 0,
          total: p.total,
          percentile: p.percentile,
          silent_architect: !!p.silent_architect,
          improvement_suggestions: p.improvement_suggestions,
          evidence: Array.isArray(p.evidence) ? p.evidence : []
        }));

        setData(normalized);
      })
      .catch(err => console.error("Fetch error:", err));
  }, []);

  /* =======================
     Auth
  ======================= */

  function handleLogout() {
    logout();
    setUser(null);
  }

  if (!user) {
    return <AuthPage onLogin={() => setUser(getUser())} />;
  }

  /* =======================
     Render
  ======================= */

  return (
    <div style={{ padding: 20 }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12
        }}
      >
        <h1>ThirdEye — Impact vs Visibility</h1>

        <div>
          <span style={{ marginRight: 12 }}>
            Signed in as <b>{user.username}</b> ({getRole()})
          </span>
          <button onClick={handleLogout}>Sign out</button>
        </div>
      </div>

      <div style={{ display: "flex", padding: 10 }}>
        {/* =======================
           Chart
        ======================= */}
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

        {/* =======================
           Side Panel
        ======================= */}
        {selected && (
          <div
            style={{
              marginLeft: 30,
              padding: 20,
              width: 360,
              border: "1px solid #ccc",
              borderRadius: 8
            }}
          >
            <h2>{selected.author}</h2>

            {selected.silent_architect && (
              <p style={{ color: "red", fontWeight: "bold" }}>
                Silent Architect 🧠
              </p>
            )}

            <p><b>Impact:</b> {selected.impact.toFixed(1)}</p>
            <p><b>Visibility:</b> {selected.visibility.toFixed(1)}</p>

            {selected.percentile !== undefined && (
              <p>
                <b>Team Percentile:</b> {selected.percentile.toFixed(0)}%
              </p>
            )}

            <hr />

            {/* Evidence */}
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

            <hr />

            {/* Gemini AI Coaching */}
            <h3>AI Coaching</h3>

            {selected.improvement_suggestions ? (
              <p style={{ whiteSpace: "pre-line" }}>
                {selected.improvement_suggestions}
              </p>
            ) : (
              <p style={{ color: "#777" }}>
                No AI suggestions available.
              </p>
            )}

            <button
              style={{ marginTop: 10 }}
              onClick={() => setSelected(null)}
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
