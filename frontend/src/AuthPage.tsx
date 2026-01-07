import React, { useState } from "react";
import { login, Role } from "./auth";

type Props = {
  onLogin: () => void;
};

export default function AuthPage({ onLogin }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("team_leader");
  const [error, setError] = useState<string | null>(null);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim()) {
      setError("Please enter a username");
      return;
    }
    if (!password) {
      setError("Please enter a password");
      return;
    }
    login(username.trim(), role, password);
    onLogin();
  }

  return (
    <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
      <form onSubmit={submit} style={{ width: 360, border: "1px solid #ddd", padding: 20, borderRadius: 8 }}>
        <h2>Sign In</h2>
        <div style={{ marginBottom: 10 }}>
          <label>Username</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{ width: "100%", padding: 8, marginTop: 6 }}
          />
        </div>

        <div style={{ marginBottom: 10 }}>
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: "100%", padding: 8, marginTop: 6 }}
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <label>Role</label>
          <div style={{ marginTop: 6 }}>
            <label style={{ marginRight: 12 }}>
              <input type="radio" checked={role === "manager"} onChange={() => setRole("manager")} /> Manager
            </label>
            <label>
              <input type="radio" checked={role === "team_leader"} onChange={() => setRole("team_leader")} /> Team Leader
            </label>
          </div>
        </div>

        {error && <div style={{ color: "red", marginBottom: 10 }}>{error}</div>}

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <button type="submit" style={{ padding: "8px 12px" }}>
            Sign in
          </button>
        </div>
      </form>
    </div>
  );
}
