import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LoadingScreen from './components/LoadingScreen';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import BudgetTracker from './pages/BudgetTracker';
import CalendarPage from './pages/CalendarPage';
import TasksPage from './pages/TasksPage';
import Profile from './pages/Profile';
import DocumentUpload from './pages/DocumentUpload';
import './tokens.css';

export default function App() {
  const [loading, setLoading] = useState(true);

  if (loading) {
    return <LoadingScreen onDone={() => setLoading(false)} />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/app" element={<Dashboard />} />
        <Route path="/app/calendar" element={<CalendarPage />} />
        <Route path="/app/tasks" element={<TasksPage />} />
        <Route path="/app/budget" element={<BudgetTracker />} />
        <Route path="/app/profile" element={<Profile />} />
        <Route path="/app/upload" element={<DocumentUpload />} />
      </Routes>
    </BrowserRouter>
  );
}
