import os
from datetime import datetime
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client
from typing import List, Dict, Any
import random

# Load .env from project root if available
root_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '.env')
if not os.path.exists(root_env):
    # fallback to default load (searches CWD and parent directories)
    load_dotenv()
else:
    load_dotenv(root_env)

app = Flask(__name__)
CORS(app)

def get_supabase_client():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


def parse_date(qdate: str):
    if not qdate:
        return None
    try:
        # accept YYYY-MM-DD
        return datetime.strptime(qdate, '%Y-%m-%d').date().isoformat()
    except Exception:
        return None


@app.route('/api/rankings', methods=['GET'])
def rankings():
    """Return career rankings ordered by vibe_score (desc).

    Query params:
      date: YYYY-MM-DD (optional) - filter by record_date
      limit: int (optional) - number of rows to return (default 100)
    """
    supabase = get_supabase_client()
    qdate = parse_date(request.args.get('date'))
    try:
        limit = int(request.args.get('limit', 100))
    except Exception:
        limit = 100

    if not supabase:
        return jsonify({'error': 'Supabase credentials missing or client init failed.'}), 500

    fields = 'career_name,record_date,vibe_score,forecasted_sentiment_avg,subreddit_id,avg_sentiment,sentiment_volatility,regret_ratio'

    # If a specific date is provided, behave as before and return rows for that date
    if qdate:
        query = supabase.table('aggregate').select(fields).eq('record_date', qdate).order('vibe_score', desc=True).limit(limit)
        res = query.execute()
        if res and getattr(res, 'data', None) is not None:
            return jsonify({'data': res.data}), 200
        return jsonify({'data': res}), 200

    # No date provided: return the most recent row PER career (based on record_date)
    # Strategy: fetch recent rows ordered by record_date desc, dedupe by career_name keeping first (most recent), then sort by vibe_score desc
    fetch_limit = max(limit * 10, 1000)
    query = supabase.table('aggregate').select(fields).order('record_date', desc=True).limit(fetch_limit)
    res = query.execute()
    rows = []
    if res and getattr(res, 'data', None) is not None:
        rows = res.data

    latest_by_career = {}
    for r in rows:
        cname = r.get('career_name')
        if not cname:
            continue
        if cname not in latest_by_career:
            latest_by_career[cname] = r

    # sort latest rows by vibe_score (None treated as very small)
    def vibe_key(x):
        try:
            return float(x.get('vibe_score'))
        except Exception:
            return float('-inf')

    sorted_latest = sorted(latest_by_career.values(), key=vibe_key, reverse=True)
    # Replace the career label with the value from subreddits.career_name when possible
    subreddit_ids = [r.get('subreddit_id') for r in sorted_latest if r.get('subreddit_id')]
    try:
        if subreddit_ids:
            # fetch mapping in a single query
            sq = supabase.table('subreddits').select('subreddit_id,career_name').in_('subreddit_id', subreddit_ids).execute()
            subs = sq.data if (sq and getattr(sq, 'data', None) is not None) else []
            mapping = {s.get('subreddit_id'): s.get('career_name') for s in subs}
            for r in sorted_latest:
                sid = r.get('subreddit_id')
                if sid and mapping.get(sid):
                    # overwrite career_name with the canonical name from subreddits table
                    r['career_name'] = mapping.get(sid)
    except Exception:
        # if anything fails, just return the original rows
        pass

    return jsonify({'data': sorted_latest[:limit]}), 200


@app.route('/api/scores', methods=['GET'])
def scores_for_career():
    """Return score fields for a specific career/profession.

    Query params:
      career: career_name (required)
      date: YYYY-MM-DD (optional) - filter by record_date
    """
    career = request.args.get('career')
    if not career:
        return jsonify({'error': 'career query parameter required'}), 400

    supabase = get_supabase_client()
    if not supabase:
        return jsonify({'error': 'Supabase credentials missing or client init failed.'}), 500

    qdate = parse_date(request.args.get('date'))
    history = request.args.get('history', 'false').lower() in ('1', 'true', 'yes')

    if qdate:
        query = supabase.table('aggregate').select('*').eq('career_name', career).eq('record_date', qdate)
        query = query.order('record_date', desc=True).limit(100)
        res = query.execute()
        if res and getattr(res, 'data', None) is not None:
            return jsonify({'career': career, 'rows': res.data}), 200
        return jsonify({'data': res}), 200

    # If not requesting history, return only the most recent row for the career
    if not history:
        query = supabase.table('aggregate').select('*').eq('career_name', career).order('record_date', desc=True).limit(1)
        res = query.execute()
        if res and getattr(res, 'data', None) is not None:
            return jsonify({'career': career, 'rows': res.data}), 200
        return jsonify({'data': res}), 200

    # history requested: return up to 100 recent rows
    query = supabase.table('aggregate').select('*').eq('career_name', career).order('record_date', desc=True).limit(100)
    res = query.execute()
    if res and getattr(res, 'data', None) is not None:
        return jsonify({'career': career, 'rows': res.data}), 200
    return jsonify({'data': res}), 200


@app.route('/api/timeline', methods=['GET'])
def timeline():
    """Return a combined timeline for a career by joining `forecast` weekly points
    with `aggregate` date points (using forecasted_sentiment_avg when present).

    Query params:
      career: career_name (required)
      include_aggregate: bool (optional, default true) - include aggregate rows
      include_forecast: bool (optional, default true) - include forecast table rows
    """
    career = request.args.get('career')
    if not career:
        return jsonify({'error': 'career query parameter required'}), 400

    supabase = get_supabase_client()
    if not supabase:
        return jsonify({'error': 'Supabase credentials missing or client init failed.'}), 500

    include_aggregate = request.args.get('include_aggregate', 'true').lower() in ('1', 'true', 'yes')
    include_forecast = request.args.get('include_forecast', 'true').lower() in ('1', 'true', 'yes')

    points = []

    # 1) Pull weekly points from forecast table
    if include_forecast:
        try:
            fq = (
                supabase
                .table('forecast')
                .select('career_name,year,week_number,sentiment_average')
                .eq('career_name', career)
                .order('year', desc=False)
                .order('week_number', desc=False)
                .execute()
            )
            if fq and getattr(fq, 'data', None) is not None:
                for row in fq.data:
                    try:
                        y = int(row.get('year'))
                        w = int(row.get('week_number'))
                        # Convert ISO week to a date (Monday of that ISO week)
                        d = datetime.fromisocalendar(y, w, 1).date().isoformat()
                        points.append({
                            'date': d,
                            'source': 'forecast',
                            'value': row.get('sentiment_average'),
                            'raw': row
                        })
                    except Exception:
                        # skip malformed rows
                        continue
        except Exception as e:
            logging.error(f"Error fetching forecast series for {career}: {e}")

    # 2) Pull aggregate rows (which contain forecasted_sentiment_avg and record_date)
    if include_aggregate:
        try:
            aq = (
                supabase
                .table('aggregate')
                .select('career_name,record_date,avg_sentiment,forecasted_sentiment_avg,vibe_score')
                .eq('career_name', career)
                .order('record_date', desc=False)
                .limit(1000)
                .execute()
            )
            if aq and getattr(aq, 'data', None) is not None:
                for row in aq.data:
                    rd = row.get('record_date')
                    # normalize record_date to ISO date string
                    try:
                        if rd is None:
                            continue
                        # record_date may already be a string date
                        d = rd if isinstance(rd, str) else row.get('record_date').isoformat()
                    except Exception:
                        try:
                            d = str(row.get('record_date'))
                        except Exception:
                            continue

                    # prefer forecasted_sentiment_avg when present, otherwise avg_sentiment
                    val = row.get('forecasted_sentiment_avg') if row.get('forecasted_sentiment_avg') is not None else row.get('avg_sentiment')
                    points.append({
                        'date': d,
                        'source': 'aggregate',
                        'value': val,
                        'raw': row
                    })
        except Exception as e:
            logging.error(f"Error fetching aggregate rows for {career}: {e}")

    # 3) Merge and sort by date; dedupe by date preferring aggregate entries
    # Build dict keyed by date, preferring aggregate source
    merged = {}
    for p in points:
        dt = p['date']
        if dt in merged:
            # prefer aggregate over forecast
            if merged[dt].get('source') == 'aggregate':
                continue
            if p.get('source') == 'aggregate':
                merged[dt] = p
        else:
            merged[dt] = p

    # produce sorted list
    timeline = [merged[k] for k in sorted(merged.keys())]

    return jsonify({'career': career, 'timeline': timeline}), 200


@app.route('/api/career_summaries', methods=['GET'])
def career_summaries():
    """Return rows from the career_summaries table.

    Query params:
      career: career_name (optional) - filter by career_name
      limit: int (optional) - number of rows to return (default 50)
    """
    career = request.args.get('career')
    try:
        limit = int(request.args.get('limit', 50))
    except Exception:
        limit = 50

    supabase = get_supabase_client()
    if not supabase:
        return jsonify({'error': 'Supabase credentials missing or client init failed.'}), 500

    try:
        query = supabase.table('career_summaries').select('*')
        if career:
            query = query.eq('career_name', career)
        query = query.order('created_at', desc=True).limit(limit)
        res = query.execute()
        rows = res.data if (res and getattr(res, 'data', None) is not None) else []

        # If client asked for a single row (limit==1), return the summary at top-level
        if limit == 1:
            if rows and len(rows) > 0:
                return jsonify({'career': career, 'summary': rows[0].get('summary'), 'row': rows[0]}), 200
            else:
                return jsonify({'career': career, 'summary': None, 'row': None}), 200

        # Otherwise return the rows list
        return jsonify({'career': career, 'rows': rows}), 200
    except Exception as e:
        logging.error(f"Error fetching career_summaries: {e}")
        return jsonify({'error': 'Failed to fetch career_summaries'}), 500


@app.route('/api/quotes', methods=['GET'])
def quotes():
    """Return rows from the quotes table.

    Query params:
      career: career_name (optional) - filter by career_name
      limit: int (optional) - number of rows to return (default 10)
      random: bool (optional) - if true, return a random selection of rows
    """
    career = request.args.get('career')
    rnd = request.args.get('random', 'false').lower() in ('1', 'true', 'yes')
    try:
        limit = int(request.args.get('limit', 10))
    except Exception:
        limit = 10

    supabase = get_supabase_client()
    if not supabase:
        return jsonify({'error': 'Supabase credentials missing or client init failed.'}), 500

    try:
        # Fetch rows (limit defensively to avoid huge payloads when random sampling)
        query = supabase.table('quotes').select('*')
        if career:
            query = query.eq('career_name', career)
        # If requesting random, fetch up to a reasonable cap and sample in Python
        fetch_cap = max(limit * 5, 100) if rnd else limit
        query = query.limit(fetch_cap)
        res = query.execute()
        rows = res.data if (res and getattr(res, 'data', None) is not None) else []

        if rnd and rows:
            # sample without replacement
            sampled = random.sample(rows, min(limit, len(rows)))
            return jsonify({'career': career, 'rows': sampled}), 200

        # Otherwise return up to limit rows (already limited by query)
        return jsonify({'career': career, 'rows': rows[:limit]}), 200
    except Exception as e:
        logging.error(f"Error fetching quotes: {e}")
        return jsonify({'error': 'Failed to fetch quotes'}), 500


if __name__ == '__main__':
    # Run dev server on port 8000
    app.run(host='0.0.0.0', port=8000, debug=True)
