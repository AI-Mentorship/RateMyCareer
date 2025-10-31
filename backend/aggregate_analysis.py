import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- Setup and Connection ---
load_dotenv()
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)
print("✅ Successfully connected to Supabase.")

# --- Pagination settings ---
BATCH_SIZE = 500

try:
    # --- 1. Fetch Analyzed Submissions (with Pagination) ---
    print("🚚 Fetching analyzed data from the 'submissions' table...")
    
    all_submissions_data = []
    page = 0
    
    while True:
        start_row = page * BATCH_SIZE
        end_row = start_row + BATCH_SIZE - 1
        
        print(f"   -> Fetching batch {page + 1} (rows {start_row} to {end_row})...")
        
        # We only select the columns we need for aggregation
        # and filter out any rows where sentiment_score is null.
        
        # --- THIS IS THE CORRECTED LINE ---
        submissions_response = supabase.table('submissions').select(
            'subreddit_id, sentiment_score, has_regret'
        ).not_.is_('sentiment_score', None).range(start_row, end_row).execute()
        
        if not submissions_response.data:
            print("   -> No more data found.")
            break # Exit the loop
        
        all_submissions_data.extend(submissions_response.data)
        page += 1

    if not all_submissions_data:
        print("🟡 No analyzed submissions found to aggregate. Exiting.")
        exit()

    # Convert the *complete* list of submissions into a pandas DataFrame
    submissions_df = pd.DataFrame(all_submissions_data)
    print(f"📊 Found a total of {len(submissions_df)} analyzed submissions to process.")

    # --- 2. Fetch Subreddit Info for Career Names ---
    print("🚚 Fetching career names from the 'subreddits' table...")
    # NOTE: If you have more than 1000 subreddits, you'll need to paginate this query too!
    subreddits_response = supabase.table('subreddits').select('subreddit_id, display_name').execute()
    subreddits_df = pd.DataFrame(subreddits_response.data)

    # --- 3. Perform Aggregation ---
    print("⚙️  Calculating aggregate metrics...")
    grouped = submissions_df.groupby('subreddit_id')

    def calculate_regret_ratio(series):
        if len(series) == 0:
            return 0
        return series.sum() / len(series) # .sum() on a boolean (True/False) counts the Trues

    aggregated_data = grouped.agg(
        avg_sentiment=('sentiment_score', 'mean'),
        sentiment_volatility=('sentiment_score', 'std'),
        regret_ratio=('has_regret', calculate_regret_ratio)
    ).reset_index()

    aggregated_data['sentiment_volatility'] = aggregated_data['sentiment_volatility'].fillna(0)

    # --- 4. Merge Data to Add Career Names ---
    print("🤝 Merging aggregated data with career names...")
    final_df = pd.merge(aggregated_data, subreddits_df, on='subreddit_id', how='left')

    # --- 5. Prepare Data for Insertion ---
    print("📝 Preparing final data for Supabase table...")
    final_df = final_df.rename(columns={'display_name': 'career_name'})
    final_df['record_date'] = datetime.now().isoformat()
    final_df['forecasted_sentiment_avg'] = None
    final_df['vibe_score'] = None
    
    final_df = final_df[[
        'career_name', 'subreddit_id', 'record_date', 'avg_sentiment', 
        'sentiment_volatility', 'regret_ratio', 'forecasted_sentiment_avg', 'vibe_score'
    ]]

    # Filter out any rows where career_name might be null (if a subreddit was deleted)
    final_df = final_df.dropna(subset=['career_name'])
    
    data_to_insert = final_df.to_dict(orient='records')

    # --- 6. Insert Data into the Aggregate Table ---
    print(f" Inserting {len(data_to_insert)} records into 'career_sentiments' table...")
    
    insert_response = supabase.table('aggregate').insert(data_to_insert).execute()
    
    print("✅ Aggregation complete! Data has been successfully inserted.")

except Exception as e:
    print(f"❌ An error occurred: {e}")

