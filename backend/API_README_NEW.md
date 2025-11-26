# Backend API (development)

This repository includes a small Flask API that exposes endpoints your React frontend can call to get career rankings, per-career scores, and a combined timeline (current weekly forecast points + aggregated rows).

This document explains how to set up and run the API locally, which environment variables are required, and how to integrate the endpoints into a React application (step-by-step, with example code snippets).

---

## Quick start (Windows / PowerShell)

1. Save the `api.py` text to `backend/api.py` (overwrite if present).
2. Open PowerShell and create a virtual environment (optional) and install dependencies:

```powershell
cd D:\Ratemycareer\backend
# optional: create and activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# Install dependencies (recommended: use the repository requirements)
pip install -r requirements.txt
# Or install only the essentials: pip install flask flask-cors python-dotenv supabase
```

3. Create a `.env` file in the repository root (`D:\Ratemycareer\.env`) with at least your Supabase credentials:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJI... (REPLACE WITH SERVICE KEY)
```

4. Run the API server (dev):

```powershell
cd D:\Ratemycareer\backend
python api.py
# The server binds to 0.0.0.0:8000 by default (API base URL: http://127.0.0.1:8000)
```

> Note: CORS is enabled in the Flask app; your React app (running on another port) can call the API directly.

---

## Endpoints

All endpoints return JSON. Base URL (dev): http://127.0.0.1:8000

1) GET /api/rankings

- Purpose: return a single (most recent) aggregate row per career, sorted by `vibe_score` (highest first). If you provide `date=YYYY-MM-DD` the endpoint instead returns rows for that date.
- Query params:
  - date (optional) — filter by `record_date` to get a snapshot
  - limit (optional) — number of careers to return (default 100)
- Response shape:

```json
{ "data": [ { "career_name": "Teachers", "record_date": "2025-11-04", "vibe_score": 3.65, "forecasted_sentiment_avg": -0.01, "avg_sentiment": -0.02, "sentiment_volatility": 0.15, "regret_ratio": 0.05, "subreddit_id": "t5_abc" }, ... ] }
```

2) GET /api/scores?career=PROFESSION_NAME

- Purpose: return aggregate rows for a career. By default returns the most recent row; pass `history=true` to get up to 100 recent rows.
- Query params:
  - career (required)
  - date (optional) — filter to a specific `record_date`
  - history (optional) — `true` to return historical rows
- Response shape:

```json
{ "career": "Teachers", "rows": [ { "career_name":"Teachers", "record_date":"2025-11-04", "avg_sentiment": -0.02, "forecasted_sentiment_avg": -0.01, "vibe_score": 3.65 }, ... ] }
```

3) GET /api/timeline?career=PROFESSION_NAME

- Purpose: return a merged timeline combining weekly entries from the `forecast` table (year, week_number → converted to ISO date) and date rows from `aggregate`. When both types exist on the same date, the `aggregate` entry takes precedence.
- Query params:
  - career (required)
  - include_aggregate (optional, default true)
  - include_forecast (optional, default true)
- Response shape:

```json
{ "career": "Teachers", "timeline": [ { "date": "2025-10-27", "source": "aggregate", "value": -0.02, "raw": { ... } }, { "date": "2025-11-03", "source": "forecast", "value": 0.01, "raw": { ... } } ] }
```

---

4) GET /api/career_summaries

- Purpose: return one or more summary rows from the `career_summaries` table. Useful for showing a small human-written summary or short description for a career.
- Query params:
  - career (optional) — filter to a specific `career_name` (exact match)
  - limit (optional) — number of rows to return (default 100)
- Response shape examples:

When a career filter is provided:
```json
{ "career": "Teachers", "rows": [ { "id": 42, "created_at": "2025-11-07T12:00:00Z", "career_name": "Teachers", "summary": "Teachers report mixed satisfaction; workload is high but community support is strong." } ] }
```

When no career filter is provided:
```json
{ "data": [ { "id": 42, "created_at": "2025-11-07T12:00:00Z", "career_name": "Teachers", "summary": "..." }, { "id": 43, "career_name": "Lawyers", "summary": "..." } ] }
```

Notes: the endpoint returns recent summaries ordered by `created_at` desc. If you prefer a single canonical summary per career, request with `limit=1` or I can add a convenience endpoint that returns a single summary string.

5) GET /api/quotes

- Purpose: return quotes (short text excerpts) from the `quotes` table. Useful for displaying user-submitted quotes or example comments on a profession page.
- Query params:
  - career (optional) — filter to a specific `career_name` (exact match)
  - limit (optional) — number of rows to return (default 100)
  - random (optional) — `true` to return a single random quote for the career (only used when `career` is provided)
- Response shape examples:

Recent quotes (no career filter):
```json
{ "data": [ { "id": 101, "created_at": "2025-11-07T12:05:00Z", "career_name": "Teachers", "quote_body": "I love my students, but paperwork is overwhelming." }, ... ] }
```

Quotes for a career:
```json
{ "career": "Teachers", "rows": [ { "id": 101, "created_at": "2025-11-07T12:05:00Z", "career_name": "Teachers", "quote_body": "I love my students..." } ] }
```

Random quote for a career (when `random=true`):
```json
{ "career": "Teachers", "quote": { "id": 101, "quote_body": "I love my students...", "created_at": "2025-11-07T12:05:00Z" } }
```

Notes: the server-side `random` implementation currently fetches up to `limit` rows and picks one at random. For very large tables a SQL-level random selection (ORDER BY RANDOM() / TABLESAMPLE) is more efficient; tell me if you want that.


## React integration — step by step (for beginners)

These steps will help the front-end team integrate the API using plain `fetch`. They can adapt this to axios or their app framework.

1) Confirm the API server is running at `http://127.0.0.1:8000`.

2) Set an `API_BASE` constant in the React app (e.g., in `.env` or a config file):

```js
// .env.local
REACT_APP_API_BASE=http://127.0.0.1:8000
```

3) Fetch the rankings (example):

```js
const API_BASE = process.env.REACT_APP_API_BASE || 'http://127.0.0.1:8000';
async function fetchRankings(limit=10){
  const res = await fetch(`${API_BASE}/api/rankings?limit=${limit}`);
  if(!res.ok) throw new Error(await res.text());
  return res.json(); // { data: [...] }
}
```

4) Fetch scores for a career (latest row):

```js
async function fetchScores(career){
  const res = await fetch(`${API_BASE}/api/scores?career=${encodeURIComponent(career)}`);
  return res.json(); // { career: 'Teachers', rows: [...] }
}
```

5) Fetch timeline and plot

```js
async function fetchTimeline(career){
  const res = await fetch(`${API_BASE}/api/timeline?career=${encodeURIComponent(career)}`);
  const json = await res.json();
  // json.timeline => array of {date, source, value}
  const dates = json.timeline.map(p => p.date);
  const values = json.timeline.map(p => p.value);
  return { dates, values, raw: json.timeline };
}
```

6) Charting notes

- You can use `react-chartjs-2` + `chart.js`, `recharts`, `apexcharts`, etc. The API returns dates as ISO strings (YYYY-MM-DD) and values as floats (usually in [-1,1]), suitable for plotting.

7) Example simple React hook (pseudo-code)

```js
import {useEffect, useState} from 'react';
export function useTimeline(career){
  const [timeline, setTimeline] = useState([]);
  useEffect(()=>{
    let mounted = true;
    fetch(`${API_BASE}/api/timeline?career=${encodeURIComponent(career)}`)
      .then(r=>r.json())
      .then(j=> mounted && setTimeline(j.timeline || []))
      .catch(console.error);
    return () => { mounted = false };
  }, [career]);
  return timeline;
}
```

---

## Required libraries and environment

- Python 3.10+ (or compatible)
- Install server dependencies via `pip install -r backend/requirements.txt` (recommended)
- Minimal Python packages if you prefer a smaller install: `flask`, `flask-cors`, `python-dotenv`, `supabase` (supabase-py)
- Frontend: `react`, and a charting library (recommended: `react-chartjs-2` + `chart.js`)

---

## Troubleshooting

- CORS: The API uses `flask-cors`. If you see CORS errors, ensure the server is running and the request origin is allowed.
- Missing SUPABASE vars: the API will log/return an error if `SUPABASE_URL` or `SUPABASE_KEY` are not set.
- Null `vibe_score`: if the DB has NULL for `vibe_score` the frontend will see empty or `-`. You can compute a fallback in the frontend or ask me to add a computed fallback in the API.
- Port mismatch: update `REACT_APP_API_BASE` in the React app to match the actual API base URL.

---
