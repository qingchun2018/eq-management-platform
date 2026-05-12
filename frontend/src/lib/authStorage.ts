// 与后端 JWT 配套的浏览器侧存储工具：access/refresh token 与当前项目 ID
// 设计要点：
//   - 使用 localStorage 持久化，刷新页面不丢失登录态
//   - 集中封装，便于将来切换为 sessionStorage 或安全 cookie
//   - 不在此处做网络/解析，避免与 axios 互相依赖

const ACCESS_TOKEN_KEY = "eq.access_token";
const REFRESH_TOKEN_KEY = "eq.refresh_token";
const PROJECT_ID_KEY = "eq.current_project_id";

function safeStorage(): Storage | null {
  try {
    if (typeof window === "undefined") return null;
    return window.localStorage;
  } catch {
    return null;
  }
}

export function getAccessToken(): string | null {
  return safeStorage()?.getItem(ACCESS_TOKEN_KEY) ?? null;
}

export function getRefreshToken(): string | null {
  return safeStorage()?.getItem(REFRESH_TOKEN_KEY) ?? null;
}

export function setTokens(accessToken: string, refreshToken: string): void {
  const s = safeStorage();
  if (!s) return;
  s.setItem(ACCESS_TOKEN_KEY, accessToken);
  s.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearAllTokens(): void {
  const s = safeStorage();
  if (!s) return;
  s.removeItem(ACCESS_TOKEN_KEY);
  s.removeItem(REFRESH_TOKEN_KEY);
}

export function getStoredProjectId(): number | null {
  const raw = safeStorage()?.getItem(PROJECT_ID_KEY);
  if (raw === null || raw === undefined || raw === "") return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

export function setStoredProjectId(id: number): void {
  safeStorage()?.setItem(PROJECT_ID_KEY, String(id));
}

export function clearStoredProjectId(): void {
  safeStorage()?.removeItem(PROJECT_ID_KEY);
}
