import { useState, useEffect } from 'react';
import TopShell from '../layout/TopShell';
import { BACKEND_URL } from '../config';
import './Profile.css';

export default function Profile() {
  const [authStatus, setAuthStatus] = useState(null);

  useEffect(() => {
    fetch(`${BACKEND_URL}/auth/google/status`)
      .then((r) => r.json())
      .then(setAuthStatus)
      .catch(() => setAuthStatus({ authenticated: false }));
  }, []);

  const handleConnect = () => {
    window.location.href = `${BACKEND_URL}/auth/google/login`;
  };

  return (
    <TopShell>
      <div className="dash-header">
        <div className="mono-tag">profile</div>
        <h1>Your account.</h1>
        <p className="dash-sub">Connection status for the tools Shundo acts through on your behalf.</p>
      </div>

      <div className="profile-card">
        <div className="profile-avatar">S</div>
        <div>
          <div className="profile-name">Guest session</div>
          <div className="profile-sub">connected via demo mode</div>
        </div>
      </div>

      <div className="connection-list">
        <div className="connection-row">
          <div>
            <div className="connection-name">Google Calendar</div>
            <div className="connection-desc">read + write real events, used by the reflection loop</div>
          </div>
          {authStatus?.authenticated ? (
            <span className="connection-badge ok">connected</span>
          ) : (
            <button className="btn btn-ghost connect-btn" onClick={handleConnect}>connect</button>
          )}
        </div>

        <div className="connection-row">
          <div>
            <div className="connection-name">Gmail</div>
            <div className="connection-desc">creates real drafts, never auto-sends</div>
          </div>
          {authStatus?.authenticated ? (
            <span className="connection-badge ok">connected</span>
          ) : (
            <span className="connection-badge">shares Google connection above</span>
          )}
        </div>

        <div className="connection-row">
          <div>
            <div className="connection-name">Web + travel search</div>
            <div className="connection-desc">live flight, hotel, and event data</div>
          </div>
          <span className="connection-badge ok">active</span>
        </div>
      </div>
    </TopShell>
  );
}
