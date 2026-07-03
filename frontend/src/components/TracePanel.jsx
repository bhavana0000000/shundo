import './TracePanel.css';

const AGENT_LABELS = { planner: 'planner', executor: 'executor', critic: 'critic' };

function agentClass(agent) {
  if (agent === 'planner') return 'planner';
  if (agent === 'critic') return 'critic';
  return 'executor';
}

function rowClass(entry) {
  const text = JSON.stringify(entry.detail || '').toLowerCase();
  if (text.includes('conflict') || text.includes('error') || text.includes('failed')) return 'warn';
  if (text.includes('confirmed') || text.includes('completed successfully') || text.includes('no conflicts')) return 'ok';
  return '';
}

function summarize(entry) {
  const { action, detail } = entry;
  if (action === 'select_tools' && Array.isArray(detail)) {
    const names = detail.map((d) => d.tool).join(', ');
    return `selecting tools: ${names}`;
  }
  if (action?.startsWith('call_')) {
    const toolName = action.replace('call_', '');
    if (detail && detail.error) return `${toolName}() failed — ${detail.error}`;
    return `${toolName}() → ${Array.isArray(detail) ? detail.length + ' results' : 'ok'}`;
  }
  if (typeof detail === 'string') return detail;
  return action;
}

export default function TracePanel({ trace, status }) {
  const showCursor = status === 'running' || status === 'connecting';

  return (
    <div className="trace-panel">
      <div className="trace-panel-header">
        <span className="tl-dot red"></span>
        <span className="tl-dot yellow"></span>
        <span className="tl-dot green"></span>
        <span className="trace-filename">agent_trace.log</span>
      </div>

      {trace.length === 0 && status === 'idle' && (
        <div className="trace-empty">give it a goal to see the agent think.</div>
      )}
      {trace.length === 0 && status === 'connecting' && (
        <div className="trace-empty">connecting...</div>
      )}

      {trace.map((entry, i) => (
        <div className={`trace-row ${rowClass(entry)}`} key={i}>
          <span className={`trace-agent ${agentClass(entry.agent)}`}>
            {AGENT_LABELS[entry.agent] || entry.agent}
          </span>
          <span className="trace-text">{summarize(entry)}</span>
        </div>
      ))}

      {showCursor && (
        <div className="trace-row cursor-row">
          <span className="cursor-blink">_</span>
        </div>
      )}
    </div>
  );
}
