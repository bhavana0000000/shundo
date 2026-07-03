import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Reveal from '../components/Reveal';
import PaintTrail from '../components/PaintTrail';
import './Landing.css';

const CHAPTERS = [
  { num: '01', title: 'It reasons before it acts.', body: 'The planner reads your goal and the full tool registry, then decides what to do — nothing is hardcoded per domain.' },
  { num: '02', title: 'It checks its own work.', body: 'The critic re-reads real data after every action. A scheduling conflict gets caught and fixed automatically — not silently missed.' },
  { num: '03', title: 'It actually does the thing.', body: 'Real Google Calendar writes. Real Gmail drafts. Real flight and hotel data. Not a plan you still have to go execute yourself.' },
];

export default function Landing() {
  const navigate = useNavigate();
  const [mouse, setMouse] = useState({ x: 0.5, y: 0.5 });

  useEffect(() => {
    const handleMove = (e) => {
      setMouse({ x: e.clientX / window.innerWidth, y: e.clientY / window.innerHeight });
    };
    window.addEventListener('mousemove', handleMove);
    return () => window.removeEventListener('mousemove', handleMove);
  }, []);

  return (
    <div className="motion-landing">
      <PaintTrail />
      <div className="grain-overlay"></div>

      <nav className="motion-nav">
        <div className="motion-logo">SHUNDO</div>
        <button className="motion-menu-btn" onClick={() => navigate('/login')}>sign in</button>
      </nav>

      <section className="motion-hero">
        <div className="motion-eyebrow reveal-load">
          planner · executor · critic — a live reflection loop
        </div>

        <div className="motion-title-wrap">
          <span className="title-line reveal-load" style={{ transitionDelay: '80ms' }}>every goal has a</span>
        </div>
        <h1 className="title-script full-bleed reveal-load" style={{ transitionDelay: '220ms' }}>shun</h1>

        <p className="motion-sub reveal-load" style={{ transitionDelay: '420ms' }}>
          the moment it's ready. an autonomous agent that turns a vague
          goal into real, executed actions.
        </p>

        <div className="floating-cta reveal-load" style={{ transitionDelay: '560ms' }}>
          <button className="pill-cta" onClick={() => navigate('/login')}>
            <span className="pill-cta-icon">→</span>
            try it live
          </button>
        </div>

        <div className="motion-scroll-cue"><span>scroll</span></div>
      </section>

      <section className="proof-strip">
        <Reveal><div className="proof-item"><div className="proof-num">11</div><div className="proof-label">real tools, one registry</div></div></Reveal>
        <div className="proof-divider"></div>
        <Reveal delay={100}><div className="proof-item"><div className="proof-num">3</div><div className="proof-label">agents, one reflection loop</div></div></Reveal>
        <div className="proof-divider"></div>
        <Reveal delay={200}><div className="proof-item"><div className="proof-num">0</div><div className="proof-label">hardcoded workflows</div></div></Reveal>
      </section>

      <section className="chapters">
        {CHAPTERS.map((c) => (
          <div className="chapter" key={c.num}>
            <Reveal className="chapter-inner">
              <div className="chapter-num">{c.num}</div>
              <h2>{c.title}</h2>
              <p>{c.body}</p>
            </Reveal>
          </div>
        ))}
      </section>

      <section className="final-cta">
        <Reveal>
          <h2>give it a goal.<br /><span className="title-script inline-script">shundo</span> does the rest.</h2>
          <button className="pill-cta pill-cta-dark" onClick={() => navigate('/login')}>
            <span className="pill-cta-icon">→</span>
            try it live
          </button>
        </Reveal>
      </section>

      <footer className="motion-footer">
        <span>shundo — the moment something is ready.</span>
        <span>built for a hackathon, working on real data.</span>
      </footer>
    </div>
  );
}
