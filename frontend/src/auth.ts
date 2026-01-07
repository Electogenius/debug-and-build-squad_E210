export type Role = "manager" | "team_leader";

export type User = {
  username: string;
  role: Role;
  pwd?: string; // base64-encoded password (mock only)
};

const STORAGE_KEY = "t3_auth_user";

export function login(username: string, role: Role, password?: string) {
  const user: User = {
    username,
    role,
    pwd: password ? btoa(password) : undefined
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  return user;
}

export function logout() {
  localStorage.removeItem(STORAGE_KEY);
}

export function getUser(): User | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function isAuthenticated() {
  return getUser() !== null;
}

export function getRole(): Role | null {
  const u = getUser();
  return u ? u.role : null;
}
