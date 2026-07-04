import { useState, useEffect } from 'react';
import TopShell from '../layout/TopShell';
import { BACKEND_URL } from '../config';
import './BudgetTracker.css';

export default function BudgetTracker() {
  const [expenses, setExpenses] = useState([]);
  const [total, setTotal] = useState({ total: 0, currency: 'INR' });
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ category: '', amount: '', description: '' });
  const [submitting, setSubmitting] = useState(false);

  const fetchBudget = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/budget`);
      const data = await res.json();
      setExpenses(data.expenses || []);
      setTotal(data.total || { total: 0, currency: 'INR' });
    } catch (e) {
      console.error('Failed to load budget', e);
    }
    setLoading(false);
  };

  useEffect(() => { fetchBudget(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.category || !form.amount) return;
    setSubmitting(true);
    try {
      await fetch(`${BACKEND_URL}/api/budget`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: form.category,
          amount: parseFloat(form.amount),
          description: form.description,
          currency: 'INR',
        }),
      });
      setForm({ category: '', amount: '', description: '' });
      await fetchBudget();
    } catch (e) {
      console.error('Failed to add expense', e);
    }
    setSubmitting(false);
  };

  return (
    <TopShell>
      <div className="dash-header">
        <div className="mono-tag">budget tracker</div>
        <h1>Real spend, tracked automatically.</h1>
        <p className="dash-sub">
          Every expense the agent logs during a trip-planning run shows up here — or add one manually below.
        </p>
      </div>

      <div className="budget-total-card">
        <div className="mono-tag">total spend</div>
        <div className="budget-total-num">₹{total.total?.toLocaleString('en-IN') || 0}</div>
      </div>

      <form className="expense-form" onSubmit={handleSubmit}>
        <input type="text" placeholder="category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
        <input type="number" placeholder="amount" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
        <input type="text" placeholder="description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <button className="btn btn-fill" type="submit" disabled={submitting}>
          {submitting ? 'adding...' : 'add expense'}
        </button>
      </form>

      <div className="expense-table">
        <div className="expense-row expense-head">
          <span>category</span><span>description</span><span>amount</span>
        </div>
        {loading && <div className="expense-empty">loading...</div>}
        {!loading && expenses.length === 0 && <div className="expense-empty">no expenses logged yet.</div>}
        {expenses.map((e) => (
          <div className="expense-row" key={e.id}>
            <span className="expense-cat">{e.category}</span>
            <span className="expense-desc">{e.description || '—'}</span>
            <span className="expense-amt">₹{e.amount.toLocaleString('en-IN')}</span>
          </div>
        ))}
      </div>
    </TopShell>
  );
}
