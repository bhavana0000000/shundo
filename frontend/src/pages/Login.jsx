import { useNavigate } from 'react-router-dom';
import PetalShower from '../components/PetalShower';
import './Login.css';

const BACKEND_URL = 'http://localhost:8001';

export default function Login() {
  const navigate = useNavigate();

  const handleGoogleLogin = () => {
    window.location.href = `${BACKEND_URL}/auth/google/login`;
  };

  return (
    <div className="login-page">
      <PetalShower />
      <div className="login-card">
        <div className="login-logo" onClick={() => navigate('/')}>
          <div className="logo-mark"></div>
          SHUNDO
        </div>

        <h1>Sign in to <span className="shun-word">act</span>.</h1>
        <p className="login-sub">
          Shundo needs real access to your calendar and inbox to actually
          do things on your behalf — not just talk about them.
        </p>

        <button className="btn btn-fill google-btn" onClick={handleGoogleLogin}>
          <svg width="18" height="18" viewBox="0 0 18 18">
            <path fill="#050505" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 01-1.8 2.72v2.26h2.9c1.7-1.56 2.7-3.86 2.7-6.62z"/>
            <path fill="#050505" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.9-2.26c-.8.54-1.84.86-3.06.86-2.35 0-4.34-1.59-5.05-3.72H.94v2.33A9 9 0 009 18z"/>
            <path fill="#050505" d="M3.95 10.7A5.4 5.4 0 013.68 9c0-.59.1-1.17.27-1.7V4.97H.94A9 9 0 000 9c0 1.45.35 2.83.94 4.03l3.01-2.33z"/>
            <path fill="#050505" d="M9 3.58c1.32 0 2.51.45 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 00.94 4.97L3.95 7.3C4.66 5.17 6.65 3.58 9 3.58z"/>
          </svg>
          Continue with Google
        </button>

        <button className="btn btn-ghost guest-btn" onClick={() => navigate('/app')}>
          continue as guest — demo mode
        </button>

        <p className="login-footnote">
          Guest mode skips real calendar/email actions but the rest of the agent runs exactly the same.
        </p>
      </div>
    </div>
  );
}
