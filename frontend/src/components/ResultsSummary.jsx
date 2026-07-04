import './ResultsSummary.css';

function formatDate(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso;
  }
}

function Section({ title, children, wide = false }) {
  return (
    <div className={`results-section ${wide ? 'results-section-wide' : ''}`}>
      <div className="results-section-title">{title}</div>
      {children}
    </div>
  );
}

export default function ResultsSummary({ result }) {
  if (!result || !result.tool_results || result.tool_results.length === 0) return null;

  const findAll = (toolName) =>
    result.tool_results.filter((r) => r.tool === toolName && Array.isArray(r.result)).flatMap((r) => r.result);

  const findLast = (toolName) => {
    const matches = result.tool_results.filter((r) => r.tool === toolName);
    return matches.length ? matches[matches.length - 1].result : null;
  };

  const flights = findAll('search_flights');
  const hotels = findAll('search_hotels');
  const places = findAll('search_places');
  const events = findLast('read_calendar_events') || [];
  const weatherEntries = result.tool_results.filter((r) => r.tool === 'get_weather_forecast' && r.result && !r.result.error);
  const createdEvent = findLast('create_calendar_event');
  const tasksCreated = result.tool_results.filter((r) => r.tool === 'create_task' && r.result && !r.result.error);
  const conversions = result.tool_results.filter((r) => r.tool === 'convert_currency' && r.result && !r.result.error);
  const expensesAdded = result.tool_results.filter((r) => r.tool === 'add_expense' && r.result && !r.result.error);

  const KNOWN_TOOLS = [
    'search_flights', 'search_hotels', 'search_places', 'read_calendar_events',
    'get_weather_forecast', 'create_calendar_event', 'create_task',
    'convert_currency', 'add_expense', 'create_email_draft', 'web_search', 'add_note',
  ];
  const otherSuccesses = result.tool_results.filter(
    (r) => !KNOWN_TOOLS.includes(r.tool) && r.result && !(r.result && r.result.error)
  );
  const emailDrafts = result.tool_results.filter((r) => r.tool === 'create_email_draft' && r.result && !r.result.error);
  const webSearches = result.tool_results.filter((r) => r.tool === 'web_search');
  const notesAdded = result.tool_results.filter((r) => r.tool === 'add_note' && r.result && !r.result.error);

  const hasAnything =
    flights.length || hotels.length || places.length || weatherEntries.length ||
    createdEvent || tasksCreated.length || events.length ||
    conversions.length || expensesAdded.length || otherSuccesses.length ||
    emailDrafts.length || webSearches.length || notesAdded.length;
  if (!hasAnything) return null;

  return (
    <div className="results-summary">
      {createdEvent && !createdEvent.error && (
        <Section title="Added to your calendar">
          <div className="result-item-row highlight">
            <span className="result-item-name">{createdEvent.title}</span>
            <span className="result-item-meta">{formatDate(createdEvent.start)}</span>
          </div>
        </Section>
      )}

      {events.length > 0 && (
        <Section title={`Your schedule (${events.length} upcoming)`}>
          {events.slice(0, 4).map((e, i) => (
            <div className="result-item-row" key={i}>
              <span className="result-item-name">{e.title}</span>
              <span className="result-item-meta">{formatDate(e.start)}</span>
            </div>
          ))}
        </Section>
      )}

      {flights.length > 0 && (
        <Section title="Flights found">
          {flights.slice(0, 4).map((f, i) => (
            <div className="result-item-row" key={i}>
              <span className="result-item-name">{f.airline || 'Flight'}</span>
              <span className="result-item-meta">{f.currency || ''} {f.price_estimate}</span>
            </div>
          ))}
        </Section>
      )}

      {hotels.length > 0 && (
        <Section title="Hotels found">
          {hotels.slice(0, 4).map((h, i) => (
            <div className="result-item-row" key={i}>
              <span className="result-item-name">{h.name}</span>
              <span className="result-item-meta">{h.currency || ''} {h.price_estimate}</span>
            </div>
          ))}
        </Section>
      )}

      {places.length > 0 && (
        <Section title="Places you can visit">
          {places.slice(0, 6).map((p, i) => (
            <div className="result-item-row" key={i}>
              <span className="result-item-name">{p.name}</span>
              <span className="result-item-meta">{p.cuisine || p.category || ''}</span>
            </div>
          ))}
        </Section>
      )}

      {weatherEntries.length > 0 && (
        <Section title="Weather">
          {weatherEntries.map((w, i) => (
            <div className="result-item-row" key={i}>
              <span className="result-item-name">{w.result.city}{w.result.date ? ` — ${w.result.date}` : ''}</span>
              <span className="result-item-meta">
                {w.result.temp_max_c ?? w.result.forecast?.[0]?.temp_max_c}°C · {w.result.rain_chance_percent ?? w.result.forecast?.[0]?.rain_chance_percent}% rain
              </span>
            </div>
          ))}
        </Section>
      )}

      {tasksCreated.length > 0 && (
        <Section title="Tasks added">
          {tasksCreated.map((t, i) => (
            <div className="result-item-row" key={i}>
              <span className="result-item-name">{t.result.title}</span>
            </div>
          ))}
        </Section>
      )}

      {conversions.length > 0 && (
        <Section title="Currency conversion">
          {conversions.map((c, i) => (
            <div className="result-item-row" key={i}>
              <span className="result-item-name">
                {c.result.amount} {c.result.from_currency} → {c.result.to_currency}
              </span>
              <span className="result-item-meta">{c.result.converted_amount} {c.result.to_currency}</span>
            </div>
          ))}
        </Section>
      )}

      {expensesAdded.length > 0 && (
        <Section title="Expenses logged">
          {expensesAdded.map((e, i) => (
            <div className="result-item-row" key={i}>
              <span className="result-item-name">{e.result.category}{e.result.description ? ` — ${e.result.description}` : ''}</span>
              <span className="result-item-meta">{e.result.currency} {e.result.amount}</span>
            </div>
          ))}
        </Section>
      )}

      {emailDrafts.length > 0 && (
        <Section title="Email drafts created">
          {emailDrafts.map((e, i) => (
            <div className="result-item-row" key={i}>
              <span className="result-item-name">{e.result.subject}</span>
              <span className="result-item-meta">to {e.result.to}</span>
            </div>
          ))}
        </Section>
      )}

      {webSearches.length > 0 && (
        <Section title="Web search results" wide>
          {(() => {
            const allItems = webSearches.filter((w) => Array.isArray(w.result)).flatMap((w) => w.result);
            const hasError = webSearches.some((w) => w.result && w.result.error);

            if (allItems.length > 0) {
              return allItems.slice(0, 4).map((item, i) => (
                <div className="search-result-row" key={i}>
                  <div className="search-result-title">{item.title || 'Result'}</div>
                  {item.snippet && <div className="search-result-snippet">{item.snippet}</div>}
                </div>
              ));
            }
            if (hasError) {
              return <div className="result-item-row"><span className="result-item-name">Search failed — try rephrasing the goal.</span></div>;
            }
            return <div className="result-item-row"><span className="result-item-name">No clear results found for this search.</span></div>;
          })()}
        </Section>
      )}

      {notesAdded.length > 0 && (
        <Section title="Notes">
          {notesAdded.map((n, i) => (
            <div className="result-item-row" key={i}>
              <span className="result-item-name">{n.result.content}</span>
            </div>
          ))}
        </Section>
      )}

      {otherSuccesses.length > 0 && (
        <Section title="Other results">
          {otherSuccesses.map((o, i) => (
            <div className="result-item-row" key={i}>
              <span className="result-item-name">{o.tool.replace(/_/g, ' ')}</span>
              <span className="result-item-meta">
                {typeof o.result === 'object' ? JSON.stringify(o.result).slice(0, 60) : String(o.result)}
              </span>
            </div>
          ))}
        </Section>
      )}
    </div>
  );
}
