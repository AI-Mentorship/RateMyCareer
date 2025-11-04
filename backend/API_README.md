# Backend API (development)

This lightweight Flask API exposes three endpoints to retrieve career rankings and forecast data from the Supabase `aggregate` table.

Run locally (dev):

```powershell
# from repository root
cd backend
python api.py
```

Endpoints

- GET /api/rankings
  - Query params:
    - date (optional) - YYYY-MM-DD to filter by record_date
    - limit (optional) - number of rows to return (default 100)
  - Returns: JSON { data: [ {career_name, record_date, vibe_score, forecasted_sentiment_avg, ...}, ... ] }

- GET /api/scores?career=PROFESSION_NAME
  - Query params:
    - career (required) - career_name to fetch
    - date (optional) - YYYY-MM-DD filter
  - Returns: JSON { career: name, rows: [...] }

- GET /api/forecasts
  - Query params:
    - date (optional) - YYYY-MM-DD
    - limit (optional)
  - Returns: JSON { data: [ {career_name, record_date, forecasted_sentiment_avg, vibe_score, subreddit_id}, ... ] }

Notes
- The implementation uses `SUPABASE_URL` and `SUPABASE_KEY` from the environment. If those are missing the endpoints will return a 500 with an explanatory message.
- The API is intentionally minimal and meant for internal/dev use. It expects the `aggregate` table to conform to the schema in the repo documentation.
