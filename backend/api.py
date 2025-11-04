import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client

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

    query = supabase.table('aggregate').select('career_name,record_date,vibe_score,forecasted_sentiment_avg,subreddit_id,avg_sentiment,sentiment_volatility,regret_ratio')
    if qdate:
        query = query.eq('record_date', qdate)
    # order by vibe_score desc
    query = query.order('vibe_score', desc=True).limit(limit)
    res = query.execute()
    if res and getattr(res, 'data', None) is not None:
        return jsonify({'data': res.data})
    # fallback for older client returns
    return jsonify({'data': res}), 200


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
    query = supabase.table('aggregate').select('*').eq('career_name', career)
    if qdate:
        query = query.eq('record_date', qdate)
    query = query.order('record_date', desc=True).limit(100)
    res = query.execute()
    if res and getattr(res, 'data', None) is not None:
        return jsonify({'career': career, 'rows': res.data})
    return jsonify({'data': res}), 200


@app.route('/api/forecasts', methods=['GET'])
def forecasts():
    """Return forecasted sentiment (and available forecast fields) per career.

    Query params:
      date: YYYY-MM-DD (optional) - filter by record_date
      limit: int (optional)
    """
    supabase = get_supabase_client()
    if not supabase:
        return jsonify({'error': 'Supabase credentials missing or client init failed.'}), 500

    qdate = parse_date(request.args.get('date'))
    try:
        limit = int(request.args.get('limit', 100))
    except Exception:
        limit = 100

    # Return career_name, record_date, forecasted_sentiment_avg, vibe_score if present
    query = supabase.table('aggregate').select('career_name,record_date,forecasted_sentiment_avg,vibe_score,subreddit_id')
    if qdate:
        query = query.eq('record_date', qdate)
    query = query.order('forecasted_sentiment_avg', desc=True).limit(limit)
    res = query.execute()
    if res and getattr(res, 'data', None) is not None:
        return jsonify({'data': res.data})
    return jsonify({'data': res}), 200


if __name__ == '__main__':
    # Run dev server on port 8000
    app.run(host='0.0.0.0', port=8000, debug=True)
