from dotenv import load_dotenv
import os
from supabase import create_client

# try backend/.env then repo root .env
backend_env = os.path.join(os.path.dirname(__file__), '..', '.env')
repo_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
for p in (backend_env, repo_env):
    if os.path.exists(p):
        load_dotenv(p)
        print('Loaded env from', p)
        break

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
if not url or not key:
    print('SUPABASE env vars missing')
    raise SystemExit(1)

sb = create_client(url, key)

def get_count(eq_filter=None):
    try:
        q = sb.table('submissions').select('submission_id', count='exact')
        if eq_filter:
            q = q.eq(*eq_filter)
        res = q.execute()
        cnt = getattr(res, 'count', None)
        data_len = len(res.data) if (res and getattr(res,'data',None) is not None) else 0
        return cnt, data_len
    except Exception as e:
        return None, None

print('Total submissions: ', get_count())
print("Subreddit '2qqcs' submissions: ", get_count(('subreddit_id','2qqcs')))
print("Subreddit name='Teachers' submissions: ", get_count(('subreddit_name','Teachers')))

try:
    res_empty = sb.table('submissions').select('submission_id', count='exact').is_('content', None).execute()
    print('Empty content count:', getattr(res_empty,'count',None))
except Exception as e:
    print('Empty content count: error', e)

try:
    sample = sb.table('submissions').select('submission_id,subreddit_id,subreddit_name').limit(20).execute()
    print('Sample rows (first 10):')
    for r in (sample.data or [])[:10]:
        print(' ', r.get('submission_id'), r.get('subreddit_id'), r.get('subreddit_name'))
except Exception as e:
    print('Sample rows error', e)
