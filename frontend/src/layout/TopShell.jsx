import { NavLink, useNavigate } from 'react-router-dom';
import PetalShower from '../components/PetalShower';
import PaintTrail from '../components/PaintTrail';
import './TopShell.css';

const NAV_ITEMS = [
  { to: '/app', label: 'dashboard', end: true },
  { to: '/app/calendar', label: 'calendar' },
  { to: '/app/tasks', label: 'tasks' },
  { to: '/app/budget', label: 'budget' },
  { to: '/app/profile', label: 'profile' },
];

export default function TopShell({ children }) {
  const navigate = useNavigate();

  return (
    <div className="top-shell">
      <div className="glow-backdrop"></div>
      <PaintTrail />
      <PetalShower />

      <nav className="top-bar">
        <div className="top-logo" onClick={() => navigate('/')}>
          <div className="logo-mark"></div>
          SHUNDO
        </div>

        <div className="top-pill-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `pill-link ${isActive ? 'active' : ''}`}
            >
              {item.label}
            </NavLink>
          ))}
        </div>

        <div className="top-status">
          <span className="pulse-dot"></span>
          idle
        </div>
      </nav>

      <main className="top-shell-main">
        <div className="top-shell-inner">{children}</div>
      </main>
    </div>
  );
}
