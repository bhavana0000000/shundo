// Central place for backend URLs and session identity.
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';
export const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws/agent/dynamic';

// Session identity - stored in localStorage instead of relying on cookies,
// since cross-domain cookies (frontend on pages.dev, backend on onrender.com)
// get silently blocked by modern browsers (Safari ITP, Chrome privacy
// protections). This is what was causing sign-in to randomly reset to guest.
const SESSION_KEY = 'shundo_session_id';

export function getSessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

// Use this for every fetch() call to the backend
export function authHeaders(extra = {}) {
  return { 'x-shundo-session': getSessionId(), ...extra };
}

// Use this to build the live WebSocket URL with the session attached
export function getWsUrl() {
  const sep = WS_BASE.includes('?') ? '&' : '?';
  return `${WS_BASE}${sep}session_id=${getSessionId()}`;
}

// Use this to build any full-page-redirect URL (like Google login) with
// the session attached, since redirects can't carry custom headers
export function withSession(url) {
  const sep = url.includes('?') ? '&' : '?';
  return `${url}${sep}session_id=${getSessionId()}`;
}
