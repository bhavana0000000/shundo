import { useState, useEffect } from 'react';
import './LoadingScreen.css';

export default function LoadingScreen({ onDone }) {
  const [progress, setProgress] = useState(0);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((p) => {
        if (p >= 100) {
          clearInterval(interval);
          setTimeout(() => setExiting(true), 300);
          setTimeout(() => onDone(), 950);
          return 100;
        }
        const jump = p < 70 ? Math.random() * 9 + 3 : Math.random() * 3 + 1;
        return Math.min(100, p + jump);
      });
    }, 90);
    return () => clearInterval(interval);
  }, [onDone]);

  return (
    <div className={`loading-screen ${exiting ? 'exiting' : ''}`}>
      <div className="loading-inner">
        <div className="loading-shun">shun</div>
        <div className="loading-bar-track">
          <div className="loading-bar-fill" style={{ width: `${progress}%` }}></div>
        </div>
        <div className="loading-footer">
          <span className="loading-label">initializing agent runtime</span>
          <span className="loading-count">{String(Math.floor(progress)).padStart(2, '0')}%</span>
        </div>
      </div>
    </div>
  );
}
