import { useState } from 'react';
import './GoalInput.css';

export default function GoalInput({ onSubmit, status }) {
  const [goal, setGoal] = useState('Plan a weekend trip to Goa with flights, a hotel, and weather check');
  const isRunning = status === 'connecting' || status === 'running';

  const handleSubmit = (e) => {
    e.preventDefault();
    if (goal.trim() && !isRunning) onSubmit(goal.trim());
  };

  return (
    <form className="goal-input-block" onSubmit={handleSubmit}>
      <textarea
        className="goal-input"
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        placeholder="Give it a goal..."
        disabled={isRunning}
        rows={3}
      />
      <button type="submit" className="pill-cta goal-submit" disabled={isRunning}>
        <span className="pill-cta-icon">→</span>
        {isRunning ? 'thinking...' : 'run it'}
      </button>
    </form>
  );
}
