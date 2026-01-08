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
  evidence: Evidence;
  loud_executor: boolean;
  all: any;
};

/* =======================
   App
======================= */

export default function App() {
  const [data, setData] = useState<Person[]>([]);
  const [selected, setSelected] = useState<Person | null>(null);
  const [user, setUser] = useState<any | null>(getUser());
  const [filter, setFilter] = useState<"all" | "silent" | "loud">("all");

  // fetch function
  const loadData = (usr: any) => {
    if (!usr) return;
    fetch("http://10.12.80.125:8000/scores?team_lead=" + usr.username)
      .then(res => res.json())
      .then(json => {
        const arr = Array.isArray(json) ? json : json.scores;
        const normalized: Person[] = arr.map((p: any) => ({
          author: p.author || "Unknown",
          execution: p.execution,
          impact: p.impact_combined ?? 0,
          visibility: p.visibility_combined ?? 0,
          total: p.total,
          percentile: p.percentile,
          silent_architect: !!p.silent_architect,
          improvement_suggestions: p.improvement_suggestions,
          evidence: {
            files_changed: p.files_changed,
            additions: p.additions,
            deletions: p.deletions,
            reviews: p.reviews,
            comments: p.comments
          },
          loud_executor: !!p.loud_executor,
          all: p
        }));

        setData(normalized);
      })
      .catch(err => console.error("Fetch error:", err));
  };

  useEffect(() => {
    loadData(user);
  }, [user]); // re-run when user changes

  function handleLogout() {
    logout();
    setUser(null);
  }

  if (!user) {
    // call setUser and reload data after login
    return <AuthPage onLogin={() => {
      const u = getUser();
      setUser(u);
      loadData(u);
    }} />;
  }

  /* =======================
     Styles
  ======================= */

  const darkBg = "#1e1e2f";
  const cardBg = "#2c2c3c";
  const textColor = "#eee";
  const secondaryText = "#aaa";
  const highlightGreen = "#28a745";
  const highlightRed = "#dc3545";
  const primaryBlue = "#007bff";

  /* =======================
     Render
  ======================= */

  document.body.style.margin = '0'

  return (
    <div style={{ padding: 40, background: darkBg, minHeight: "100vh", color: textColor, fontFamily: "sans-serif", boxSizing: 'border-box'}}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20
        }}
      >
        <h1 style={{ margin: 0 }}>ThirdEye — Impact vs Visibility</h1>

        <div>
          <span style={{ marginRight: 12, color: secondaryText }}>
            Signed in as <b>{user.username}</b> ({getRole()})
          </span>
          <button
            onClick={handleLogout}
            style={{
              padding: "6px 12px",
              borderRadius: 6,
              border: "none",
              background: primaryBlue,
              color: "#fff",
              cursor: "pointer"
            }}
          >
            Sign out
          </button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 20 }}>
        {/* =======================
           Chart + Filter
        ======================= */}
        <div style={{ flex: 1 }}>
          {/* Filter Buttons */}
          <div style={{ marginBottom: 12 }}>
            {["all", "silent", "loud"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f as any)}
                style={{
                  marginRight: 8,
                  padding: "6px 14px",
                  borderRadius: 20,
                  border: filter === f ? `2px solid ${primaryBlue}` : "1px solid #555",
                  background: filter === f ? "#3a3a50" : "#2c2c3c",
                  color: textColor,
                  cursor: "pointer"
                }}
              >
                {f === "all" ? "All" : f === "silent" ? "Silent Architects" : "Loud Executors"}
              </button>
            ))}
          </div>

          <p style={{ color: secondaryText }}>🟢 Green dots = Silent Architects</p>
          <p style={{ color: secondaryText }}>🔴 Red dots = Loud Executors</p>

          <ScatterChart
            width={700}
            height={500}
            margin={{ top: 20, right: 30, bottom: 60, left: 60 }}
          >
            <CartesianGrid stroke="#444" strokeDasharray="3 3" />

 <XAxis
  type="number"
  dataKey="visibility"
  name="Visibility"
  tick={{ fill: textColor }}
  tickFormatter={(val) => Math.round(val).toString()}   // integer ticks
  label={{
    value: "Visibility (Reviews + Comments)",
    position: "bottom",
    offset: 30,
    fill: textColor
  }}
  domain={[-2, 2]}   // axis range from -2 to 2
/>

<YAxis
  type="number"
  dataKey="impact"
  name="Impact"
  tick={{ fill: textColor }}
  tickFormatter={(val) => Math.round(val).toString()}   // integer ticks
  label={{
    value: "Engineering Impact",
    angle: -90,
    position: "left",
    offset: 40,
    fill: textColor
  }}
  domain={[-2, 2]}   // axis range from -2 to 2
/>




            <Tooltip
              cursor={{ stroke: "#666", strokeDasharray: "3 3" }}
              contentStyle={{ backgroundColor: "#fff", borderRadius: 6, border: "none", color: textColor }}
              formatter={(value, name) => [
                typeof value === "number" ? value.toFixed(1) : value,
                name
              ]}
              labelFormatter={() => "Contributor"}
            />

            {["all"].includes(filter) && (
              <Scatter
                data={data.filter(d => !d.silent_architect && !d.loud_executor)}
                fill={"#fff"}
                onClick={(d) => setSelected(d as Person)}
              />
            )}

            {["all", "silent"].includes(filter) && (
              <Scatter
                data={data.filter(d => d.silent_architect)}
                fill={highlightGreen}
                onClick={(d) => setSelected(d as Person)}
              />
            )}

            {["all", "loud"].includes(filter) && (
              <Scatter
                data={data.filter(d => d.loud_executor)}
                fill={highlightRed}
                onClick={(d) => setSelected(d as Person)}
              />
            )}
          </ScatterChart>
        </div>

        {/* =======================
           Side Panel
        ======================= */}
        {selected && (
          <div
            style={{
              width: 360,
              background: cardBg,
              padding: 20,
              borderRadius: 12,
              boxShadow: "0 4px 12px rgba(0,0,0,0.4)"
            }}
          >
            <h2 style={{ marginTop: 0 }}>{selected.author}</h2>

            {selected.silent_architect && (
              <p style={{ color: highlightGreen, fontWeight: "bold" }}>
                Silent Architect 🧠
              </p>
            )}

            {selected.loud_executor && (
              <p style={{ color: highlightRed, fontWeight: "bold" }}>
                Loud Executor 🗣️
              </p>
            )}

            <p><b>Impact:</b> {selected.impact.toFixed(1)}</p>
            <p><b>Visibility:</b> {selected.visibility.toFixed(1)}</p>
            <p><b>Total Score:</b> {selected.total}</p>
            <p><b>Percentile:</b> {selected.percentile}%</p>
            <p><b>Slack Impact:</b> {selected.all.impact_slack}</p>
            <p><b>Slack Visibility:</b> {selected.all.visibility_slack}</p>

            {selected.percentile !== undefined && (
              <p>
                <b>Team Percentile:</b> {selected.percentile.toFixed(0)}%
              </p>
            )}

            <hr style={{ borderColor: "#444" }} />

            <h3>Evidence</h3>
            {([selected.evidence]).map((e, i) => (
              <div key={i} style={{ marginBottom: 10 }}>
                <p style={{ color: textColor }}>
                  🧩 Files: {e.files_changed} <br />
                  ➕ +{e.additions} / ➖ -{e.deletions} <br />
                  💬 Reviews: {e.reviews}, Comments: {e.comments} <br />
                </p>
              </div>
            ))}

            <hr style={{ borderColor: "#444" }} />

            <h3>AI Coaching</h3>
            {selected.improvement_suggestions ? (
              <p style={{ whiteSpace: "pre-line", color: textColor }}>
                {selected.improvement_suggestions}
              </p>
            ) : (
              <p style={{ color: secondaryText }}>No AI suggestions available.</p>
            )}

            <button
              style={{
                marginTop: 10,
                padding: "6px 12px",
                borderRadius: 6,
                border: "none",
                background: primaryBlue,
                color: "#fff",
                cursor: "pointer"
              }}
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
