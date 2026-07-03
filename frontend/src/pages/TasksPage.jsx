import { useState, useEffect } from 'react';
import TopShell from '../layout/TopShell';
import './TasksPage.css';

const BACKEND_URL = 'http://localhost:8001';

export default function TasksPage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newTask, setNewTask] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks`);
      const data = await res.json();
      setTasks(data.tasks || []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => { fetchTasks(); }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newTask.trim()) return;
    setSubmitting(true);
    try {
      await fetch(`${BACKEND_URL}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTask.trim() }),
      });
      setNewTask('');
      await fetchTasks();
    } catch (e) {
      console.error(e);
    }
    setSubmitting(false);
  };

  const handleComplete = async (id) => {
    await fetch(`${BACKEND_URL}/api/tasks/${id}/complete`, { method: 'POST' });
    fetchTasks();
  };

  return (
    <TopShell>
      <div className="dash-header">
        <div className="mono-tag">tasks</div>
        <h1>What the agent still needs to do.</h1>
        <p className="dash-sub">Reminders logged during a run, or added by you directly.</p>
      </div>

      <form className="task-form" onSubmit={handleAdd}>
        <input
          type="text"
          placeholder="add a task..."
          value={newTask}
          onChange={(e) => setNewTask(e.target.value)}
        />
        <button className="btn btn-fill" type="submit" disabled={submitting}>
          {submitting ? 'adding...' : 'add'}
        </button>
      </form>

      <div className="task-list-page">
        {loading && <div className="task-empty">loading...</div>}
        {!loading && tasks.length === 0 && <div className="task-empty">no tasks yet.</div>}
        {tasks.map((t) => (
          <div className={`task-row-page ${t.completed ? 'done' : ''}`} key={t.id}>
            <button className="task-check" onClick={() => !t.completed && handleComplete(t.id)}>
              {t.completed ? '✓' : ''}
            </button>
            <span className="task-title">{t.title}</span>
            {t.due_date && <span className="task-due">{t.due_date}</span>}
          </div>
        ))}
      </div>
    </TopShell>
  );
}
