import os
import json
import datetime
from dotenv import load_dotenv
from supabase import create_client

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

def load_supabase_client():
    # Try loading from backend/.env or root .env
    backend_env = os.path.join(os.path.dirname(__file__), '.env')
    root_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
    elif os.path.exists(root_env):
        load_dotenv(root_env)
    else:
        load_dotenv() # Try default

    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_KEY not found.")
        return None
    return create_client(url, key)

def fetch_all_rows(supabase, table_name):
    print(f"Fetching {table_name}...")
    all_rows = []
    page_size = 1000
    start = 0
    while True:
        try:
            # Range is inclusive
            response = supabase.table(table_name).select("*").range(start, start + page_size - 1).execute()
            rows = response.data
            if not rows:
                break
            all_rows.extend(rows)
            if len(rows) < page_size:
                break
            start += page_size
            print(f"  Fetched {len(all_rows)} rows so far...")
        except Exception as e:
            print(f"  Error fetching {table_name}: {e}")
            break
    return all_rows

def main():
    supabase = load_supabase_client()
    if not supabase:
        return

    # List of tables to export
    tables = [
        'aggregate',
        'career_summaries',
        'forecast',
        'quotes',
        'submission_topics',
        'submissions',
        'subreddits',
        'topics',
        'warning',
        'comments' 
    ]

    data = {}
    for table in tables:
        data[table] = fetch_all_rows(supabase, table)

    # Ensure prototype directory exists
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prototype')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, 'supabase_dump.json')
    print(f"Writing data to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, cls=DateTimeEncoder, indent=2)
    print("Done.")

if __name__ == "__main__":
    main()
