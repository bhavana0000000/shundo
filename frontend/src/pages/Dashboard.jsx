import TopShell from '../layout/TopShell';
import { useAgentWebSocket } from '../hooks/useAgentWebSocket';
import TracePanel from '../components/TracePanel';
import GoalInput from '../components/GoalInput';
import ResultsSummary from '../components/ResultsSummary';
import './Dashboard.css';

export default function Dashboard() {
  const { trace, status, result, error, runGoal, reset } = useAgentWebSocket();

  return (
    <TopShell>
      <div className="dash-top">
        <div className="dash-header">
          <div className="mono-tag">dashboard</div>
          <h1>Give it a goal.</h1>
          <p className="dash-sub">
            Shundo decides which tools to use, calls them for real, and checks its own work before it's done.
          </p>
          <GoalInput onSubmit={runGoal} status={status} />
          {error && <div className="dash-error">{error}</div>}
          {status !== 'idle' && (
            <button className="btn btn-ghost dash-reset" onClick={reset}>$ reset</button>
          )}
        </div>

        <div className="dash-trace">
          <TracePanel trace={trace} status={status} />
        </div>
      </div>

      {result && (
        <div className="dash-results-full">
          <div className="result-card">
            <div className="mono-tag">critic summary</div>
            <p>{result.critic_summary}</p>
          </div>
          <ResultsSummary result={result} />
        </div>
      )}
    </TopShell>
  );
}
