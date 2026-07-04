import { useState, useRef, useCallback } from 'react';
import { WS_URL } from '../config';

export function useAgentWebSocket() {
  const [trace, setTrace] = useState([]);
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  const runGoal = useCallback((goal) => {
    setTrace([]);
    setResult(null);
    setError(null);
    setStatus('connecting');

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('running');
      ws.send(JSON.stringify({ goal }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'step') {
        setTrace((prev) => [...prev, data.entry]);
      } else if (data.type === 'done') {
        const toolCount = data.result?.tool_results?.length || 0;
        setTrace((prev) => [
          ...prev,
          {
            agent: 'system',
            action: 'complete',
            detail: `finished — ${toolCount} tool call${toolCount === 1 ? '' : 's'} completed. results below.`,
          },
        ]);
        setResult(data.result);
        setStatus('done');
      } else if (data.type === 'error') {
        setError(data.message);
        setStatus('error');
      }
    };

    ws.onerror = () => {
      setError('Connection failed.');
      setStatus('error');
    };

    ws.onclose = () => {
      setStatus((s) => (s === 'running' || s === 'connecting' ? 'done' : s));
    };
  }, []);

  const reset = useCallback(() => {
    if (wsRef.current) wsRef.current.close();
    setTrace([]);
    setResult(null);
    setError(null);
    setStatus('idle');
  }, []);

  return { trace, status, result, error, runGoal, reset };
}
