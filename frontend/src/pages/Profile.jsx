import { useState, useEffect } from 'react';
import TopShell from '../layout/TopShell';
import { BACKEND_URL } from '../config';
import './Profile.css';

export default function Profile() {
  const [authStatus, setAuthStatus] = useState(null);

  useEffect(() => {
    fetch(`${BACKEND_URL}/auth/google/status`, { credentials: 'include' })
      .then((r) => r.json())
      .then(setAuthStatus)
      .catch(() => setAuthStatus({ authenticated: false, user: null }));
  }, []);

  const handleConnect = () => {
    window.location.href = `${BACKEND_URL}/auth/google/login`;
  };

  const isAuthed = authStatus?.authenticated;
  const user = authStatus?.user;

  return (
    <TopShell>
      <div className="dash-header">
        <div className="mono-tag">profile</div>
        <h1>Your account.</h1>
        <p className="dash-sub">Connection status for the tools Shundo acts through on your behalf.</p>
      </div>

      <div className="profile-card">
        {user?.picture ? (
          <img src={user.picture} alt="" className="profile-avatar-img" />
        ) : (
          <div className="profile-avatar">{isAuthed ? (user?.name?.[0] || 'U') : 'G'}</div>
        )}
        <div>
          <div className="profile-name">{isAuthed ? (user?.name || user?.email || 'Signed in') : 'Guest session'}</div>
          <div className="profile-sub">{isAuthed ? user?.email : 'not connected — using guest mode'}</div>
        </div>
      </div>

      <div className="connection-list">
        <div className="connection-row">
          <div>
            <div className="connection-name">Google Calendar</div>
            <div className="connection-desc">read + write real events, used by the reflection loop</div>
          </div>
          {isAuthed ? (
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
          {isAuthed ? (
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
