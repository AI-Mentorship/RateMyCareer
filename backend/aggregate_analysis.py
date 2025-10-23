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

# --- 1. Fetch Analyzed Submissions ---
print("🚚 Fetching analyzed data from the 'submissions' table...")
# We only select the columns we need for aggregation
# and filter out any rows where sentiment_score is null.
submissions_response = supabase.table('submissions').select(
    'subreddit_id, sentiment_score, has_regret'
).not_.is_('sentiment_score', 'is', None).execute()

if not submissions_response.data:
    print("🟡No new analyzed submissions found to aggregate. Exiting.")
    exit()

# Convert the submissions data into a pandas DataFrame for easy manipulation
submissions_df = pd.DataFrame(submissions_response.data)
print(f"📊 Found {len(submissions_df)} analyzed submissions to process.")

# --- 2. Fetch Subreddit Info for Career Names ---
print("🚚 Fetching career names from the 'subreddits' table...")
subreddits_response = supabase.table('subreddits').select('subreddit_id, display_name').execute()
subreddits_df = pd.DataFrame(subreddits_response.data)

# --- 3. Perform Aggregation ---
print("⚙️  Calculating aggregate metrics...")
# Group the DataFrame by subreddit_id to perform calculations for each career
grouped = submissions_df.groupby('subreddit_id')

# Define a function to calculate the regret ratio safely
def calculate_regret_ratio(series):
    if len(series) == 0:
        return 0
    return series.sum() / len(series)

# Perform the aggregations for each group
aggregated_data = grouped.agg(
    avg_sentiment=('sentiment_score', 'mean'),
    sentiment_volatility=('sentiment_score', 'std'),
    regret_ratio=('has_regret', calculate_regret_ratio)
).reset_index()

# The std() function returns NaN (Not a Number) for groups with only one post.
# We'll fill these with 0 to represent no volatility.
aggregated_data['sentiment_volatility'] = aggregated_data['sentiment_volatility'].fillna(0)

# --- 4. Merge Data to Add Career Names ---
print("🤝 Merging aggregated data with career names...")
# Merge the aggregated metrics with the subreddit names
final_df = pd.merge(aggregated_data, subreddits_df, on='subreddit_id', how='left')

# --- 5. Prepare Data for Insertion ---
print("📝 Preparing final data for Supabase table...")
# Rename 'display_name' to 'career_name' to match the target table schema
final_df = final_df.rename(columns={'display_name': 'career_name'})

# Add the columns that don't come from the aggregation
final_df['record_date'] = datetime.now().isoformat()
final_df['forecasted_sentiment_avg'] = None # Placeholder for future analysis
final_df['vibe_score'] = None # Placeholder for future analysis

# Ensure the columns are in the correct order for insertion
final_df = final_df[[
    'career_name', 'subreddit_id', 'record_date', 'avg_sentiment', 
    'sentiment_volatility', 'regret_ratio', 'forecasted_sentiment_avg', 'vibe_score'
]]

# Convert the DataFrame to a list of dictionaries, which is the format Supabase expects
data_to_insert = final_df.to_dict(orient='records')

# --- 6. Insert Data into the Aggregate Table ---
print(f" Inserting {len(data_to_insert)} records into 'career_sentiments' table...")
# Assuming your aggregate table is named 'career_sentiments'
insert_response = supabase.table('career_sentiments').insert(data_to_insert).execute()

print("✅ Aggregation complete! Data has been successfully inserted.")