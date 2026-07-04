// Central place for backend URLs. Falls back to localhost for local dev.
// For production builds, set VITE_BACKEND_URL / VITE_WS_URL in
// frontend/.env.production before running `npm run build`.

export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws/agent/dynamic';
