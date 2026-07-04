import { useState } from 'react';
import TopShell from '../layout/TopShell';
import { BACKEND_URL } from '../config';
import './DocumentUpload.css';

export default function DocumentUpload() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${BACKEND_URL}/api/upload-pdf`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.error) setError(data.error);
      else setResult(data);
    } catch (err) {
      setError('Upload failed. Try again.');
    }
    setLoading(false);
  };

  return (
    <TopShell>
      <div className="dash-header">
        <div className="mono-tag">document upload</div>
        <h1>Upload a document.</h1>
        <p className="dash-sub">Shundo reads a real PDF and pulls out dates, tasks, and a summary — a syllabus, an itinerary, a project brief.</p>
      </div>

      <form className="upload-form" onSubmit={handleUpload}>
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button className="btn btn-fill" type="submit" disabled={!file || loading}>
          {loading ? 'reading...' : 'extract info'}
        </button>
      </form>

      {error && <div className="upload-error">{error}</div>}

      {result && (
        <div className="upload-results">
          {result.summary && (
            <div className="upload-section">
              <div className="upload-section-title">Summary</div>
              <p>{result.summary}</p>
            </div>
          )}

          {result.important_dates?.length > 0 && (
            <div className="upload-section">
              <div className="upload-section-title">Important dates</div>
              {result.important_dates.map((d, i) => (
                <div className="upload-item-row" key={i}>
                  <span className="upload-item-date">{d.date}</span>
                  <span>{d.description}</span>
                </div>
              ))}
            </div>
          )}

          {result.tasks?.length > 0 && (
            <div className="upload-section">
              <div className="upload-section-title">Tasks found</div>
              {result.tasks.map((t, i) => (
                <div className="upload-item-row" key={i}>{t}</div>
              ))}
            </div>
          )}
        </div>
      )}
    </TopShell>
  );
}
