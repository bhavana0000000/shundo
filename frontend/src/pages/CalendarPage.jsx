import { useState, useEffect } from 'react';
import TopShell from '../layout/TopShell';
import './CalendarPage.css';

const BACKEND_URL = 'http://localhost:8001';

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' }) +
    ' · ' + d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

export default function CalendarPage() {
  const [events, setEvents] = useState([]);
  const [authenticated, setAuthenticated] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/calendar`)
      .then((r) => r.json())
      .then((data) => {
        setEvents(data.events || []);
        setAuthenticated(data.authenticated);
      })
      .catch(() => setAuthenticated(false))
      .finally(() => setLoading(false));
  }, []);

  return (
    <TopShell>
      <div className="dash-header">
        <div className="mono-tag">calendar</div>
        <h1>What's actually on your calendar.</h1>
        <p className="dash-sub">Real events, read live from Google Calendar — this is what the critic checks against.</p>
      </div>

      {!authenticated && (
        <div className="cal-warning">
          Not connected to Google yet. <a href={`${BACKEND_URL}/auth/google/login`}>Connect your calendar →</a>
        </div>
      )}

      <div className="event-list">
        {loading && <div className="event-empty">loading...</div>}
        {!loading && authenticated && events.length === 0 && (
          <div className="event-empty">nothing on your calendar for the next 30 days.</div>
        )}
        {events.map((e) => (
          <div className="event-row" key={e.id}>
            <div className="event-dot"></div>
            <div className="event-info">
              <div className="event-title">{e.title}</div>
              <div className="event-time">{formatDate(e.start)} → {formatDate(e.end)}</div>
            </div>
          </div>
        ))}
      </div>
    </TopShell>
  );
}
