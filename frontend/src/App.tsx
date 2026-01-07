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
   Styles
======================= */

const theme = {
  bg: "#0f172a",
  card: "#111827",
  text: "#e5e7eb",
  muted: "#94a3b8",
  primary: "#6366f1",
  danger: "#ef4444",
  border: "#1f2937",
  ai: "#1e1b4b"
};

const card = {
  background: theme.card,
  borderRadius: 14,
  boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
  padding: 20,
  border: `1px solid ${theme.border}`
};

const button = {
  padding: "10px 16px",
  borderRadius: 10,
  border: "none",
  background: theme.primary,
  color: "#fff",
  fontWeight: 600,
  cursor: "pointer"
};

/* =======================
   App
======================= */

export default function App() {
  const [data, setData] = useState<Person[]>([]);
  const [selected, setSelected] = useState<Person | null>(null);
  const [user, setUser] = useState<any | null>(getUser());

  useEffect(() => {
    fetch("http://10.12.80.125:8000/scores")
      .then(res => res.json())
      .then(json => {
        const arr = Array.isArray(json) ? json : json.scores;
        setData(
          arr.map((p: any) => ({
            author: p.author || "Unknown",
            execution: p.execution,
            impact: p.impact ?? 0,
            visibility: p.visibility ?? 0,
            total: p.total,
            percentile: p.percentile,
            silent_architect: !!p.silent_architect,
            improvement_suggestions: p.improvement_suggestions,
            evidence: Array.isArray(p.evidence) ? p.evidence : []
          }))
        );
      });
  }, []);

  function handleLogout() {
    logout();
    setUser(null);
  }

  if (!user) return <AuthPage onLogin={() => setUser(getUser())} />;

  return (
    <div style={{
      minHeight: "100vh",
      background: theme.bg,
      padding: 24,
      color: theme.text,
      fontFamily: "Inter, system-ui, sans-serif"
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 24
      }}>
        <div>
          <h1 style={{ margin: 0 }}>ThirdEye</h1>
          <p style={{ color: theme.muted }}>
            Engineering Impact vs Visibility
          </p>
        </div>

        <div>
          <span style={{ marginRight: 16, color: theme.muted }}>
            <b style={{ color: theme.text }}>{user.username}</b> · {getRole()}
          </span>
          <button style={button} onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 24 }}>
        {/* Chart */}
        <div style={{ ...card, flex: 1 }}>
          <p style={{ color: theme.muted }}>
            🔴 High impact, low visibility = Silent Architects
          </p>

          <ScatterChart
            width={720}
            height={480}
            margin={{ top: 20, right: 30, bottom: 60, left: 60 }}
          >
            <CartesianGrid stroke={theme.border} strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="visibility"
              domain={[0, "dataMax + 10"]}
              tick={{ fill: theme.muted }}
              axisLine={{ stroke: theme.border }}
              label={{
                value: "Visibility (Reviews + Comments)",
                position: "bottom",
                offset: 30,
                fill: theme.muted
              }}
            />
            <YAxis
              type="number"
              dataKey="impact"
              domain={[0, "dataMax + 10"]}
              tick={{ fill: theme.muted }}
              axisLine={{ stroke: theme.border }}
              label={{
                value: "Engineering Impact",
                angle: -90,
                position: "left",
                offset: 40,
                fill: theme.muted
              }}
            />
            <Tooltip
              contentStyle={{
                background: theme.card,
                border: `1px solid ${theme.border}`,
                borderRadius: 8,
                color: theme.text
              }}
            />
            <Scatter
              data={data.filter(d => !d.silent_architect)}
              fill={theme.primary}
              onClick={(d) => setSelected(d as Person)}
            />
            <Scatter
              data={data.filter(d => d.silent_architect)}
              fill={theme.danger}
              onClick={(d) => setSelected(d as Person)}
            />
          </ScatterChart>
        </div>

        {/* Side Panel */}
        {selected && (
          <div style={{ ...card, width: 400 }}>
            <h2 style={{ marginTop: 0 }}>{selected.author}</h2>

            {selected.silent_architect && (
              <span style={{
                display: "inline-block",
                background: "#3f1d1d",
                color: theme.danger,
                padding: "4px 12px",
                borderRadius: 999,
                fontSize: 13,
                fontWeight: 600
              }}>
                Silent Architect
              </span>
            )}

            <div style={{ marginTop: 16 }}>
              <p><b>Impact:</b> {selected.impact.toFixed(1)}</p>
              <p><b>Visibility:</b> {selected.visibility.toFixed(1)}</p>
              {selected.percentile !== undefined && (
                <p><b>Team Percentile:</b> {selected.percentile.toFixed(0)}%</p>
              )}
            </div>

            <hr style={{ borderColor: theme.border }} />

            <h3>Evidence</h3>
            {(selected.evidence || []).slice(0, 4).map((e, i) => (
              <div key={i} style={{
                background: "#020617",
                padding: 12,
                borderRadius: 10,
                marginBottom: 8,
                fontSize: 14,
                border: `1px solid ${theme.border}`
              }}>
                🧩 {e.files_changed} files · +{e.additions} / -{e.deletions}<br />
                💬 {e.reviews} reviews · {e.comments} comments
              </div>
            ))}

            <hr style={{ borderColor: theme.border }} />

            <h3>AI Coaching</h3>
            {selected.improvement_suggestions ? (
              <div style={{
                background: theme.ai,
                padding: 14,
                borderRadius: 10,
                whiteSpace: "pre-line",
                fontSize: 14,
                border: `1px solid ${theme.primary}`
              }}>
                {selected.improvement_suggestions}
              </div>
            ) : (
              <p style={{ color: theme.muted }}>
                No AI suggestions available.
              </p>
            )}

            <button
              style={{ ...button, marginTop: 16, width: "100%" }}
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
